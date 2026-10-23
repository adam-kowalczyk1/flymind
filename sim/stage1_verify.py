"""Etap 1 — weryfikacja: 10 s symulacji, pętla 100 Hz (10 kroków fizyki po 1 ms).
Sterowanie skryptowe (bez SNN): ramię w pozie „bramkarza”, kulka stacza się z równi do
paszczy, po dotyku dłoni szczęki się zamykają, potem uniesienie. Sprawdza kolizje,
odczyty czujników dotyku i czas pętli.
"""
import sys
import time

import mujoco
import numpy as np

import scene

SERVO_SPEED = 4.7   # rad/s — STS3215 bez obciążenia ok. 0,222 s/60° @7,4 V (karta katalogowa, ok.)
GRIP_PWM = 0.25     # domykanie 0,84 N·m
HOLD_PWM = 0.05     # trzymanie 0,17 N·m po dotyku obu szczęk. Stały PWM 0,25–0,35 daje 10–17 N i wyciska
                    # miękką kulkę ze szczęk ustawionych w „V”; pełny PWM (3,35 N·m) dawał 72 N


def geom_pairs(m, d):
    pairs = set()
    for c in d.contact[:d.ncon]:
        a, b = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"#{g}" for g in (c.geom1, c.geom2))
        pairs.add(tuple(sorted((a, b))))
    return pairs


def main(T=10.0):
    m, d = scene.load()
    q_catch, err = scene.ik_catch_pose(m, d, r=0.28)
    q_lift = q_catch.copy()
    q_lift[1] -= 0.25                       # bark w górę ≈ uniesienie
    mujoco.mj_resetData(m, d)
    d.qpos[:5] = q_catch
    d.qpos[5] = 1.0
    d.ctrl[:5] = q_catch
    d.ctrl[5] = 0.0                        # PWM 0: szczęka stoi (tarcie stawu)
    mujoco.mj_forward(m, d)

    n_sub = round(scene.CONTROL_DT / m.opt.timestep)
    steps = round(T / scene.CONTROL_DT)
    seen, touch_log, loop_ms, phase_t = set(), [], [], {}
    target = d.ctrl.copy()
    phase = "czekam"
    for k in range(steps):
        t0 = time.perf_counter()
        t = d.time
        touch = d.sensordata[:3].copy()
        if phase == "czekam" and touch.sum() > 0.05:
            phase, phase_t["kontakt"] = "zamykam", t
        if phase == "zamykam":
            # skryptowo (SNN dopiero w Etapie 3): domknij, po dotyku obu szczęk zmniejsz moment
            target[5] = -(HOLD_PWM if "obie_szczeki" in phase_t else GRIP_PWM)
            if touch[0] > 0.05 and touch[1] > 0.05:
                phase_t.setdefault("obie_szczeki", t)
            if "obie_szczeki" in phase_t and t - phase_t["obie_szczeki"] > 0.3:
                phase, phase_t["unoszenie"] = "unoszę", t
        if phase == "unoszę":
            target[:5] = q_lift
        # ograniczenie prędkości serw pozycyjnych ramienia; chwytak (PWM) bez ograniczenia
        d.ctrl[:5] = d.ctrl[:5] + np.clip(target[:5] - d.ctrl[:5], -SERVO_SPEED * scene.CONTROL_DT,
                                          SERVO_SPEED * scene.CONTROL_DT)
        d.ctrl[5] = target[5]
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
        seen |= geom_pairs(m, d)
        touch_log.append(d.sensordata[:3].copy())
        loop_ms.append((time.perf_counter() - t0) * 1e3)
        if not np.isfinite(d.qpos).all():
            print("BŁĄD: niestabilna fizyka (NaN)")
            return 1

    touch_log = np.array(touch_log)
    loop_ms = np.array(loop_ms)
    ball = d.body("ball").xpos
    print(f"IK pozy chwytu: błąd {err*1000:.1f} mm, q = {np.round(q_catch, 3)}")
    print(f"Symulacja {T:.0f} s: {steps} cykli × {n_sub} kroków po {m.opt.timestep*1e3:.0f} ms")
    print(f"Czas cyklu 10 ms (ściana): średnio {loop_ms.mean():.2f} ms, p99 {np.percentile(loop_ms, 99):.2f} ms, "
          f"max {loop_ms.max():.2f} ms → zapas czasu x{scene.CONTROL_DT*1e3/np.percentile(loop_ms, 99):.1f}")
    ball_pairs = sorted(p for p in seen if "ball" in p)
    print("Kontakty kulki:", ball_pairs)
    other = sorted(p for p in seen if "ball" not in p)
    print("Inne kontakty (ramię/stół):", other if other else "brak")
    for i, s in enumerate(scene.SENSORS):
        print(f"  czujnik {s:10s}: max {touch_log[:, i].max():6.2f} N, końcowo {touch_log[-1, i]:5.2f} N")
    print("Zdarzenia:", {k: round(v, 3) for k, v in phase_t.items()})
    print(f"Kulka na końcu: {np.round(ball, 3)} (z>{scene.BALL_R+0.02:.3f} = uniesiona)")

    checks = {
        "fizyka stabilna (brak NaN)": True,
        "kulka dotknęła równi i stołu": {("ball", "ramp"), ("ball", "table")} <= set(ball_pairs),
        "kulka dotknęła padów chwytaka": any(p for p in ball_pairs if any(n in p for n in ("jaw_fixed", "jaw_moving", "palm"))),
        "obie szczęki czują nacisk": "obie_szczeki" in phase_t,
        "kulka uniesiona": ball[2] > scene.BALL_R + 0.02,
        "pętla 100 Hz mieści się w czasie rzeczywistym (p99 < 10 ms)": np.percentile(loop_ms, 99) < 10.0,
    }
    for k, v in checks.items():
        print(("OK   " if v else "BŁĄD ") + k)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
