"""Gdzie dać DWA czujniki FSR402 na chwytaku SO-101 — statystyka kontaktów na PRAWDZIWYCH siatkach (cel: TARGET_placement_r1.md).
Metoda jak Kim i in. 2026 (arXiv 2611.10647): miejsca wybiera to, gdzie przedmioty i ręka naprawdę dotykają, nie intuicja.
Układ ciała `gripper` [mm]: szczęka stała ma wewnętrzną ścianę z normalną +x, czubki przy z ≈ −104, nadgarstek przy +z,
szczęka ruchoma obraca się wokół zawiasu (oś −y). Bez mózgu muchy (to pytanie o fizyczne miejsce czujnika).
  placement.py --check   sprawdziany geometrii (wzór obrotu vs MuJoCo, znane miejsce FSR1, sztuczne zdarzenia)
  placement.py           pełne liczenie → results/placement_r1.json + rysunki"""
import json
import os
import sys
import time

import mujoco
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
OUT = os.path.join(HERE, "results")
R_ACT, R_FOIL, T_FOIL, T_PUCK = 6.35, 9.14, 0.45, 1.45      # FSR402: pole czynne Ø12,7, folia Ø18,3 (karta katalogowa)
DENS = 8.0                                                  # punktów powierzchni na mm²
PLANE_TOL, COS_TOL = 0.3, 0.95
COVER = float(os.environ.get("FSR_COVER", 0.95))           # płaskość pola czynnego (cel: 0,95; wariant eksploracyjny: mniej)
TS = tuple(float(x) for x in os.environ.get("FSR_T", "0.45,1.45").split(","))   # grubości czujnika [mm] (cel: 0,45 i 1,45)
TAG = ("r1b" if COVER == 0.95 else f"r1b_cover{int(COVER * 100)}") + ("" if TS == (0.45, 1.45) else "_t" + "-".join(str(t) for t in TS))
TOUCH_TOL = 0.3                                             # mm: „najbardziej wystające” w śladzie
SEED_PTS, SEED_EV = 2011200, 2011201
PARTS = ("sts3215_03a_v1", "wrist_roll_follower_so101_v1", "moving_jaw_so101_v1")   # 0,1 = nieruchome, 2 = ruchoma


