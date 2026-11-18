"""flymind/demo/demo_reflex.py — film na Explory: „dotyk przy głowie → odruch łokcia i nadgarstka; wycięcie neuronu → staw stoi”.
SYMULACJA MuJoCo, tylko wizualizacja kroku 6 (r2 sonda + r3 wycięcie). Niczego nie liczy po swojemu: woła reflex5.trial5 z siecią
brainleg.BrainNet i światem brainleg_probe.ProbeWorld bez zmian; wycięcie = to samo zerowanie wyjść co brainleg_lesion.py.
Dołożone są tylko haki, które PODGLĄDAJĄ (impulsy z SparseALIF.run, stan świata po kroku). Sceny TRENINGOWE (21 421 xxx), nie testowe.
test_demo_reflex.py sprawdza, że wynik próby z nagrywaniem = wynik bez nagrywania.

Uruchom (bez okna, NOWY katalog):  .venv/bin/python -I -B flymind/demo/demo_reflex.py --media flymind/demo/media_reflex_<data>
"""
import sys

sys.dont_write_bytecode = True
import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STEP3 = os.path.join(os.path.dirname(HERE), "experiments", "step3_wiring")
sys.path.insert(0, HERE)
sys.path.insert(0, STEP3)
import brainleg as B  # noqa: E402
import brainleg_probe as P  # noqa: E402
import reflex as R  # noqa: E402
import reflex5 as R5  # noqa: E402

import demo as D  # noqa: E402  (pomocnicze: _fig, _rgb, text_image, Video, overlay, add_fill_light, apply_cam, _out_ok)

SCENE = 21421                    # sceny treningowe kroku 6 (SEED_REGISTRY: w użyciu, trening) — NIE testowe 21831/21861/21891/21631
RUNS = (("N", "Sieć z danych muchy (nic nie wycięte)"),
        ("d15", "Wycięte 2 neurony DNg15 (szlak do łokcia)"),
        ("d78", "Wycięte 2 neurony DNge078 (szlak do nadgarstka)"))
HONEST = ("SYMULACJA (MuJoCo), nie żywa mucha i nie prawdziwy robot.\n"
          "Sieć: 3221 neuronów z mapy połączeń muchy MaleCNS v1.0.\n"
          "Klasyczny kod: dojazd, sonda (docisk 3 N przez 0,5 s), bezpiecznik.\n"
          "O ruchu łokcia i nadgarstka decyduje sieć.\n"
          "Testy (każdy raz, cel zapisany przed testem): odruch 26/26 prób;\n"
          "bez DNg15 łokieć rusza się 0/27; bez DNge078 nadgarstek 0/27.")
SUMMARY = ("Dotyk dłoni robota trafia do neuronów czucia głowy muchy (BM).\n"
           "Dalej sygnał idzie dwiema drogami znalezionymi w mapie połączeń:\n\n"
           "BM → DNg15 → łokieć prostuje się\n"
           "BM → DNge078 → nadgarstek unosi się\n\n"
           "Wytnij DNg15 — stoi tylko łokieć. Wytnij DNge078 — stoi tylko nadgarstek.\n"
           "Testy w symulacji: 26/26 odruchów; po wycięciu 0/27 dla właściwego stawu.\n\n"
           "To model z danych muchy, nie pomiar na żywej musze.")
W, H, PW = 1600, 900, 640        # klatka, szerokość panelu


class DemoNet(B.BrainNet):
    """BrainNet bez zmian + podgląd częstości BM / DNg15 / DNge078 + opcjonalne wycięcie (jak brainleg_lesion.py)."""

    def __init__(self, glu, lesion="N"):
        bm, d78, d15 = B.route_ids()
        pos = B.nets2.build_ext(glu, bm + d78 + d15)[4]
        self.ix = dict(BM=[pos[b] for b in bm], DNg15=[pos[b] for b in d15], DNge078=[pos[b] for b in d78])
        super().__init__(glu)
        if lesion != "N":
            cut = self.ix["DNg15" if lesion == "d15" else "DNge078"]
            mask = np.ones(self.N)
            mask[cut] = 0.0
            import scipy.sparse as sp
            self.W = sp.csr_matrix(self.W.multiply(mask[None, :])) if sp.issparse(self.W) else self.W * mask[None, :]
            self.reset()

    def reset(self):
        super().reset()
        self.hz = {k: 0.0 for k in getattr(self, "ix", {})}
        run0 = self.net.run

        def run(X, n):
            s = run0(X, n)
            for k, ix in self.ix.items():
                self.hz[k] = float(s[:, ix].mean()) * 1000.0
            return s

        self.net.run = run


