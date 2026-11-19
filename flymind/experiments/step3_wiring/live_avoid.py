"""„Nie dać się dotknąć” NA ŻYWO (19 XI): prawdziwa kamera nadgarstka + prawdziwe czujniki FSR → TEN SAM mózg co avoid.py
(head.HeadLife(eyes=True), dotyk hw2p: A0 szczęka stała → „udo”, A1 = dłoń → szczecinki BM) → ramię W SYMULACJI (kinematyka).
Do prawdziwego ramienia NIC nie jest wysyłane (Adam: pierwszy ruch tylko na jego „ruszamy”).
Kod klasyczny = TYLKO czujniki: wykrycie ręki w obrazie (różnica od tła) → kąt widzenia θ → L = dθ/dt → komórki zbliżania oka
(jak avoid.py: 40 mV przy 2 rad/s, strona z położenia ręki w kadrze); FSR → touch_map.from_counts (ta sama funkcja co w symulacji).
Mózg liczony szybciej (aktualizacja tylko od neuronów, które właśnie strzeliły — te same spiki co alif.ALIF.step, sprawdzane w --check).
Kamera działa tylko z Terminal.app (uprawnienia macOS).  Uruchom:
  live_avoid.py --cam "USB Camera" [--fsr /dev/cu.usbmodemXXXX --r-fix 10000] [--seconds 60] [--out log.npz] [--brake hub] [--fov 70] [--flip]
  live_avoid.py --video plik.mp4 [--fsr-csv plik.csv]       (nagranie zamiast kamery)
  live_avoid.py --check                                      (sprawdzian bez sprzętu, ~2 min)
Podgląd na żywo: http://127.0.0.1:8793 (strona hardware/sensors/test_czujnikow.html, punkt 3; --serve 0 wyłącza)."""
import argparse
import base64
import csv
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import alive  # noqa: E402
import avoid as A  # noqa: E402
import fly_mode as FM  # noqa: E402
import head  # noqa: E402
import reflex as R  # noqa: E402
import touch_map as TM  # noqa: E402

FF = "/Users/admin/miniforge3/bin/ffmpeg"
W_PX, H_PX = 160, 100                     # obraz zmniejszany przez ffmpeg (ręce są duże; ponytail: większy, gdy trzeba szczegółu)
BG_S, THR, BG_A = 1.5, 25, 0.02           # s do zdjęcia tła (ręka poza kadrem!), próg różnicy jasności 0–255, tempo uczenia tła
LIVE = {}                                 # najnowszy stan (co 100 ms) dla strony hardware/sensors/test_czujnikow.html
PAGE = os.path.join(HERE, "../../../hardware/sensors/test_czujnikow.html")
ESC = ("DNp01", "DNp02", "DNp04", "DNp11")


def fast_step(s, Wc):
    """alif.ALIF.step, ale wkład synaps liczony tylko z kolumn neuronów, które strzeliły (≈75/15 571) → ~10× szybciej, te same spiki."""
    def step(I_ext):
        p, dt = s.p, s.p.dt
        slot = s.t % p.delay_steps
        idx = np.flatnonzero(s.buf[slot])
        s.g -= s.g * dt / p.tau_syn
        if idx.size:
            s.g += Wc[:, idx].sum(axis=1).A1
        I = I_ext + p.noise * s.rng.standard_normal(s.N) if p.noise else I_ext
        s.v += dt / p.tau_m * (p.v_rest - s.v + s.gain * (s.g + I) - s.a)
        s.v[s.ref > 0] = p.v_reset
        s.ref -= dt
        spk = s.v >= p.v_th
        s.v[spk] = p.v_reset
        s.ref[spk] = p.t_ref
        s.a += -s.a * dt / p.tau_a + s.b_a * spk
        s.buf[slot] = spk
        s.t += 1
        return spk
    return step