class Gripper:
    """Punkty powierzchni (barycentrycznie na trójkątach siatek) i ich położenie przy dowolnym kącie szczęki q."""
    def __init__(self):
        xml = open(os.path.join(ROOT, "assets/so101_upstream.xml")).read().replace('meshdir="assets"', 'meshdir="assets/so101_meshes"')
        os.chdir(ROOT)
        self.m = m = mujoco.MjModel.from_xml_string(xml)
        self.d = mujoco.MjData(m)
        self.g, self.jaw, self.jid = m.body("gripper").id, m.body("moving_jaw_so101_v1").id, m.joint("gripper").id
        self.qlo, self.qhi = m.jnt_range[self.jid]
        self.geoms = {}
        for i in range(m.ngeom):
            if m.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH and m.geom_group[i] == 2 and m.geom_bodyid[i] in (self.g, self.jaw):
                self.geoms[m.mesh(m.geom_dataid[i]).name] = i
        rng = np.random.default_rng(SEED_PTS)
        self.tri, self.bary, self.part = [], [], []
        V0, F = self._mesh(0.0)
        for k, name in enumerate(PARTS):
            v, f = V0[name], F[name]
            T = v[f]
            a = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1) / 2
            n = rng.poisson(a * DENS)
            ti = np.repeat(np.arange(len(f)), n)
            r1, r2 = rng.random(len(ti)), rng.random(len(ti))
            s = np.sqrt(r1)
            self.tri.append(f[ti]); self.bary.append(np.c_[1 - s, s * (1 - r2), s * r2]); self.part.append(np.full(len(ti), k))
        self.F = F
        self.tri, self.bary, self.part = np.vstack(self.tri), np.vstack(self.bary), np.concatenate(self.part)
        self.offs = {name: k for k, name in enumerate(PARTS)}
        self.mov = self.part == 2
        # zawias w układzie gripper (stały, niezależny od q)
        self._pose(0.0)
        Rg = self.d.xmat[self.g].reshape(3, 3)
        self.axis = Rg.T @ (self.d.xmat[self.jaw].reshape(3, 3) @ m.jnt_axis[self.jid])
        self.anchor = (self.d.xanchor[self.jid] - self.d.xpos[self.g]) @ Rg * 1000

    def _pose(self, q):
        self.d.qpos[:] = 0
        self.d.qpos[self.m.jnt_qposadr[self.jid]] = q
        mujoco.mj_forward(self.m, self.d)

    def _mesh(self, q):
        self._pose(q)
        Rg, pg = self.d.xmat[self.g].reshape(3, 3), self.d.xpos[self.g]
        V, F = {}, {}
        for name, gi in self.geoms.items():
            mid = self.m.geom_dataid[gi]
            a, n = self.m.mesh_vertadr[mid], self.m.mesh_vertnum[mid]
            fa, fn = self.m.mesh_faceadr[mid], self.m.mesh_facenum[mid]
            v = self.m.mesh_vert[a:a + n] @ self.d.geom_xmat[gi].reshape(3, 3).T + self.d.geom_xpos[gi]
            V[name], F[name] = (v - pg) @ Rg * 1000, self.m.mesh_face[fa:fa + fn]
        return V, F

    def points(self, q):
        """(punkty [n,3] mm, normalne [n,3]) przy kącie szczęki q — z MuJoCo (wzorzec)."""
        V, _ = self._mesh(q)
        P, N = np.zeros((len(self.part), 3)), np.zeros((len(self.part), 3))
        for k, name in enumerate(PARTS):
            sel = self.part == k
            T = V[name][self.tri[sel]]                                   # [n,3 wierzch.,3]
            P[sel] = (self.bary[sel, :, None] * T).sum(1)
            c = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            N[sel] = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-12)
        return P, N

    def rot(self, phi):
        """Macierz obrotu o kąt phi wokół osi zawiasu (Rodrigues)."""
        k = self.axis / np.linalg.norm(self.axis)
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        return np.eye(3) + np.sin(phi) * K + (1 - np.cos(phi)) * K @ K


def flat_discs(P, N, part, centers, others_P):
    """Kandydaci: środki co ~3 mm; pole czynne płaskie (≥95 % koła pokryte ±0,3 mm, cos ≥ 0,95) i odsłonięte."""
    tree = cKDTree(P)
    otree = cKDTree(others_P)
    keep, members = [], []
    cell = 1.0
    gx = np.arange(-R_ACT + cell / 2, R_ACT, cell)
    GX, GY = np.meshgrid(gx, gx)
    disc_cells = np.c_[GX.ravel(), GY.ravel()][np.hypot(GX.ravel(), GY.ravel()) <= R_ACT]
    for ci in centers:
        c, n = P[ci], N[ci]
        idx = np.array(tree.query_ball_point(c, R_ACT + 0.5))
        rel = P[idx] - c
        h = rel @ n
        ok = (np.abs(h) <= PLANE_TOL) & (N[idx] @ n >= COS_TOL) & (part[idx] == part[ci])
        if ok.sum() < 20:
            continue
        u = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0]); u /= np.linalg.norm(u)
        w = np.cross(n, u)
        uv = np.c_[rel[ok] @ u, rel[ok] @ w]
        cov = (cKDTree(uv).query(disc_cells, distance_upper_bound=0.75)[0] < np.inf).mean()
        if cov < COVER:
            continue
        # odsłonięcie: nic innego 0,5–8 mm nad środkiem w promieniu 3 mm (z własnej i obcych części)
        blocked = False
        for t in np.arange(1.0, 8.01, 1.0):
            p = c + n * t
            near = tree.query_ball_point(p, 3.0)
            if near and np.any((P[near] - c) @ n > 0.5):               # tylko to, co NAD powierzchnią (cienkie ścianki!)
                blocked = True
                break
            onear = otree.query_ball_point(p, 3.0) if len(others_P) else []
            if onear and np.any((others_P[onear] - c) @ n > 0.5):
                blocked = True
                break
        if blocked:
            continue
        inside = idx[ok][np.hypot(*uv.T) <= R_ACT]
        keep.append(ci)
        members.append(inside)
    return np.array(keep), members