class Rec:
    """Zbiera stan po każdym kroku świata i składa klatki: scena (lewo) + wykresy (prawo)."""

    def __init__(self, vid, title, net, lesion="N"):
        self.vid, self.title, self.net, self.lesion = vid, title, net, lesion
        self.log, self.n, self.r, self.t_net = [], 0, None, None
        self.fig, self.canvas = D._fig(PW, H)
        self.last = None

    def on_step(self, w, obs):
        import mujoco
        if self.r is None:
            m = w.sim.m
            m.vis.global_.offwidth, m.vis.global_.offheight = max(m.vis.global_.offwidth, W), max(m.vis.global_.offheight, H)
            self.r, self.cam = mujoco.Renderer(m, H, W - PW), mujoco.MjvCamera()
            m_ = w.sim.m
            self.qa = {j: m_.jnt_qposadr[m_.joint(j).id] for j in ("elbow_flex", "wrist_flex")}
            self.q0 = None
        d = w.sim.d
        probe = bool(w.pressed and w.phase == "net")
        if w.phase == "net" and self.t_net is None:
            self.t_net = obs.t
            self.q0 = {j: float(d.qpos[a]) for j, a in self.qa.items()}
        dq = {j: (np.degrees(float(d.qpos[a]) - self.q0[j]) if self.q0 else 0.0) for j, a in self.qa.items()}
        self.log.append(dict(t=obs.t, phase=w.phase, palm=float(obs.touch[2]), probe=probe, **self.net.hz,
                             elbow=-dq["elbow_flex"], wrist=float(R.JN.UP[3]) * dq["wrist_flex"]))   # + = prostowanie / unoszenie
        self.n += 1
        slow = w.phase in ("press", "net")
        if slow or self.n % 4 == 0:                            # 25 kl./s: zwykle czas rzeczywisty, odruch zwolniony 4×
            self.write(w, slow)

    def write(self, w, slow):
        f = self.frame(w, slow)
        self.vid.write(f)
        self.last = f

    def frame(self, w, slow):
        import mujoco  # noqa: F401
        s = self.log[-1]
        close = w.phase in ("press", "net")
        shot = ((0.24, 0.0, 0.10), 0.42, -60.0, -15.0) if close else ((0.20, 0.0, 0.09), 0.72, -40.0, -30.0)
        D.apply_cam(self.cam, shot, None)
        self.r.update_scene(w.sim.d, camera=self.cam)
        D.add_fill_light(self.r.scene)
        fr = np.zeros((H, W, 3), np.uint8)
        fr[:, :W - PW] = self.r.render()
        fr[:, W - PW:] = self.panel()
        cap = self.title + ("   ·   zbliżenie, zwolnione 4×" if slow else "")
        D.overlay(fr, D.text_image(cap, W - PW, 46, size=15, weight="bold"), 0, 0, 0.85)
        if s["probe"]:
            D.overlay(fr, D.text_image("SONDA DOTYKA DŁONI (3 N)", 360, 40, size=14, fg="#ffd166", weight="bold"), 20, 60, 0.9)
        return fr

    def panel(self):
        f = self.fig
        f.clear()
        L = [x for x in self.log if self.t_net is not None and x["t"] >= self.t_net - 0.2] or self.log[-1:]
        t = np.array([x["t"] for x in L]) - (self.t_net or L[0]["t"])
        f.text(0.04, 0.975, "Co robi sieć muchy", fontsize=15, weight="bold", color="#e6edf3", va="top")
        spec = (("palm", "dotyk dłoni [N] → neurony BM (szczecinki głowy)", ("#4ea8ff",)),
                (("BM", "DNg15", "DNge078"), "częstość neuronów [Hz]", ("#4ea8ff", "#ff9f43", "#2ec27e")),
                (("elbow", "wrist"), "ruch stawu od początku dotyku [°]", ("#ff9f43", "#2ec27e")))
        cut = " (WYCIĘTY: impulsy nigdzie nie dochodzą)"
        names = dict(BM="BM (69)", DNg15="DNg15 → łokieć" + (cut if self.lesion == "d15" else ""),
                     DNge078="DNge078 → nadgarstek" + (cut if self.lesion == "d78" else ""),
                     elbow="łokieć: prostowanie", wrist="nadgarstek: unoszenie")
        for i, (keys, ttl, cols) in enumerate(spec):
            ax = f.add_axes([0.13, 0.67 - i * 0.235, 0.83, 0.17], facecolor="#000")
            for k, c in zip((keys,) if isinstance(keys, str) else keys, cols):
                ax.plot(t, [x[k] for x in L], color=c, lw=2, label=names.get(k, k))
            if i == 1:
                ax.set_ylim(-10, 480)
            ax.set_xlim(-0.2, 0.7)
            ax.set_title(ttl, fontsize=11, color="#e6edf3", loc="left")
            ax.tick_params(colors="#9aa7b4", labelsize=9)
            for sp_ in ax.spines.values():
                sp_.set_color("#3a4450")
            if not isinstance(keys, str):
                ax.legend(fontsize=9, loc="upper left", facecolor="#101418", labelcolor="#e6edf3", edgecolor="#3a4450")
        ax.set_xlabel("czas od początku dotyku [s]", fontsize=10, color="#9aa7b4")
        f.text(0.04, 0.115, HONEST, fontsize=7.6, color="#8fbf8f", va="top", linespacing=1.4)
        self.canvas.draw()
        return D._rgb(self.canvas)

    def close(self):
        if self.r is not None:
            if self.r._gl_context is not None:
                self.r._gl_context.make_current()
            self.r.close()


