"""Poślizg w MuJoCo (cel: TARGET_slip_r1.md). Szczęki = schody co 1 mm z PRAWDZIWYCH siatek (placement.Gripper), czujniki =
walce Ø12,7 × 0,45 mm na ścianach (tylko pole czynne). Przedmiot w poprzek szczęk, szczęki w dół, potem rosnąca siła ciągnąca.
  slip.py --check   jedna próba + sprawdziany (geometria, siła czujnika = siła kontaktu)
  slip.py           wszystkie próby → results/slip_r1.json"""
import json
import os
import sys

import mujoco
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL  # noqa: E402

T_FSR = 0.45
LAYOUTS = {"T": [("fixed", (-7.9, -2.32, -96.24), (1, 0, 0)), ("fixed", (-11.6, -0.13, -73.39), (1, 0, 0))],
           "H": [("fixed", (-11.6, -0.13, -73.39), (1, 0, 0)), ("fixed", (2.89, -0.87, -35.8), (0, 0, -1))],
           "R": [("moving", (11.9, -1.25, -54.93), (-1, 0, 0)), ("moving", (11.9, 2.02, -71.88), (-1, 0, 0))]}


def stairs():
    """Pudełka-schody [mm] z siatek: (ciało, środek, pół-rozmiary). Szczęka ruchoma w pozie q = 0, w układzie gripper."""
    G = PL.Gripper()
    P, N = G.points(0.0)
    out = []
    for part, sgn in ((1, 1), (2, -1)):
        sel = (G.part == part) & (N[:, 0] * sgn > 0.9) & (P[:, 2] > -104.5) & (P[:, 2] < -38.0) & (np.abs(P[:, 0]) < 20) & (np.abs(P[:, 1]) < 15)
        for z in np.arange(-104.5, -38.0, 1.0):
            k = sel & (P[:, 2] >= z) & (P[:, 2] < z + 1)
            if k.sum() < 5:
                continue
            xf = P[k, 0].max() if sgn > 0 else P[k, 0].min()
            f = k & (np.abs(P[:, 0] - xf) < 0.5)
            y0, y1 = P[f, 1].min(), P[f, 1].max()
            out.append(("fixed" if part == 1 else "moving", (xf - sgn * 1.0, (y0 + y1) / 2, z + 0.5), (1.0, max((y1 - y0) / 2, 0.5), 0.5)))
    pal = (G.part == 0) & (N[:, 2] < -0.9) & (P[:, 2] > -37)
    x0, x1, y0, y1, zp = P[pal, 0].min(), P[pal, 0].max(), P[pal, 1].min(), P[pal, 1].max(), P[pal, 2].mean()
    out.append(("fixed", ((x0 + x1) / 2, (y0 + y1) / 2, zp + 1.0), ((x1 - x0) / 2, (y1 - y0) / 2, 1.0)))
    # zawias i poza szczęki (q = 0) względem gripper
    G._pose(0.0)
    m, d = G.m, G.d
    Rg, pg = d.xmat[G.g].reshape(3, 3), d.xpos[G.g]
    Rj, pj = d.xmat[G.jaw].reshape(3, 3), d.xpos[G.jaw]
    Rrel, prel = Rg.T @ Rj, Rg.T @ (pj - pg) * 1000
    return out, Rrel, prel, m.jnt_pos[G.jid] * 1000, m.jnt_axis[G.jid], (G.qlo, G.qhi), G


def quat_z_to(n):
    n = np.asarray(n, float) / np.linalg.norm(n)
    z = np.array([0, 0, 1.0])
    v, c = np.cross(z, n), z @ n
    if np.linalg.norm(v) < 1e-9:
        return (1, 0, 0, 0) if c > 0 else (0, 1, 0, 0)
    q = np.r_[1 + c, v]
    return tuple(q / np.linalg.norm(q))