class Frames:
    """ffmpeg → szare klatki W_PX×H_PX w wątku; trzyma tylko najnowszą."""
    def __init__(self, cam=None, video=None, fps=120, size="640x400"):   # kamera_diag 19 XI: 640x400@120 → ~78 kl./s; 1280x800 → tylko 10
        src = (["-fflags", "nobuffer", "-f", "avfoundation", "-framerate", str(fps), "-video_size", size, "-i", cam] if cam
               else ["-re", "-i", video])
        self.p = subprocess.Popen([FF, "-nostdin", "-loglevel", "error", *src, "-vf", f"scale={W_PX}:{H_PX},format=gray",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.last, self.n, self.t0 = None, 0, time.time()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        k = W_PX * H_PX
        while True:
            b = self.p.stdout.read(k)
            if len(b) < k:
                self.last = "end" if self.last is not None else None
                return
            self.last, self.n = np.frombuffer(b, np.uint8).reshape(H_PX, W_PX), self.n + 1

    def stop(self):
        self.p.kill()


class Touch:
    """Najnowszy odczyt Arduino `ms,A0,A1` (port: tylko ODCZYT; csv: odtwarzane w swoim tempie)."""
    def __init__(self, port=None, path=None, r_fix=TM.R_FIX):
        self.c, self.r_fix = (0, 0), r_fix
        if port or path:
            threading.Thread(target=self._read, args=(port, path), daemon=True).start()

    def _read(self, port, path):
        if port:
            import serial
            s = serial.Serial(port, 115200, timeout=1)
            lines = (s.readline().decode(errors="ignore") for _ in iter(int, 1))
        else:
            lines = open(path)
        t0 = None
        for ln in lines:
            r = ln.strip().split(",")
            if len(r) != 3 or not all(x.isdigit() for x in r):
                continue
            ms, a0, a1 = map(int, r)
            if path:                                           # tempo nagrania
                t0 = t0 if t0 is not None else time.time() - ms / 1000
                time.sleep(max(0.0, t0 + ms / 1000 - time.time()))
            self.c = (a0, a1)


class Eye:
    """Ręka w kadrze = piksele różne od tła. Tło: pierwsza klatka po BG_S (kamera kończy ustawiać naświetlenie), potem powoli
    uczy się tam, gdzie ręki nie ma. Jasność liczona względem mediany klatki (auto-naświetlenie nie udaje ręki)."""
    def __init__(self, fov_deg=70.0, flip=False):
        self.tan, self.flip, self.bg, self.t_last = np.tan(np.radians(fov_deg) / 2), flip, None, None
        self.th, self.L, self.sa = 0.0, 0.0, 0.0

    def see(self, f, dt, t):
        if t < BG_S:
            return 0.0
        g = f.astype(float) - np.median(f)
        if self.bg is None:
            self.bg, self.t_last = g, t
            return 0.0
        dt, self.t_last = max(dt, t - self.t_last), t          # prawdziwy odstęp między klatkami (kamera ~10 kl./s, takt 10 ms)
        m = self.m = np.abs(g - self.bg) > THR
        self.bg[~m] += BG_A * (g - self.bg)[~m]
        a = m.mean()
        th = 2 * np.arctan(np.sqrt(a) * self.tan)               # plama jak kwadrat o boku √a szerokości kadru
        self.L = 0.7 * self.L + 0.3 * max(0.0, (th - self.th) / dt)
        self.th = th
        if a > 0.002:
            cx = (np.nonzero(m)[1].mean() / (W_PX - 1)) * 2 - 1    # −1 lewa krawędź kadru, +1 prawa
            self.sa = float(np.clip(-cx if not self.flip else cx, -1, 1))   # sa > 0 = ręka po LEWEJ muchy (jak avoid.py)
        return self.L


def build(glu=-1, brake="hub", sigma=2.0, seed=19112026):
    net = head.HeadLife(glu, "N", eyes=True)
    mode = FM.resolve(brake)
    FM.apply(net, mode)
    net.pads = TM.pads_for(net, "somato")
    net._spec = R.JN.LB._W(net.W)
    net.net = R.SparseALIF(net._spec, R.ALIFParams(noise=sigma), seed)
    net.net.step = fast_step(net.net, net.net.W.tocsc())
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    import pandas as pd
    a = pd.read_feather(A.nets.visual_path.ANN, columns=["bodyId", "type"])
    grp = lambda ts: [net.pos[int(b)] for b in a.bodyId[a.type.isin(ts)] if int(b) in net.pos]  # noqa: E731
    net._grp = {"esc": grp(ESC), "MDN": grp(["MDN"]), "DNg15": grp(["DNg15"]), "DNge078": grp(["DNge078"])}
    net._eyes, net._feco, net._mode = A.eye_idx(net), alive.feco_idx(glu), mode
    net._world = R.JN.ForceWorld([("cyl", R.JN.oh.BASE_MATS[0])], 1)     # tylko kąty startowe i granice stawów SO-101
    return net


def loop(net, frames, touch, eye, seconds, realtime=True, say=print):
    """Takt 10 ms. Zwraca log. Ramię: pule stawów 1–3 → kąty celu w symulacji (jak avoid.py), granice z modelu SO-101."""
    w = net._world
    q6 = w.sim.d.qpos[w.sim.qadr].copy()
    lo, hi = w.sim.m.jnt_range[1:4, 0], w.sim.m.jnt_range[1:4, 1]
    st, run0, last = dict(loom={"L": 0.0, "R": 0.0}, qd=np.zeros(6)), net.net.run, {}

    def run_senses(X, n):
        X = X.copy()
        for s, ix in net._eyes.items():
            X[ix] = st["loom"][s]
        e, v = q6[2] / alive.Q_LIM, st["qd"][2]
        for k, x in (("claw_flex", e), ("claw_ext", -e), ("hook_flex", v), ("hook_ext", -v)):
            X[net._feco[k]] = 40.0 * min(1.0, max(0.0, x))
        last["s"] = run0(X, n)
        return last["s"]
    net.net.run = run_senses
    log = {k: [] for k in ("t", "L", "th", "sa", "A0_N", "P_N", "esc", "MDN", "DNg15", "DNge078", "q", "lag", "cnt")}
    t0, seen, acc = time.time(), -1, []
    try:
        for i in range(int(seconds / A.DT)):
            t = i * A.DT
            if realtime:
                time.sleep(max(0.0, t0 + t - time.time()))
            f = frames.last if frames else None
            if frames and i == int(2 / A.DT):
                say(f"[kamera: {frames.n / (time.time() - frames.t0):.0f} kl./s" + (" — BRAK OBRAZU, przerwij Ctrl+C]" if frames.n == 0 else "]"))
            if isinstance(f, str):
                break                                                  # koniec nagrania
            L = eye.see(f, A.DT, t) if f is not None and frames.n != seen else eye.L
            seen = frames.n if frames else seen
            drive = A.MV * min(1.0, L / A.L_FULL)
            st["loom"] = {"L": drive * (1 + eye.sa) / 2, "R": drive * (1 - eye.sa) / 2}
            felt = TM.from_counts(*touch.c, touch.r_fix)
            dq = net.step(np.array([felt[0], 0.0, felt[1]]), q6[:5], st["qd"][:5], A.DT)   # hw2p: A1 = dłoń → BM
            q1 = np.clip(q6[1:4] + dq[1:4], lo, hi)
            st["qd"][1:4] = (q1 - q6[1:4]) / A.DT
            q6[1:4] = q1
            s = last["s"] * 1000.0
            row = dict(t=t, L=L, th=eye.th, sa=eye.sa, A0_N=felt[0], P_N=felt[1], q=q6[1:4].copy(), lag=time.time() - t0 - t, cnt=np.array(touch.c, float),
                       **{k: float(s[:, ix].mean()) for k, ix in net._grp.items()})
            for k, v in row.items():
                log[k].append(v)
            acc.append(row)
            if len(acc) == 10:
                m = {k: np.mean([r[k] for r in acc], axis=0) for k in acc[0]}
                say(f"t={m['t']:5.1f}s ręka θ={np.degrees(m['th']):4.0f}° L={m['L']:4.2f} strona={m['sa']:+.1f} | dotyk A0={m['A0_N']:.1f}N "
                    f"dłoń={m['P_N']:.1f}N | ucieczka={m['esc']:5.1f}Hz MDN={m['MDN']:5.1f} DNg15={m['DNg15']:5.1f} | "
                    f"ramię(sym.)°={np.round(np.degrees(m['q'])).astype(int).tolist()} opóźn={1000 * m['lag']:.0f}ms")
                LIVE.update(t=round(float(m["t"]), 2), th=float(np.degrees(m["th"])), L=float(m["L"]), sa=float(m["sa"]),
                            A0_N=float(m["A0_N"]), P_N=float(m["P_N"]), cnt=[int(x) for x in m["cnt"]],
                            q=np.degrees(m["q"]).round(1).tolist(), q0=np.degrees(log["q"][0]).round(1).tolist(), lag=float(1000 * m["lag"]),
                            fps=round(frames.n / (time.time() - frames.t0), 1) if frames else 0,
                            Hz={k: round(float(m[k]), 1) for k in net._grp}, **_img(f, eye))
                acc = []
    except KeyboardInterrupt:
        say("przerwane (Ctrl+C) — zapisuję to, co jest")
    return {k: np.array(v) for k, v in log.items()}


def _img(f, eye):
    """Klatka 160×100 (szarość) i maska ręki jako base64 dla strony."""
    if f is None or isinstance(f, str):
        return {}
    m = getattr(eye, "m", None)
    m = np.zeros_like(f, bool) if m is None else m
    return dict(w=W_PX, h=H_PX, img=base64.b64encode(f.tobytes()).decode(), mask=base64.b64encode(m.astype(np.uint8).tobytes()).decode())


def serve(port):
    """http://127.0.0.1:port/ = strona testu czujników z panelem muchy, /stan = LIVE jako JSON. Tylko localhost."""
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/stan"):
                body, ct = json.dumps(LIVE).encode(), "application/json"
            else:
                body, ct = open(PAGE, "rb").read(), "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _synthetic(path, n=600, fps=120):
    """Nagranie próbne: szare tło; 2–3,5 s ciemna „ręka” rośnie po lewej stronie kadru (zbliżanie), potem stoi do 5 s."""
    yy, xx = np.mgrid[:200, :320]
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "320x200", "-r", str(fps),
                          "-i", "-", "-c:v", "ffv1", path], stdin=subprocess.PIPE)
    for k in range(n):
        f = np.full((200, 320), 150, np.uint8)
        r = 0 if k < 240 else 5 + 0.0025 * (min(k, 420) - 240) ** 2   # przyspieszające rośnięcie, od 3,5 s stoi
        f[(xx - 90) ** 2 + (yy - 100) ** 2 < r * r] = 40
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def _check():
    import tempfile
    d = tempfile.mkdtemp()
    net = build(brake="intact")
    ref = R.SparseALIF(net._spec, R.ALIFParams(noise=2.0), 7)
    fst = R.SparseALIF(net._spec, R.ALIFParams(noise=2.0), 7)
    fst.step = fast_step(fst, fst.W.tocsc())
    X = np.zeros(net.N)
    X[net._eyes["L"]] = 30.0
    assert (ref.run(X, 200) == fst.run(X, 200)).all(), "szybki krok daje inne spiki"
    vid, fcsv = os.path.join(d, "v.mkv"), os.path.join(d, "f.csv")
    _synthetic(vid)
    rows = [(10 * k, 2, 4) for k in range(400)] + [(10 * k, 2, 700) for k in range(400, 500)]   # 4 s spokoju, 1 s nacisk dłoni
    csv.writer(open(fcsv, "w")).writerows(rows)
    net.net = R.SparseALIF(net._spec, R.ALIFParams(noise=2.0), 19112026)     # świeży stan po porównaniu
    net.net.step = fast_step(net.net, net.net.W.tocsc())
    log = loop(net, Frames(video=vid), Touch(path=fcsv), Eye(), 5.5, say=lambda s: print(s, flush=True))
    t, L, th = log["t"], log["L"], log["th"]
    grow, held = np.gradient(th) > 1e-4, (th > 0.3) & (np.abs(np.gradient(th)) < 1e-6)
    assert grow.sum() > 50 and L[grow].max() > 0.3 and log["sa"][grow].mean() > 0.3, "zbliżanie z lewej niewidoczne"
    assert held.sum() > 30 and L[held][10:].max() < 0.05, "ręka stoi, a oko widzi zbliżanie"
    assert L[th == 0].max() == 0, "oko widzi coś w pustym kadrze"
    assert log["P_N"].max() > 1.0 and log["P_N"][:100].max() < 0.2, "nacisk dłoni nie dochodzi"
    print("live_avoid _check OK; max opóźnienie", round(1000 * log["lag"].max()), "ms; ucieczka przed/po ręce [Hz]:",
          round(log["esc"][th == 0].mean(), 1), round(log["esc"][grow].mean(), 1),
          "| DNg15 bez/w nacisku:", round(log["DNg15"][log["P_N"] < 0.2].mean(), 1), round(log["DNg15"][log["P_N"] > 1].mean(), 1),
          "| ramię Δ° =", np.round(np.degrees(log["q"][-1] - log["q"][0])).astype(int).tolist())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam")
    ap.add_argument("--video")
    ap.add_argument("--fps", type=int, default=120)
    ap.add_argument("--size", default="640x400")
    ap.add_argument("--fsr")
    ap.add_argument("--fsr-csv")
    ap.add_argument("--r-fix", type=float, default=TM.R_FIX, help="opornik dzielnika [Ω]: 10000 albo 5100 — jaki wstawiono")
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--glu", type=float, default=-1)
    ap.add_argument("--brake", default="hub", choices=("hub", "intact", "silenced"))
    ap.add_argument("--fov", type=float, default=70.0, help="poziomy kąt widzenia obiektywu [°] — do zmierzenia")
    ap.add_argument("--flip", action="store_true", help="zamień lewą/prawą stronę kadru")
    ap.add_argument("--out")
    ap.add_argument("--serve", type=int, default=8793, help="port strony na żywo (0 = bez strony)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        _check()
        sys.exit(0)
    if a.serve:
        serve(a.serve)
        print(f"strona na żywo: http://127.0.0.1:{a.serve}  (otwórz w przeglądarce)", flush=True)
    print("buduję mózg muchy (~45 s)…", flush=True)
    net = build(a.glu, a.brake)
    print(f"tryb mózgu: {net._mode}. Przez pierwszą sekundę trzymaj rękę POZA kadrem (kamera uczy się tła).", flush=True)
    fr = Frames(cam=a.cam, video=a.video, fps=a.fps, size=a.size) if (a.cam or a.video) else None
    log = loop(net, fr, Touch(a.fsr, a.fsr_csv, a.r_fix), Eye(a.fov, a.flip), a.seconds)
    if fr:
        print(f"kamera: {fr.n} klatek = {fr.n / max(1e-9, time.time() - fr.t0):.0f} kl./s", flush=True)
        fr.stop()
    if a.out:
        np.savez_compressed(a.out, **log)