def install(rec_box):
    P.install()
    base = R.JN.ForceWorld                                    # = ProbeWorld po install()

    class RecWorld(base):
        def step(self, q_t, tau):
            obs = super().step(q_t, tau)
            if rec_box[0] is not None:
                rec_box[0].on_step(self, obs)
            return obs

    R.JN.ForceWorld = RecWorld


def run_one(glu, lesion, mi, pose, rec=None, box=None):
    """Jedna próba W (sonda) jak w brainleg_probe/brainleg_lesion. Zwraca rekord trial5."""
    net = DemoNet(glu, lesion)
    if rec is not None:
        rec.net = net
    box[0] = rec
    fc = R.sm.FlyCfg(glu_sign=glu, trigger="search")
    ac = R.JN.ArmCfg(version="reflex", joints=(1, 2, 3), roll=False, inputs=(), in_rule="fl")
    try:
        return R5.trial5(R.ITEMS["W"][mi], SCENE * 1000 + mi * 10 + pose, "W", net, fc, ac)
    finally:
        box[0] = None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--media", required=True, help="NOWY katalog na MP4 + zrzuty")
    ap.add_argument("--glu", type=float, default=1.0)
    ap.add_argument("--mat", type=int, default=0, help="indeks materiału walca (R.ITEMS['W'])")
    ap.add_argument("--pose", type=int, default=0)
    a = ap.parse_args()
    if not D._out_ok(a.media) or os.path.exists(a.media):
        sys.exit(f"{a.media}: tylko NOWY katalog w flymind/demo/ albo /tmp")
    os.makedirs(a.media)
    box = [None]
    install(box)
    vid = D.Video(os.path.join(a.media, "demo_reflex.mp4"), W, H)
    t0, out = time.time(), []
    import matplotlib.image as mpimg
    try:
        for lesion, title in RUNS:
            vid_title = D.text_image(title + "\n\nza chwilę: sonda dotyka dłoni robota", W, H, size=30, weight="bold", align="center")
            for _ in range(50):
                vid.write(vid_title)
            rec = Rec(vid, title, None, lesion)
            r = run_one(a.glu, lesion, a.mat, a.pose, rec, box)
            for _ in range(40):                                # 1,6 s stopklatki z pełnymi wykresami
                vid.write(rec.last)
            shot = os.path.join(a.media, f"demo_reflex_{lesion}.png")
            mpimg.imsave(shot, rec.last)
            rec.close()
            out.append(dict(lesion=lesion, title=title, shot=shot, **{k: r.get(k) for k in
                                                                       ("item", "seed", "valid", "dq2", "dq3_lev", "reason")}))
            print(json.dumps(out[-1], ensure_ascii=False, default=float), flush=True)
        end = D.text_image(SUMMARY, W, H, size=26, weight="bold", align="center")
        for _ in range(200):                                   # 8 s planszy końcowej
            vid.write(end)
        mpimg.imsave(os.path.join(a.media, "demo_reflex_podsumowanie.png"), end)
    finally:
        vid.close()
    info = dict(argv=sys.argv, glu=a.glu, scene_seed=SCENE, frames=vid.n, runs=out, wall_s=round(time.time() - t0, 1),
                note="sceny treningowe; ilustracja, nie test")
    with open(os.path.join(a.media, "info.json"), "x") as f:
        json.dump(info, f, indent=1, ensure_ascii=False, default=float)


if __name__ == "__main__":
    main()