def downsample(P, N, sel, step=3.0):
    """Jeden punkt na komórkę 3 mm × kierunek normalnej (żeby kandydaci byli co ~3 mm na każdej ścianie)."""
    idx = np.where(sel)[0]
    key = np.c_[np.floor(P[idx] / step), np.round(N[idx] * 2)]
    _, first = np.unique(key, axis=0, return_index=True)
    return idx[first]


def hand_events(G, rng):
    """S1: kula R jedzie w kierunku d; zdarzenie = pierwszy punkt kontaktu (indeks punktu, q)."""
    ev = []
    dirs = rng.normal(size=(4000, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    dirs = dirs[(-dirs)[:, 2] <= 0.3][:400]                           # start ręki = −d; nie zza nadgarstka
    centre = np.array([5.0, 0.0, -70.0])
    for q in (0.0, 0.6, 1.2):
        P, N = G.points(q)
        sub = np.arange(len(P))[::8]                                  # ~1 pkt/mm² wystarcza do „pierwszego kontaktu”
        Ps = P[sub]
        for R in (40.0, 150.0):
            for d in dirs:
                e1 = np.cross(d, [0, 0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0, 0]); e1 /= np.linalg.norm(e1)
                e2 = np.cross(d, e1)
                for _ in range(3):
                    o = rng.uniform(-45, 45, 2)
                    c0 = centre - 400 * d + o[0] * e1 + o[1] * e2
                    r = Ps - c0
                    al = r @ d
                    pp = (r * r).sum(1) - al * al
                    hit = pp <= R * R
                    if not hit.any():
                        continue
                    t = np.where(hit, al - np.sqrt(np.maximum(R * R - pp, 0)), np.inf)
                    ev.append((sub[np.argmin(t)], q, R, sub[t <= t.min() + 2.0]))
    return ev


def grasp_events(G, rng):
    """S2 pudełka i S3 długi pręt czubkami: (rodzaj, d, okno y, okno z, W) → kontakt na obu szczękach."""
    S2 = [("S2", d, yc, h, L, W) for h in (10, 20, 30) for L in (10, 20, 30, 50) for W in (10, 20, 30)
          for d in np.arange(0, 45.1, 3.0) for yc in (-4.0, 0.0, 4.0)]
    S3 = [("S3", d, 0.0, 999.0, D, D) for D in (8, 15, 25) for d in np.arange(0, 12.1, 1.0)]
    return S2 + S3


class Contacts:
    """Liczy dla zdarzenia chwytu: maks. wystawanie szczęki stałej w śladzie, kąt zetknięcia szczęki ruchomej, kontakt dłoni."""
    def __init__(self, G):
        self.G = G
        self.P0, self.N0 = G.points(0.0)
        self.ztip = self.P0[G.part == 1, 2].min()
        fixed = ~G.mov
        self.fx = np.where(fixed & (self.N0[:, 0] > 0.3) & (self.P0[:, 0] < 5.0))[0]   # ściany +x W SZCZELINIE (poprawka r1b: bez zewn. ściany serwa x≈30)
        self.palm = np.where(fixed & (self.N0[:, 2] < -0.7))[0]       # ściany zwrócone ku czubkom (−z) — „dłoń” i schodki
        self.mv = np.where(G.mov)[0]
        self.qgrid = np.arange(G.qhi, G.qlo - 1e-9, -0.004)            # zamykanie: od otwartej do zamkniętej
        # położenia szczęki ruchomej na siatce q (wzór obrotu sprawdzony w --check)
        v0 = self.P0[self.mv] - G.anchor
        self.Rs = np.stack([G.rot(q) for q in self.qgrid])            # obrót z q=0 do q
        self.mvP = (np.einsum("qij,nj->qni", self.Rs, v0) + G.anchor).astype(np.float32)   # [nq, n, 3] ~0,5 GB
        self.mvNX = np.einsum("qj,nj->qn", self.Rs[:, 0, :], self.N0[self.mv]).astype(np.float32)

    def event(self, e):
        kind, d, yc, h, L, W = e
        z0 = self.ztip + d
        z1 = z0 + L
        y0, y1 = yc - h / 2, yc + h / 2
        P = self.P0
        def wall(z1_):
            f_ = self.fx[(P[self.fx, 1] >= y0) & (P[self.fx, 1] <= y1) & (P[self.fx, 2] >= z0) & (P[self.fx, 2] <= z1_)]
            return f_, (P[f_, 0].max() if len(f_) else None)
        f, M = wall(z1)
        if M is None:
            return None
        # poprawka r1b: przedmiot (x∈[M, M+W]) nie wchodzi głębiej niż dłoń (ściany −z przy z > −50), potem ściana jeszcze raz
        pw = self.palm[(P[self.palm, 0] >= M) & (P[self.palm, 0] <= M + W) & (P[self.palm, 1] >= y0) & (P[self.palm, 1] <= y1)
                       & (P[self.palm, 2] >= max(z0, -50.0))]   # tylko dłoń (z≈−36), nie czoło czubka (z≈−104)
        if len(pw) and P[pw, 2].min() < z1:
            z1 = P[pw, 2].min()
            f, M = wall(z1)
            if M is None:
                return None
        x1 = M + W
        # dłoń: jeśli przedmiot sięga do ścian zwróconych ku czubkom w oknie x∈[M, x1]
        pl = self.palm[(P[self.palm, 0] >= M) & (P[self.palm, 0] <= x1) & (P[self.palm, 1] >= y0) & (P[self.palm, 1] <= y1)
                       & (P[self.palm, 2] >= max(z0, -50.0)) & (P[self.palm, 2] <= z1 + TOUCH_TOL)]
        Zp = P[pl, 2].min() if len(pl) else None
        # szczęka ruchoma: pierwszy q (od otwartej), przy którym punkt w śladzie dotyka płaszczyzny x1
        X, Y, Z, NX = self.mvP[..., 0], self.mvP[..., 1], self.mvP[..., 2], self.mvNX
        win = (Y >= y0) & (Y <= y1) & (Z >= z0) & (Z <= z1) & (NX < -0.3)
        touch = win & (X <= x1)
        qi = np.argmax(touch.any(1))
        if not touch[qi].any():
            return None                                                # za szeroki / nie sięga
        return dict(M=M, x1=x1, y=(y0, y1), z=(z0, z1), Zp=Zp, qi=qi, W=W, kind=kind, d=d)


def detect_grasp(C, ev, cand, members, t):
    """Czy pole czynne (podniesione o t) jest wśród najbardziej wystających punktów śladu — dla każdego kandydata."""
    G, P = C.G, C.P0
    det = np.zeros(len(cand), bool)
    for j, (ci, mem) in enumerate(zip(cand, members)):
        n = C.N0[ci]
        if G.mov[ci]:
            loc = np.searchsorted(C.mv, mem)                           # indeksy w tablicy szczęki ruchomej
            q = ev["qi"]
            Pq, nq = C.mvP[q, loc], C.Rs[q] @ n
            w = (Pq[:, 1] >= ev["y"][0]) & (Pq[:, 1] <= ev["y"][1]) & (Pq[:, 2] >= ev["z"][0]) & (Pq[:, 2] <= ev["z"][1])
            if nq[0] < -0.3 and w.any() and (Pq[w, 0] + t * nq[0]).min() <= ev["x1"] + TOUCH_TOL:
                det[j] = True
        else:
            Pm = P[mem]
            w = (Pm[:, 1] >= ev["y"][0]) & (Pm[:, 1] <= ev["y"][1]) & (Pm[:, 2] >= ev["z"][0]) & (Pm[:, 2] <= ev["z"][1])
            if not w.any():
                continue
            if n[0] > 0.3 and (Pm[w, 0] + t * n[0]).max() >= ev["M"] - TOUCH_TOL:
                det[j] = True
            elif n[2] < -0.7 and ev["Zp"] is not None:
                xw = (Pm[:, 0] >= ev["M"]) & (Pm[:, 0] <= ev["x1"]) & w
                if xw.any() and (Pm[xw, 2] + t * n[2]).min() <= ev["Zp"] + TOUCH_TOL:
                    det[j] = True
    return det


def detect_hand2(G, hev, cand, Pq_by_q, Nq_by_q):
    """EKSPLORACYJNE (spoza celu r1): dłoń miękka — wykryte, gdy któryś punkt dotknięty przy 2 mm wgniecenia leży w polu czynnym."""
    det = np.zeros((len(cand), len(hev)), bool)
    for q in Pq_by_q:
        P, N = Pq_by_q[q], Nq_by_q[q]
        ks = [k for k, e in enumerate(hev) if e[1] == q]
        ev_id = np.concatenate([np.full(len(hev[k][3]), k) for k in ks])
        hp = np.concatenate([hev[k][3] for k in ks])
        for j, ci in enumerate(cand):
            c, n = P[ci], N[ci]
            rel = P[hp] - c
            h = rel @ n
            inpl = np.sqrt(np.maximum((rel * rel).sum(1) - h * h, 0))
            ok = (inpl <= R_ACT) & (np.abs(h) <= 1.0) & (N[hp] @ n >= 0.9) & (G.part[hp] == G.part[ci])
            det[j, np.unique(ev_id[ok])] = True
    return det


def detect_hand(G, hev, cand, Pq_by_q, Nq_by_q):
    det = np.zeros((len(cand), len(hev)), bool)
    for q in Pq_by_q:
        P, N = Pq_by_q[q], Nq_by_q[q]
        ks = [k for k, e in enumerate(hev) if e[1] == q]
        hp = np.array([hev[k][0] for k in ks])
        for j, ci in enumerate(cand):
            c, n = P[ci], N[ci]
            rel = P[hp] - c
            h = rel @ n
            inpl = np.sqrt(np.maximum((rel * rel).sum(1) - h * h, 0))
            ok = (inpl <= R_ACT) & (np.abs(h) <= 1.0) & (N[hp] @ n >= 0.9) & (G.part[hp] == G.part[ci])
            det[j, np.array(ks)[ok]] = True
    return det


def where_acc(a, b, deep):
    """Trafność czubek/nasada z samego wzoru (A, B, AB) — najlepsza tablica; tylko zdarzenia wykryte."""
    pat = a.astype(int) + 2 * b.astype(int)
    s = pat > 0
    if not s.any():
        return 0.0, 0
    tot = 0
    for p in (1, 2, 3):
        k = pat[s] == p
        tot += max((deep[s][k]).sum(), (~deep[s][k]).sum())
    return tot / s.sum(), int(s.sum())


def main(check=False):
    t0 = time.time()
    G = Gripper()
    print(f"punkty powierzchni: {len(G.part)} (gęstość {DENS}/mm²), zawias {np.round(G.anchor, 1)} oś {np.round(G.axis, 3)}", flush=True)
    # --- sprawdzian wzoru obrotu szczęki: Rodrigues vs MuJoCo
    P0, _ = G.points(0.0)
    for q in (G.qlo, 0.6, 1.2, G.qhi):
        Pq, _ = G.points(q)
        pred = (P0[G.mov] - G.anchor) @ G.rot(q).T + G.anchor
        err = np.abs(pred - Pq[G.mov]).max()
        assert err < 1e-6 * 1000, f"wzór obrotu szczęki zły przy q={q}: {err} mm"
    print("wzór obrotu szczęki = MuJoCo (błąd < 0,001 mm)", flush=True)
    C = Contacts(G)
    print(f"czubek szczęki stałej z = {C.ztip:.1f} mm", flush=True)
    # --- kandydaci
    sel = np.ones(len(G.part), bool)
    centers = downsample(P0, G.points(0.0)[1], sel)
    N0 = C.N0
    Popen, _ = G.points(0.6)
    cand_f, mem_f = flat_discs(P0[~G.mov], N0[~G.mov], G.part[~G.mov], np.searchsorted(np.where(~G.mov)[0], centers[~G.mov[centers]]), Popen[G.mov])
    fixed_idx = np.where(~G.mov)[0]
    cand_f, mem_f = fixed_idx[cand_f], [fixed_idx[m] for m in mem_f]
    mov_idx = np.where(G.mov)[0]
    cand_m, mem_m = flat_discs(Popen[G.mov], G.points(0.6)[1][G.mov], G.part[G.mov], np.searchsorted(mov_idx, centers[G.mov[centers]]), Popen[~G.mov])
    cand_m, mem_m = mov_idx[cand_m], [mov_idx[m] for m in mem_m]
    cand, members = np.r_[cand_f, cand_m], mem_f + mem_m
    print(f"kandydaci (płaskie, odsłonięte Ø12,7): {len(cand)} = nieruchome {len(cand_f)} + ruchoma {len(cand_m)}  [{time.time() - t0:.0f} s]", flush=True)
    # obecne układy: najbliższy ważny kandydat do miejsc z README / gripper_mm.json (q = 0,6 przy eksporcie)
    js = json.load(open(os.path.join(ROOT, "hardware/gripper_sensors/gripper_mm.json")))["_sensors"]
    fsr1 = np.array(js["FSR1_A0_szczeka_stala"][0])
    fsr2_open = np.array(js["FSR2_A1_szczeka_ruchoma"][0])
    fsr2 = (fsr2_open - G.anchor) @ G.rot(-0.6).T + G.anchor            # do pozy q = 0 (kandydaci w P0)
    palm_sel = [j for j, ci in enumerate(cand) if not G.mov[ci] and N0[ci, 2] < -0.7 and P0[ci, 2] < -30]
    def near(p, js_):
        dd = [np.linalg.norm(P0[cand[j]] - p) for j in js_]
        return js_[int(np.argmin(dd))], float(min(dd))
    i1, e1 = near(fsr1, list(range(len(cand))))
    i2, e2 = near(fsr2, list(range(len(cand))))
    pc = np.array([P0[cand[j]] for j in palm_sel])
    ipalm, epalm = near(pc.mean(0), palm_sel) if palm_sel else (None, None)
    print(f"FSR1 (README) → kandydat {i1}, odległość {e1:.1f} mm; FSR2 ruchoma → {i2}, {e2:.1f} mm; dłoń (środek ścian −z) → {ipalm}", flush=True)
    if check:
        assert e1 < 3.0, "miejsce FSR1 z README nie jest ważnym płaskim miejscem — sprawdzić geometrię"
        assert abs(C.ztip - (-104.4)) < 0.5 and abs(fsr1[2] - C.ztip - 30) < 1.5, "czubek / 30 mm od czubka się nie zgadza"
        print("check OK (bez zdarzeń)")
        return G, C, cand, members
    rng = np.random.default_rng(SEED_EV)
    # --- zdarzenia
    hev = hand_events(G, rng)
    Pq = {q: G.points(q)[0] for q in (0.0, 0.6, 1.2)}
    Nq = {q: G.points(q)[1] for q in (0.0, 0.6, 1.2)}
    det1 = detect_hand(G, hev, cand, Pq, Nq)
    det1b = detect_hand2(G, hev, cand, Pq, Nq)
    print(f"S1 ręka: {len(hev)} zdarzeń  [{time.time() - t0:.0f} s]", flush=True)
    gev = [C.event(e) for e in grasp_events(G, rng)]
    gev = [e for e in gev if e is not None]
    res = {}
    for t in TS:
        dg = np.stack([detect_grasp(C, e, cand, members, t) for e in gev], 1)
        res[t] = dg
        print(f"S2+S3 przy t={t}: {len(gev)} zdarzeń  [{time.time() - t0:.0f} s]", flush=True)
    kind = np.array([e["kind"] for e in gev])
    deep = np.array([e["d"] >= 15 for e in gev])
    if check:
        return G, C, cand, members, hev, gev, det1, res
    out = dict(n_points=int(len(G.part)), n_cand=int(len(cand)), n_S1=len(hev), n_S2=int((kind == "S2").sum()), n_S3=int((kind == "S3").sum()),
               cand=[dict(i=int(ci), p=P0[ci].round(2).tolist(), n=N0[ci].round(3).tolist(), part=PARTS[G.part[ci]]) for ci in cand],
               baseline=dict(fsr1=int(i1), fsr1_err=e1, fsr2=int(i2), fsr2_err=e2, palm=ipalm), score={})
    for t, dg in res.items():
        D1 = det1.astype(np.uint8)
        D2, D3 = dg[:, kind == "S2"].astype(np.uint8), dg[:, kind == "S3"].astype(np.uint8)
        def cov(D, a, b):
            return (np.maximum(D[a], D[b]).sum(-1) / D.shape[1])
        nc = len(cand)
        A, B = np.triu_indices(nc, 1)
        s1 = np.zeros(len(A)); s2 = np.zeros(len(A)); s3 = np.zeros(len(A))
        for k in range(0, len(A), 20000):
            a, b = A[k:k + 20000], B[k:k + 20000]
            s1[k:k + 20000] = (D1[a] | D1[b]).mean(1)
            s2[k:k + 20000] = (D2[a] | D2[b]).mean(1)
            s3[k:k + 20000] = (D3[a] | D3[b]).mean(1)
        sc = (s1 + s2 + s3) / 3
        order = np.argsort(-sc)[:10]
        def pack(a, b):
            j = np.where((A == min(a, b)) & (B == max(a, b)))[0][0]
            wa, nd = where_acc(dg[a], dg[b], deep)
            return dict(pair=[int(a), int(b)], S1=float(s1[j]), S2=float(s2[j]), S3=float(s3[j]), score=float(sc[j]), where=wa, n_det=nd)
        top = [pack(A[j], B[j]) for j in order]
        both = np.where((s1 >= 0.5) & (s3 >= 0.8))[0]
        hw2p = pack(i1, ipalm) if ipalm is not None else None
        orig = pack(i1, i2)
        # top-contact (Kim 2026): 2 kandydatów o najwięcej kontaktach łącznie; contact-cover: zachłannie
        tot = D1.sum(1) / D1.shape[1] + D2.sum(1) / D2.shape[1] + D3.sum(1) / D3.shape[1]
        tc = np.argsort(-tot)[:2]
        g1 = int(np.argmax(tot))
        allD = np.c_[D1, D2, D3].astype(bool)
        g2 = int(np.argmax((allD | allD[g1]).sum(1)))
        D1b = det1b.astype(np.uint8)
        s1b = np.zeros(len(A))
        for k in range(0, len(A), 20000):
            s1b[k:k + 20000] = (D1b[A[k:k + 20000]] | D1b[B[k:k + 20000]]).mean(1)
        scb = (s1b + s2 + s3) / 3
        ob = np.argsort(-scb)[:5]
        def packb(a, b):
            j = np.where((A == min(a, b)) & (B == max(a, b)))[0][0]
            return dict(pair=[int(a), int(b)], S1b=float(s1b[j]), S2=float(s2[j]), S3=float(s3[j]), score_b=float(scb[j]))
        out["score"][str(t)] = dict(explor_soft_hand=dict(top=[packb(A[j], B[j]) for j in ob], hw2p=packb(i1, ipalm), original=packb(i1, i2)),
                                    top=top, hw2p=hw2p, original=orig, top_contact=pack(*tc), contact_cover=pack(g1, g2),
                                    n_pairs_S1ge05_S3ge08=int(len(both)),
                                    best_S1ge05_S3ge08=pack(A[both[np.argmax(sc[both])]], B[both[np.argmax(sc[both])]]) if len(both) else None,
                                    single_best=[dict(i=int(j), S1=float(D1[j].mean()), S2=float(D2[j].mean()), S3=float(D3[j].mean()))
                                                 for j in np.argsort(-tot)[:8]])
        print(f"t={t}: najlepsza para {top[0]} | hw2p {hw2p} | pierwotny {orig}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, f"placement_{TAG}.json"), "w"), indent=1, default=float)
    np.savez_compressed(os.path.join(OUT, f"placement_{TAG}_raw.npz"), cand=cand, det1=det1, det1b=det1b, **{f"det_t{t}": v for t, v in res.items()},
                        kind=kind, deep=deep, P0=P0[cand], N0=N0[cand], hev=np.array([(e[0], e[1], e[2]) for e in hev]), gev_d=np.array([e["d"] for e in gev]), gev_W=np.array([e["W"] for e in gev]))
    print(f"zapisano {OUT}/placement_{TAG}.json  [{time.time() - t0:.0f} s]")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