def build(layout, obj, ctrl_q0=1.0):
    boxes, Rrel, prel, jpos, jaxis, (qlo, qhi), _ = stairs()
    mm = lambda v: " ".join(f"{x / 1000:.6f}" for x in v)
    def to_jaw(p):
        return Rrel.T @ (np.asarray(p, float) - prel)
    fixed, moving = [], []
    for i, (body, c, h) in enumerate(boxes):
        if body == "fixed":
            fixed.append(f'<geom name="f{i}" type="box" pos="{mm(c)}" size="{mm(h)}" contype="1" conaffinity="0" friction="0.5 0.005 0.0001"/>')
        else:
            moving.append(f'<geom name="m{i}" type="box" pos="{mm(to_jaw(c))}" size="{mm(h)}" contype="1" conaffinity="0" friction="0.5 0.005 0.0001"/>')
    for k, (body, c, n) in enumerate(LAYOUTS[layout]):
        n = np.asarray(n, float)
        cc = np.asarray(c, float) + n * T_FSR / 2
        if body == "moving":
            cc, n = to_jaw(cc), Rrel.T @ n
        g = (f'<geom name="fsr{k}" type="cylinder" pos="{mm(cc)}" quat="{" ".join(f"{x:.6f}" for x in quat_z_to(n))}" '
             f'size="{PL.R_ACT / 1000:.6f} {T_FSR / 2000:.6f}" contype="1" conaffinity="0" rgba="0 .6 0 1" friction="0.5 0.005 0.0001"/>')
        (fixed if body == "fixed" else moving).append(g)
    qj = np.zeros(4)
    mujoco.mju_mat2Quat(qj, Rrel.ravel())
    o = obj
    if o["kind"] == "rod":
        og = (f'<geom name="obj" type="capsule" fromto="{mm((0, -100 - o["off"], 0))} {mm((0, 100 - o["off"], 0))}" size="{o["D"] / 2000:.6f}" '
              f'mass="0.06" contype="0" conaffinity="1" condim="4" friction="0.5 0.005 0.0001"/>')
        half_x, z_low = o["D"] / 2, o["D"] / 2
    else:
        og = (f'<geom name="obj" type="box" pos="{mm((0, -o["off"], 0))}" size="0.01 0.01 0.01" mass="0.06" contype="0" conaffinity="1" condim="4" '
              f'friction="0.5 0.005 0.0001"/>')
        half_x, z_low = 10.0, 10.0
    return f"""<mujoco><compiler angle="radian" autolimits="true"/><option timestep="0.0005" gravity="0 0 -9.81" cone="elliptic" impratio="10"/>
<default><geom solref="0.002 1"/></default>
<worldbody>
 <body name="grip" pos="0 0 0.3">{''.join(fixed)}
  <body name="jaw" pos="{mm(prel)}" quat="{" ".join(f"{x:.6f}" for x in qj)}">
   <joint name="hinge" type="hinge" pos="{mm(jpos)}" axis="{" ".join(f"{x:.6f}" for x in jaxis)}" range="{qlo} {qhi}" armature="0.028" damping="0.6" frictionloss="0.052"/>
   <inertial pos="-0.00157495 -0.0300244 0.0192755" quat="0.69526504 0.71796504 -0.0245618 -0.0230097" mass="0.012" diaginertia="6.63582397e-06 5.29092012e-06 1.86522590e-06"/>{''.join(moving)}
  </body>
 </body>
 <body name="obj" pos="0 0 0.3"><freejoint name="obj"/>{og}</body>
</worldbody>
<actuator><motor name="grip" joint="hinge" gear="3.35" ctrlrange="-1 1"/></actuator></mujoco>""", half_x, z_low


def place(m, d, o, half_x, z_low, layout):
    """Przedmiot przy szczęce stałej: na głębokości d od czubka, 0,3 mm od najbardziej wystającej ściany w jego zasięgu."""
    boxes = stairs()[0]
    z_bot = -104.4 + o["d"]
    zc = z_bot + z_low
    xs = [c[0] + h[0] for b, c, h in boxes if b == "fixed" and h[2] < 1 and c[2] + h[2] >= z_bot and c[2] - h[2] <= z_bot + 2 * z_low]
    for b, c, n in LAYOUTS[layout]:
        if b == "fixed" and n[0] > 0 and abs(c[2] - zc) < PL.R_ACT + z_low:
            xs.append(c[0] + T_FSR)
    xc = max(xs) + half_x + 0.3
    d.qpos[m.jnt_qposadr[m.joint("obj").id]:][:7] = [xc / 1000, 0, 0.3 + zc / 1000, 1, 0, 0, 0]
    d.qpos[m.jnt_qposadr[m.joint("hinge").id]] = 0.4          # szczelina ~49 mm; z q=1,0 słaby chwyt nie zamykał się w 1 s (poprawka przed wynikami)
    mujoco.mj_forward(m, d)


