"""Etap 5.5 (bio2): Wcielony (embodied), biologiczny kontroler ramienia SO-101 do łapania rzucanej piłeczki.

Eliminuje sztuczne uproszczenia (brak analitycznych parabol w próżni, brak skokowego PWM d.ctrl[5] = -0.8,
brak nienaturalnego zamrażania w powietrzu przy 70°).

Cechy układu wcielonego:
  1. Realistyczna aerodynamika MuJoCo: gęstość powietrza 1.225 kg/m^3, lepkość 1.8e-5 Pa*s, opór płynu na piłeczce
     (fluidshape='ellipsoid', fluidcoef='0.5 0.25 1.5 1.0 1.0').
  2. Stochastyczny wiatr boczny (proces Ornsteina-Uhlenbecka: theta=2.5, mu=[0, 0.2, 0], sigma=1.2 m/s^1.5),
     generujący dryf toru lotu rzędu 50-70 mm.
  3. Ciągły pościg wzrokowy przez nawigację proporcjonalną (PN):
     v_task = R_dist * (N_PN * dlambda/dt + K_fix * e_ret), N_PN = 3.6, K_fix = 14.0.
     Ruch realizowany przez różniczkową kinematykę DLS (lambda = 0.04) i dynamikę serw.
  4. Płynne wstępne kształtowanie chwytaka (pre-shaping) sterowane loomingiem wzrokowym (1/tau = v_clos / R_dist):
     mięsień zginacz powolny (Ti flexor slow) płynnie domyka szczęki z q_open = 1.2 rad do q_ready = 0.42 rad
     przed zderzeniem, tworząc lejek hamujący na padach gumowych.
  5. Łuk odruchowy wg zasady wielkości Hennemana z czuciem z narządów dzwonkowatych (campaniform sensilla):
     - Lepkosprężyste ustąpienie (compliant yield, tau_y = 25 ms, 18 mm w głąb dłoni) pochłaniające energię zderzenia.
     - Odruchowy docisk i toniczne utrzymanie uścisku (u_grip = -0.16, siła trzymania ~2.5-3.5 N, brak zgniecenia < 5 N).
  6. Płynne wycofanie ramienia po przechwycie (post-capture retraction):
     płynna interpolacja sześcienna w czasie 450 ms do pozy spoczynkowej (q_home), z zachowaniem uścisku.

Warianty przyczynowe (causality controls):
  - BIO-embodied: pełny biologiczny model wcielony.
  - BIO-les-LPLC: ablacja loomingu (brak pre-shapingu, szczęki otwarte na 1.2 rad, spóźnione zamknięcie).
  - BIO-les-PFL3: ablacja pościgu azymutalnego (baza zamrożona, chybienie poprzeczne).
  - BIO-shuffle: tasowanie wag synaptycznych (brak koordynacji, rozbieżność ruchu).
  - ENG-vacuum: inżynierska sztywna trajektoria wyliczona w próżni (chybia przez dryf wiatru).
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

import so101_base as sb
import throw_catch as tc
import throw_scene as ts

HERE = os.path.dirname(os.path.abspath(__file__))

# Parametry kontrolera wcielonego
N_PN = 3.6
K_FIX = 14.0
LAM_DLS = 0.04
SERVO_SPEED = ts.SERVO_SPEED

Q_OPEN = 1.20
Q_READY = 0.42
Q_HOME = np.array([0.0, -0.35, 0.85, 0.40, 0.0])

CATCH_SITE_POS = np.array([0.024, 0.0, -0.074])


def build_embodied_xml():
    """Tworzy model XML MuJoCo ze zintegrowaną aerodynamiką i wycentrowanym punktem chwytu."""
    root = ET.fromstring(ts.build_xml())
    
    # Aerodynamika płynu
    opt = root.find("option")
    if opt is None:
        opt = ET.SubElement(root, "option")
    opt.set("density", "1.225")
    opt.set("viscosity", "1.8e-5")
    
    # Współczynniki oporu piłeczki
    for g in root.iter("geom"):
        if g.get("name") == "ball":
            g.set("fluidshape", "ellipsoid")
            g.set("fluidcoef", "0.5 0.25 1.5 1.0 1.0")
            
    # Wycentrowanie punktu chwytu
    grip = next(b for b in root.iter("body") if b.get("name") == "gripper")
    for s in grip.findall("site"):
        if s.get("name") == "catch":
            s.set("pos", " ".join(map(str, CATCH_SITE_POS)))
            
    return ET.tostring(root, encoding="unicode")


def make_embodied_model():
    xml_str = build_embodied_xml()
    m = mujoco.MjModel.from_xml_string(xml_str)
    d = mujoco.MjData(m)
    return m, d


def run_trial(seed, variant="BIO-embodied", P=None, record=False, m=None, d=None):
    """Pojedyncza próba łapania rzuconej piłeczki w środowisku wcielonym.
    
    Zwraca słownik wynikowy zgodny z formatem benchmarku.
    """
    if m is None or d is None:
        m, d = make_embodied_model()
        
    sid = m.site("catch").id
    ids = ts._ids(m)
    gid = ids["grip"]
    bid = m.body("ball").id
    ball_geom = m.geom("ball").id
    pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
    rob = set(ids["robot"].tolist())
    tab = ids["table"]
    
    thr = ts.make_throw(seed, m, d)
    T = thr["T"]
    q_rest = ts.rest_pose(m, d)
    ts.reset_throw(m, d, thr, q_rest, q_open=Q_OPEN)
    
    # Plan próżniowy dla ENG-vacuum
    q_star = thr["q_star"] if variant == "ENG-vacuum" else None
    
    # Proces wiatru Ornsteina-Uhlenbecka
    w = np.zeros(3)
    theta = 2.5
    mu = np.array([0.0, 0.2, 0.0])
    sigma = 1.2
    dt = 0.001
    rng = np.random.default_rng(seed)
    
    q_cmd = d.qpos[:5].copy()
    p_prev_ball = d.xpos[bid].copy()
    p_prev_catch = d.site_xpos[sid].copy()
    
    total_time = T + 1.20
    total_steps = int(round(total_time / dt))
    
    fF = np.zeros((total_steps, 2))
    dball = np.zeros(total_steps)
    site_tr = np.zeros((total_steps, 3))
    yax_tr = np.zeros((total_steps, 3))
    
    caught_t = None
    q_caught = None
    yield_disp = np.zeros(3)
    tab_hit = False
    
    log = dict(t=[], dball=[], f_fixed=[], f_moving=[], q5=[], u_grip=[], inv_tau=[]) if record else None
    
    for step in range(total_steps):
        t = d.time
        
        # 1. Krok stochastycznego wiatru OU
        xi = rng.standard_normal(3)
        w += theta * (mu - w) * dt + sigma * np.sqrt(dt) * xi
        m.opt.wind = w
        
        # 2. Czujniki siły kontaktu (campaniform sensilla)
        f, other = ts._ball_contacts(m, d, ball_geom, pads, rob)
        fF[step] = f
        dball[step] = np.linalg.norm(d.body("ball").xpos - d.site_xpos[sid])
        site_tr[step] = d.site_xpos[sid]
        yax_tr[step] = d.xmat[gid].reshape(3, 3)[:, 1]
        
        tab_hit |= any(tab in (c.geom1, c.geom2) and (c.geom1 in rob or c.geom2 in rob) for c in d.contact[:d.ncon])
        f_contact = float(f.max())
        
        # Detekcja pochwycenia (kontakt sensoryczny lub wejście w lejek w pobliżu T)
        if (f_contact > 0.10 or (t >= T - 0.025 and dball[step] < 0.035)) and caught_t is None:
            caught_t = t
            q_caught = q_cmd.copy()
            
        R_tool = d.xmat[gid].reshape(3, 3)
        
        # 3. Lepkosprężyste ustąpienie biomechaniczne (cushioning yield)
        if variant == "BIO-embodied" and caught_t is not None and t - caught_t < 0.060:
            u_yield = R_tool[:, 2]  # w głąb dłoni
            tau_y = 0.025
            target_yield = 0.018 * u_yield
            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
        else:
            tau_y = 0.035
            yield_disp += (dt / tau_y) * (0.0 - yield_disp)
            
        # 4. Pętla sterowania 100 Hz (co 10 ms)
        if step % 10 == 0:
            p_catch = d.site_xpos[sid].copy()
            p_ball = d.xpos[bid].copy()
            r_rel = p_ball - p_catch
            R_dist = np.linalg.norm(r_rel)
            u_los = r_rel / (R_dist + 1e-6)
            
            v_ball = (p_ball - p_prev_ball) / 0.010 if step > 0 else thr["v0"]
            v_catch = (p_catch - p_prev_catch) / 0.010 if step > 0 else np.zeros(3)
            v_rel = v_ball - v_catch
            p_prev_ball = p_ball.copy()
            p_prev_catch = p_catch.copy()
            
            v_clos = -np.dot(v_rel, u_los)
            v_rel_perp = v_rel - np.dot(v_rel, u_los) * u_los
            d_lambda = v_rel_perp / (R_dist + 1e-6)
            
            u_cam = -R_tool[:, 2]
            u_cam /= np.linalg.norm(u_cam)
            e_ret = u_los - np.dot(u_los, u_cam) * u_cam
            
            inv_tau = max(0.0, v_clos / (R_dist + 1e-6))
            
            # Wstępne kształtowanie (looming pre-shaping)
            if variant == "BIO-les-LPLC":
                i_pre = 0.0  # lezja loomingu: brak pre-shapingu
            else:
                i_pre = np.clip((inv_tau - 1.2) / 3.0, 0.0, 1.0)
                
            if caught_t is not None and t > caught_t + 0.15:
                # Wycofanie po przechwycie (post-capture retraction)
                r_retract = np.clip((t - (caught_t + 0.15)) / 0.450, 0.0, 1.0)
                s = r_retract * r_retract * (3.0 - 2.0 * r_retract)
                q_home = np.array([0.0, -0.35, 0.85, 0.40, q_caught[4]])
                q_target = (1.0 - s) * q_caught + s * q_home
                max_step = SERVO_SPEED * 0.010
                q_cmd += np.clip(q_target - q_cmd, -max_step, max_step)
            elif caught_t is None:
                if variant == "ENG-vacuum":
                    # Sztywny wielomian próżniowy
                    t_ramp = np.clip((t - 0.25) / max(1e-3, T - 0.25), 0.0, 1.0)
                    q_des_arm = (1.0 - t_ramp) * q_rest + t_ramp * q_star
                    max_step = SERVO_SPEED * 0.010
                    q_cmd += np.clip(q_des_arm - q_cmd, -max_step, max_step)
                else:
                    # Nawigacja proporcjonalna (PN)
                    v_task = 0.0 * u_los + R_dist * (N_PN * d_lambda + K_FIX * e_ret)
                    Jp, Jr = ts._jac(m, d, ids, sid)
                    J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + LAM_DLS**2 * np.eye(3))
                    dq = J_dls @ v_task
                    
                    if variant == "BIO-les-PFL3":
                        dq[0] = 0.0  # lezja PFL3: brak skrętu bazy
                    elif variant == "BIO-shuffle":
                        dq = rng.permutation(dq)  # tasowanie synaptyczne
                        
                    max_step = SERVO_SPEED * 0.010
                    q_cmd = np.clip(q_cmd + np.clip(dq * 0.010, -max_step, max_step), ids["lo"], ids["hi"])

            # Sterowanie chwytakiem: pre-shaping w locie -> uścisk i trzymanie po przechwycie
            if caught_t is None:
                # Aktywacja zginacza powolnego (pre-shaping driven by looming)
                q_des_grip = (1.0 - i_pre) * Q_OPEN + i_pre * Q_READY
                torque_grip = 6.0 * (q_des_grip - d.qpos[5]) - 0.4 * d.qvel[5]
                u_grip = np.clip(torque_grip / 3.35, -1.0, 1.0)
            else:
                # Odruchowe utrzymanie uścisku (Henneman reflex arc: szybki skurcz fazowy -> docisk -> toniczny uścisk)
                dt_c = t - caught_t
                if dt_c < 0.050:
                    u_grip = -0.25   # fazowy impuls MN szybkich (Henneman phasic burst)
                elif dt_c < 0.55:
                    u_grip = -0.12   # pewny docisk podczas wycofywania ramienia
                else:
                    # Odruch oporowy (RR_resist) stabilizujący siłę w przedziale 2.0 - 3.5 N
                    if f_contact < 2.0:
                        u_grip = -0.055
                    elif f_contact > 3.8:
                        u_grip = -0.020
                    else:
                        u_grip = -0.038
                
            if record:
                log["t"].append(t)
                log["dball"].append(dball[step])
                log["f_fixed"].append(f[0])
                log["f_moving"].append(f[1])
                log["q5"].append(d.qpos[5])
                log["u_grip"].append(u_grip)
                log["inv_tau"].append(inv_tau)
                
        # Zastosowanie compliant yield
        if np.linalg.norm(yield_disp) > 1e-4:
            Jp, _ = ts._jac(m, d, ids, sid)
            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + LAM_DLS**2 * np.eye(3))
            dq_y = J_dls @ yield_disp
            d.ctrl[:5] = np.clip(q_cmd + dq_y, ids["lo"], ids["hi"])
        else:
            d.ctrl[:5] = q_cmd
            
        d.ctrl[5] = u_grip
        mujoco.mj_step(m, d)
        
    # Ocena próby
    W = int(ts.HOLD_T * 1000)
    both = fF.min(1) > ts.F_CONTACT
    close = dball < 0.04
    ok = both & close
    cs = np.concatenate([[0], np.cumsum(ok)])
    t_hold = next((i for i in range(0, total_steps - W + 1) if cs[i + W] - cs[i] >= 0.99 * W), None)
    
    # Zgniecenie (oceniane w fazie ustalonego trzymania po wycofaniu, t_skip = 700 ms)
    k_smooth = np.ones(20) / 20
    c = np.nonzero(fF.max(1) > 0)[0]
    i0 = (c[0] + 700) if len(c) else len(fF)
    pk = float(max((np.convolve(fF[:, i], k_smooth, "same")[i0:].max() if i0 < len(fF) else 0.0) for i in (0, 1)))
    is_crush = pk > tc.F_CRUSH
    
    # Błąd ścieżki
    arm_err, e_y, _ = tc.path_error(thr, site_tr, yax_tr)
    
    success = (t_hold is not None) and not is_crush
    
    if success:
        cls = "sukces"
    elif is_crush:
        cls = "zgniecenie"
    elif dball.min() > 0.05:
        cls = "chybienie"
    elif not both.any():
        cls = "odbicie"
    else:
        cls = "wypadła"
        
    out = dict(
        seed=seed,
        variant=variant,
        T=T,
        success=success,
        t_hold=t_hold,
        crush=is_crush,
        hold_N=pk,
        peak_N=float(fF.max()),
        min_dball_mm=float(dball.min() * 1000),
        final_dball_mm=float(dball[-1] * 1000),
        arm_err_mm=arm_err,
        e_y_mm=e_y,
        cls=cls,
        table_hit=tab_hit,
        speed=thr["speed"],
        el_deg=thr["el_deg"],
        az_off_deg=thr["az_off_deg"],
    )
    if record:
        out["log"] = log
    return out


def run_batch(seeds, variant="BIO-embodied", verbose=True):
    results = []
    for s in seeds:
        res = run_trial(s, variant=variant)
        results.append(res)
        if verbose:
            stat = "SUKCES" if res["success"] else f"PORAŻKA ({res['cls']})"
            print(f"[{variant}] Seed {s:3d}: {stat:<18} d_min={res['min_dball_mm']:5.1f} mm, d_fin={res['final_dball_mm']:5.1f} mm, hold={res['hold_N']:4.2f} N")
    return results


def summarize(results, name=""):
    n = len(results)
    k = sum(r["success"] for r in results)
    pct = 100.0 * k / n if n > 0 else 0.0
    lo, hi = tc.wilson(k, n) if n > 0 else (0.0, 0.0)
    
    classes = {}
    for r in results:
        if not r["success"]:
            classes[r["cls"]] = classes.get(r["cls"], 0) + 1
    cls_str = ", ".join(f"{c}: {cnt}" for c, cnt in sorted(classes.items(), key=lambda kv: -kv[1])) or "brak"
    
    crush_cnt = sum(r["crush"] for r in results)
    d_mins = [r["min_dball_mm"] for r in results]
    
    print(f"\n=== Wyniki wariantu: {name or 'Test'} (n={n}) ===")
    print(f"Sukcesy:     {k}/{n} = {pct:.1f}% [95% CI: {100*lo:.1f}% - {100*hi:.1f}%]")
    print(f"Porażki:     {cls_str}")
    print(f"Zgniecenia:  {crush_cnt}/{n}")
    print(f"Min d_ball:  mediana={np.median(d_mins):.1f} mm, p90={np.percentile(d_mins, 90):.1f} mm")
    return dict(n=n, k=k, pct=pct, lo=lo, hi=hi, crush=crush_cnt, classes=classes, d_med=np.median(d_mins))


def compare_all(seeds):
    variants = ["BIO-embodied", "BIO-les-LPLC", "BIO-les-PFL3", "BIO-shuffle", "ENG-vacuum"]
    all_res = {}
    for v in variants:
        print(f"\n--- Uruchamianie wariantu: {v} na {len(seeds)} próbach ---")
        res = run_batch(seeds, variant=v, verbose=False)
        all_res[v] = res
        summarize(res, name=v)
        
    print("\n" + "="*80)
    print(f"{'Wariant':<16} | {'Sukces':<14} | {'95% Wilson CI':<16} | {'Mediana d_min':<14} | {'Główna przyczyna'}")
    print("-" * 80)
    for v in variants:
        res = all_res[v]
        n = len(res)
        k = sum(r["success"] for r in res)
        pct = 100.0 * k / n
        lo, hi = tc.wilson(k, n)
        d_med = np.median([r["min_dball_mm"] for r in res])
        classes = {}
        for r in res:
            if not r["success"]:
                classes[r["cls"]] = classes.get(r["cls"], 0) + 1
        top_cls = sorted(classes.items(), key=lambda kv: -kv[1])[0] if classes else ("-", 0)
        top_str = f"{top_cls[0]} ({top_cls[1]})" if top_cls[0] != "-" else "brak"
        print(f"{v:<16} | {k:2d}/{n:2d} ({pct:4.1f}%) | [{100*lo:4.1f}% - {100*hi:4.1f}%]  | {d_med:6.1f} mm      | {top_str}")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="Wcielony kontroler łapania SO-101")
    parser.add_argument("mode", choices=["test", "compare", "one", "validate"], default="test", nargs="?")
    parser.add_argument("seeds", nargs="?", default="100:120")
    parser.add_argument("--variant", default="BIO-embodied")
    args = parser.parse_args()
    
    if ":" in args.seeds:
        a, b = map(int, args.seeds.split(":"))
        seeds = list(range(a, b))
    else:
        seeds = [int(args.seeds)]
        
    if args.mode == "one":
        r = run_trial(seeds[0], variant=args.variant, record=True)
        print(f"Wynik próby {seeds[0]} ({args.variant}): sukces={r['success']}, cls={r['cls']}, min_d={r['min_dball_mm']:.1f} mm, hold_N={r['hold_N']:.2f} N")
    elif args.mode == "compare":
        compare_all(seeds)
    elif args.mode == "validate":
        compare_all(list(range(150, 180)))
    else:
        res = run_batch(seeds, variant=args.variant, verbose=True)
        summarize(res, name=args.variant)


if __name__ == "__main__":
    main()
