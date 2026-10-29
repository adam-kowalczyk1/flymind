# Łańcuch bez MuJoCo: SNN (mózg bio2, tylko dane) → SteerDecoder → całkowanie ω → SafetyLayer → ZASTĘPCZY serwo (kinematyka)
# Widzenie: SensoryGate na odtwarzanym klipie z utratą klatek (tylko wiek obrazu; obraz nie steruje siecią — napęd PFL3 = proxy).
import sys, time
S = "/private/tmp/claude-501/-Users-admin-so101-fly-project/6454b16d-a7f4-423a-a824-4d37dc6a0832/scratchpad/"
exec(open(S + "check_decoder_real.py").read().split("XC, XT")[0])
from safety import SafetyLayer, Limits, Command, ranges_from_mjcf
from sensory import SensoryGate, replay, spot_clip
R = ranges_from_mjcf("/Users/admin/so101_fly_project/assets/so101_upstream.xml")
print("zakresy SO-101 [rad]:", R.round(3).tolist())
T = 600                                          # 6 s po 10 ms
rng = np.random.default_rng(1001)
clip = spot_clip(np.zeros(T), 0.0, (96, 128), 70.0)
drop = set(range(250, 290)) | set(np.flatnonzero(rng.random(T) < 0.02))    # 400 ms zasłonięcia kamery + 2 % utraty
frames = {f.seq: f for f in replay(clip, 0.01, delay=0.004, drop=drop)}
gate = SensoryGate((96, 128), 0.01, 0.03, 0.05)
dec = SteerDecoder(idx, ("DNa02",), [-0.63], [-37.68], SteerParams())     # kalibracja z check_decoder_real (tylko dane)
net, safe = ALIF(specs["data"], P, 1001), SafetyLayer(Limits(R))
q, last_img, tgt, log, dts = np.zeros(6), -1.0, 0.0, [], []
for k in range(T):
    t = k * 0.01
    if k in frames:
        smp = gate.push(frames[k], frames[k].t_receive)
        if smp.usable: last_img = frames[k].t_capture
    x = 1.0 if (k // 100) % 2 == 0 else -1.0                              # proxy kierunku: przełączany co 1 s
    o = dec.step(net.run(drive(x), 10), 1.0)
    tgt = tgt + o["omega"] * 0.01
    t0 = time.perf_counter()
    out, tau, flags, per = safe.step(Command(t, {0: tgt}, None, {0: "snn:DNa02"}), q, t, t - last_img)
    dts.append(time.perf_counter() - t0)
    tgt = out[0]
    q[:5] += np.clip(out - q[:5], -4.7 * 0.01, 4.7 * 0.01)                # zastępczy serwo, nie fizyka
    log.append((o["omega"], out[0], q[0], per.get(0, ())))
om, tg, qq = (np.array([l[i] for l in log]) for i in range(3))
print("statystyki bramki:", {k: v for k, v in gate.stats.items() if v})
print("interwencje warstwy:", safe.stats["per_source"], " hold:", safe.stats["hold"])
st = [k for k, l in enumerate(log) if "vision_stale" in l[3]]
print(f"vision_stale: {len(st)} taktów, pierwszy {st[0] if st else None}, ostatni {st[-1] if st else None}")
print(f"ω [rad/s]: min {om.min():+.2f} max {om.max():+.2f};  cel bazy: {tg.min():+.3f}…{tg.max():+.3f} rad;"
      f"  max|Δcel| {np.abs(np.diff(tg)).max():.4f} rad/takt;  max|cel − q| {np.abs(tg - qq).max():.4f} rad")
print(f"czas SafetyLayer.step: mediana {np.median(dts)*1e6:.0f} µs, max {max(dts)*1e6:.0f} µs (jedna maszyna)")