def run(layout, o, ctrl, T=5.0, record=False):
    xml, hx, zl = build(layout, o)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    place(m, d, o, hx, zl, layout)
    ob = m.body("obj").id
    fs = [m.geom(f"fsr{k}").id for k in range(2)]
    og = m.geom("obj").id
    mg = m.body_mass[ob] * 9.81
    f6 = np.zeros(6)
    ts, F, X = [], [], []
    p_ref = q_ref = None
    n = int(T / m.opt.timestep)
    for i in range(n):
        t = i * m.opt.timestep
        d.ctrl[0] = -ctrl
        d.xfrc_applied[ob] = 0
        if t < 1.0:
            d.xfrc_applied[ob, 2] = mg                      # trzymany „w powietrzu”, aż szczęki się zamkną
        else:
            d.xfrc_applied[ob, 2] = -20.0 * min(1.0, (t - 1.0) / 4.0)
        mujoco.mj_step(m, d)
        if i % 2:
            continue
        f = [0.0, 0.0]
        for ci in range(d.ncon):
            c = d.contact[ci]
            if og in (c.geom1, c.geom2):
                for k in range(2):
                    if fs[k] in (c.geom1, c.geom2):
                        mujoco.mj_contactForce(m, d, ci, f6)
                        f[k] += abs(f6[0])
        # pozycja przedmiotu względem chwytaka (chwytak stoi)
        ts.append(t); F.append(f); X.append(np.r_[d.xpos[ob].copy(), d.xquat[ob].copy()])
    ts, F, X = np.array(ts), np.array(F), np.array(X)
    i1 = np.searchsorted(ts, 1.0)
    hold = F[i1 - 1]
    dp = np.linalg.norm(X[:, :3] - X[i1, :3], axis=1) * 1000
    ang = np.degrees(2 * np.arccos(np.clip(np.abs((X[:, 3:] * X[i1, 3:]).sum(1)), 0, 1)))
    slip = np.where((ts >= 1.0) & ((dp > 0.5) | (ang > 2.0)))[0]
    s = int(slip[0]) if len(slip) else None
    res = dict(layout=layout, obj=o, ctrl=ctrl, hold=hold.tolist(), q_hold=float(d.qpos[m.jnt_qposadr[m.joint("hinge").id]]),
               slip_t=float(ts[s]) if s is not None else None, M1=bool((hold > 0.2).any()))
    if s is not None:
        pre = (ts >= 1.0) & (ts <= ts[s] - 0.02)
        rel = np.abs(F[pre] - hold) / np.maximum(hold, 0.2)
        res["M2"] = bool((hold > 0.2).any() and (rel[:, hold > 0.2] >= 0.2).any())
        post = (ts > ts[s]) & (ts <= ts[s] + 0.2)
        res["M3"] = bool((hold > 0.2).any() and ((F[post][:, hold > 0.2] <= 0.5 * hold[hold > 0.2]).any()))
    if record:
        res["trace"] = dict(t=ts[::20].tolist(), F=F[::20].round(3).tolist(), dp=dp[::20].round(3).tolist())
    return res


def trials():
    for D in (8, 15, 25):
        for dd in (2, 6, 10):
            for off in (0, 60):
                yield dict(kind="rod", D=D, d=dd, off=off)
    for dd in (15, 30):
        for off in (0, 60):
            yield dict(kind="box", d=dd, off=off)


def main(check=False):
    if check:
        boxes = stairs()[0]
        fx = [c[0] + h[0] for b, c, h in boxes if b == "fixed" and h[2] < 1]
        assert abs(max(fx) - (-7.9)) < 0.6, f"czubek szczęki stałej w złym miejscu: {max(fx)}"
        # szczęka ruchoma w MJCF przy q = 0 musi leżeć tam, gdzie siatka (czubek ściany x ≈ +7,9 mm przy z ≈ −100)
        xml, hx, zl = build("T", dict(kind="rod", D=15, d=6, off=0))
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        mb = [b for b in boxes if b[0] == "moving" and b[2][2] < 1]
        tipbox = min(mb, key=lambda b: b[1][2])
        gi = [i for i in range(m.ngeom) if m.geom(i).name.startswith("m")]
        zs = d.geom_xpos[gi, 2] * 1000 - 300
        j = gi[int(np.argmin(zs))]
        face = d.geom_xpos[j] * 1000 - np.array([0, 0, 300]) - d.geom_xmat[j].reshape(3, 3)[:, 0] * 1.0
        assert np.abs(face - np.array(tipbox[1]) + np.array([1.0, 0, 0])).max() < 0.05, f"szczęka ruchoma w złym miejscu: {face} vs {tipbox[1]}"
        r = run("T", dict(kind="rod", D=15, d=6, off=0), 0.4, T=2.0, record=True)
        print(json.dumps({k: v for k, v in r.items() if k != "trace"}))
        assert -0.18 <= r["q_hold"] <= 0.6, f"szczęka poza zakresem / niezamknięta: {r['q_hold']}"
        assert r["hold"][0] > 0.2, "pręt Ø15 przy czubku nie naciska czujnika na czubku"
        print("check OK")
        return
    out = []
    for lay in LAYOUTS:
        for o in trials():
            for ctrl in (0.15, 0.4):
                r = run(lay, o, ctrl)
                out.append(r)
                print(lay, o, ctrl, "hold", np.round(r["hold"], 2), "slip", r["slip_t"], r.get("M2"), r.get("M3"), flush=True)
    summ = {}
    for lay in LAYOUTS:
        rs = [r for r in out if r["layout"] == lay]
        sl = [r for r in rs if r["slip_t"] is not None]
        summ[lay] = dict(n=len(rs), M1=float(np.mean([r["M1"] for r in rs])), n_slip=len(sl),
                         M2=float(np.mean([r["M2"] for r in sl])) if sl else None, M3=float(np.mean([r["M3"] for r in sl])) if sl else None)
    q1 = summ["T"]["M1"] >= 0.8 and summ["T"]["M1"] >= summ["H"]["M1"] + 0.3
    q2 = summ["T"]["M3"] is not None and summ["T"]["M3"] >= 0.8
    print(json.dumps(summ, indent=1), "\nQ1", "ZDANE" if q1 else "NIE ZDANE", "| Q2", "ZDANE" if q2 else "NIE ZDANE")
    json.dump(dict(summary=summ, Q1=q1, Q2=q2, trials=out), open(os.path.join(PL.OUT, "slip_r1.json"), "w"), indent=1)


if __name__ == "__main__":
    main(check="--check" in sys.argv)
