"""Etap 5 (bio2): percepcja 3D i predyktor toru rzuconej piłeczki (throw_scene.py) dla sterownika chwytu.

WARSTWA INŻYNIERSKA, nie biologiczna: to jest „oko robota” w pełnej rozdzielczości (domyślnie 320×240, ta sama kamera „eye”
na chwytaku i ten sam fovy co w scene2), a nie siatkówka muchy. Siatkówka 32×24 (retina.py) ma 768 punktów: piłeczka 5 cm
z 1,5 m daje < 1 komórki, więc ułamek milimetra wymagany przy chwycie (oś y chwytaka ~5 mm) jest poza jej zasięgiem.
Mózg muchy (looming, ucieczka, pierścień EPG) dalej działa na 32×24; ten moduł dostarcza tylko liczby: gdzie piłeczka będzie
i kiedy. Nic tu nie czyta prawdy z symulatora: wejściem jest obraz RGB, poza kamery z kinematyki (d.cam_xpos / d.cam_xmat
— robot zna swoją kinematykę, w realu: enkodery) i znane stałe (g, promień piłeczki, fovy).

Metoda (jedna klatka):
 1. Detekcja po KOLORZE, niezależna od ruchu kamery (kamera jest na chwytaku i jedzie z ramieniem, więc różnica z tłem odpada;
    nie ma tu modelu tła ani kopii eferentnej): piłeczka jest zielona (.1 .7 .2), reszta sceny (tło, stół, ramię, pady, chwytak)
    ma g − max(r, b) ≤ 0, więc maska = g − max(r, b) > c_min. Największa plamka → środek (centroid piksela maski, współrzędne
    ciągłe, subpikselowo), pole A (liczba pikseli), drugie momenty (elongacja, wypełnienie → pewność), flaga „na brzegu obrazu”.
 2. Model sfery w kamerze pinhole: sylwetka kuli o promieniu R w odległości D to elipsa; jej środek NIE jest rzutem środka
    kuli (przesunięcie rośnie z kątem od osi), a pole ≈ π s²/cos³θ. Rozwiązuję dokładnie (stożek o półkącie α, oś pod kątem θ):
    środek elipsy c = t(1 + s²)/(1 − t²s²), pole ab = sin²α cosα/(cos²θ − sin²α)^{3/2}, t = tg θ, s = tg α, D = R / sin α.
    Pole poprawiam o nadmiar promienia maski δ(c_min) (piksele brzegowe zmieszane z tłem; stała zmierzona, DELTA_TAB).
    Kierunek: n_cam z (θ, azymut obrazu), punkt świata p = cam_pos + R_cam n_cam D.
 3. Niepewność pomiaru jest anizotropowa: kierunek ± σ_c/f (piksele), odległość ± D·K_A/(2√A) (z pola).
 4. Predyktor: parabola balistyczna x(t) = p_a + v_a t + ½ g t² (znane g) dopasowywana ważoną MNK (wagi = odwrotność
    anizotropowej kowariancji każdego pomiaru) do wszystkich pomiarów od pierwszego wykrycia; odświeżana co klatkę
    (przyrostowa suma równań normalnych 6×6). Start rzutu: pierwszy wykryty pomiar (piłeczka sama się „zgłasza”); pomiar
    odstający od bieżącego toru o > GATE σ jest odrzucany, po N_RESET odrzuceniach z rzędu (albo po STALE s ciszy) tor jest
    zaczynany od nowa. Predykcja od N_MIN pomiarów; cov_p / sigma_T mówią, na ile jej ufać (wcześnie: setki mm).
 5. Punkt przechwycenia: przecięcie toru z płaszczyzną poziomą z = z_c („powierzchnia chwytu”), w opadaniu. Uzasadnienie:
    lot jest stromy (−55…−80°, v_z 3,5–5,4 m/s), więc czas przecięcia jest dobrze uwarunkowany (błąd 5 mm w z = ~1 ms);
    płaszczyzna jest stała w świecie, więc wynik nie „ucieka” w miarę jazdy ramienia (inaczej niż „punkt toru najbliższy
    paszczy”, który zależy od pozycji paszczy i oscyluje); każdy tor generatora przecina płaszczyznę z_c = 0,28 m (środek
    z_star 0,22–0,34) niedaleko swojego p* (patrz raport: odległość i osiągalność IK). Sterownik z własnym zakresem
    osiągalności może zapytać o dowolną płaszczyznę: trk.predict(z_c). T_pred jest czasem BEZWZGLĘDNYM (ta sama oś czasu co t),
    v_pred daje kierunek nalotu (orientacja chwytaka w IK). Kowariancja p uwzględnia, że punkt leży na płaszczyźnie.

API:
    trk = BallTracker(m, d, res=(320, 240), z_c=0.28)       # res = (W, H); poza kamery z d (albo jawnie w step)
    r, opt = trk.renderer()                                 # renderer „eye” w tej rozdzielczości (zamknij r.close())
    r.update_scene(d, camera="eye", scene_option=opt); rgb = r.render()
    out = trk.step(rgb, t, pose=None)    # t: chwila klatki [s]; pose=(pos[3], R[3×3]) kamery w tej chwili (domyślnie z d)
    trk.reset()
    trk.predict(z_c)                     # → dict(p, v, T, cov_p, sigma_T) dla innej płaszczyzny (albo None)
    out: seen (bool, wykrycie przyjęte w tej klatce), p_meas (3, świat; None gdy brak), conf (0…1), n (pomiary w torze),
         ready (tor dopasowany, n ≥ N_MIN), p_pred (3, świat, na z = z_c), v_pred (3), T_pred (s, bezwzględny),
         tau (T_pred − t), cov_p (3×3, świat), sigma_T (s), p_now (położenie toru w t), blob (diagnostyka detektora).
    trk.R_corr, trk.t_corr: poprawka kalibracji ręka–oko (domyślnie tożsamość/0), stosowana do pozy kamery.
Weryfikacja: `python throw_percept.py test` (szybki test), `python throw_percept.py` (pełna ewaluacja → results/stage5_percept.txt/png).
"""
import os
import sys
import time

import mujoco
import numpy as np
from scipy import ndimage as ndi

import scene2
import throw_scene as ts

HERE = os.path.dirname(os.path.abspath(__file__))
G = ts.G
R_BALL = ts.R_BALL

# --- detekcja ---
C_MIN = 2             # g − max(r, b) > C_MIN (0…255): piłeczka 14…150 w rdzeniu, reszta sceny ≤ 0 (pomiar na kilkuset tys. pikseli).
                      # Niski próg, bo wyższy ucina ciemny (nieoświetlony) brzeg kuli: przesunięcie środka w obrazie dv = −0,05 px przy 2,
                      # −0,10 przy 4, −0,26 przy 12, −0,33 przy 20 (mierzone, 678 klatek); render bez szumu. Przy szumie obrazu podnieś c_min.
# nadmiar promienia maski δ [px] (piksele krawędziowe zmieszane z tłem) w funkcji c_min — pomiar j.w. (A_kor = π(√(A/π) − δ)²)
DELTA_TAB = ((1, 2, 4, 8, 12, 16, 20, 30), (0.287, 0.276, 0.233, 0.141, 0.066, -0.013, -0.114, -0.380))
A_MIN = 6             # min. pole plamki [px]
CONF_MIN = 0.2
# --- model niepewności pomiaru (σ_c w pikselach, σ_A/A = K_A/√A) ---
SIG_C = 0.2           # dobrane na seedach 100–149 (przegląd σ_c ∈ {0,1; 0,2}, K_A ∈ {0,25…2}); render bez szumu daje ~0,07 px, ale pole/środek mają
K_A = 0.5             # błędy systematyczne zależne od geometrii (cieniowanie), których dopasowanie nie uśrednia — stąd σ większe niż jitter
SIG_FLOOR = 2e-3      # m, minimalna σ pomiaru
# --- tor ---
N_MIN = 5             # min. liczba pomiarów, by podać predykcję
GATE = 6.0            # odrzucenie pomiaru: |reszta| > GATE σ (kierunek i odległość osobno)
N_RESET = 8           # tyle odrzuceń z rzędu → nowy tor
STALE = 0.5           # s bez przyjętego pomiaru → nowy tor (nowy rzut)
Z_C = 0.28            # płaszczyzna przechwycenia [m] (środek z_star 0,22–0,34)


# --------------------------------------------------------------------------------------------- kamera / model sfery
class Cam:
    """Pinhole z fovy (pionowy) i rozdzielczości; piksel (i, j) ma środek w (j + 0,5, i + 0,5) we współrzędnych ciągłych."""

    def __init__(self, W, H, fovy=scene2.CAM_FOVY):
        self.W, self.H = W, H
        self.f = (H / 2) / np.tan(np.radians(fovy) / 2)


def delta_r(c_min):
    return float(np.interp(c_min, *DELTA_TAB))


def _sphere_inverse(c, ab):
    """(c = |środek elipsy|/f, ab = pole/(π f²)) → (t = tg θ, sin α). Wzory z docstringu, iteracja stałopunktowa."""
    t = c
    sa2 = ab * (1 + t * t) ** 1.5
    for _ in range(6):
        ca = np.sqrt(max(1 - sa2, 1e-9))
        ct2 = 1 / (1 + t * t)
        sa2 = ab * max(ct2 - sa2, 1e-6) ** 1.5 / ca
        sa2 = min(sa2, 0.5 * ct2)
        s2 = sa2 / (1 - sa2)
        t = max(c * (1 - t * t * s2) / (1 + s2), 0.0)
    return t, np.sqrt(sa2)


def blob_to_ray(cam, u, v, A, delta=0.0, sig_c=SIG_C, k_a=K_A):
    """Plamka (środek u, v [px], pole A [px]) → (n_cam, D, σ_ang, σ_D): jednostkowy kierunek do środka kuli w układzie kamery
    MuJoCo (x w prawo, y w górę, patrzy wzdłuż −z), odległość środka D [m] i niepewności (kierunek [rad], odległość [m])."""
    A = np.pi * max(np.sqrt(A / np.pi) - delta, 0.5) ** 2
    x, y = (u - cam.W / 2) / cam.f, (cam.H / 2 - v) / cam.f
    c = np.hypot(x, y)
    t, sa = _sphere_inverse(c, A / (np.pi * cam.f ** 2))
    th = np.arctan(t)
    az = (x / c, y / c) if c > 1e-9 else (1.0, 0.0)
    n = np.array([np.sin(th) * az[0], np.sin(th) * az[1], -np.cos(th)])
    D = R_BALL / sa
    return n, D, sig_c / cam.f * (1 + t * t), D * k_a / (2 * np.sqrt(A))


def project(cam, cam_pos, cam_R, p, r=R_BALL):
    """Prawda do EWALUACJI (tracker jej nie używa): rzut kuli (środek p, promień r) → (u, v, A, D). A = π a b dokładne (wzór stożka)."""
    pc = cam_R.T @ (np.asarray(p) - cam_pos)
    D = np.linalg.norm(pc)
    if pc[2] >= 0:
        return np.nan, np.nan, np.nan, D
    x, y = pc[0] / -pc[2], pc[1] / -pc[2]
    sa = r / D
    ct2 = (pc[2] / D) ** 2
    ab = sa ** 2 * np.sqrt(1 - sa ** 2) / max(ct2 - sa ** 2, 1e-9) ** 1.5
    t = np.hypot(x, y)
    s2 = sa ** 2 / (1 - sa ** 2)
    k = (1 + s2) / (1 - t * t * s2)
    return cam.W / 2 + cam.f * x * k, cam.H / 2 - cam.f * y * k, np.pi * ab * cam.f ** 2, D


# --------------------------------------------------------------------------------------------- detekcja
def detect(rgb, c_min=C_MIN, a_min=A_MIN, f=None):
    """Plamka piłeczki w obrazie RGB (uint8 [H, W, 3]) — po kolorze, bez prawdy z symulatora.
    Zwraca dict(u, v, A, conf, border, el, fill, n_blobs) albo None. u, v: środek maski [px, ciągły]. f: ogniskowa [px] (do oczekiwanej
    elongacji elipsy 1/cos θ; domyślnie fovy z scene2)."""
    H, W = rgb.shape[:2]
    if f is None:
        f = (H / 2) / np.tan(np.radians(scene2.CAM_FOVY) / 2)
    x = rgb.astype(np.int16)
    c = x[..., 1] - np.maximum(x[..., 0], x[..., 2])
    lab, n = ndi.label(c > c_min)
    if n == 0:
        return None
    area = np.bincount(lab.ravel(), minlength=n + 1)[1:]
    order = [i for i in np.argsort(-area) if area[i] >= a_min][:4]
    if not order:
        return None
    objs = ndi.find_objects(lab)
    best = None
    for i in order:
        sl = objs[i]
        ys, xs = np.nonzero(lab[sl] == i + 1)
        ys = ys + sl[0].start
        xs = xs + sl[1].start
        A = float(len(ys))
        u, v = xs.mean() + 0.5, ys.mean() + 0.5
        lam = np.maximum(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]), bias=True) + np.eye(2) / 12.0), 1e-9)   # + wariancja piksela
        el = float(np.sqrt(lam[1] / lam[0]))
        fill = float(A / (4 * np.pi * np.sqrt(lam[0] * lam[1])))          # π a b = 4π √(λ1 λ2); wypełniona elipsa → ~1
        border = bool(sl[0].start == 0 or sl[1].start == 0 or sl[0].stop == H or sl[1].stop == W)
        el_exp = np.sqrt(1 + (np.hypot(u - W / 2, v - H / 2) / f) ** 2)  # elongacja sylwetki kuli poza osią ~ 1/cos θ
        tol = 0.15 + 1.5 / np.sqrt(A)
        conf = float(np.exp(-0.5 * ((fill - 1) / (0.1 + 1.0 / np.sqrt(A))) ** 2) * np.exp(-0.5 * ((el - el_exp) / (el_exp * tol)) ** 2))
        if border:                                                         # przycięta przez brzeg obrazu: środek i pole obciążone
            conf = 0.0
        cand = dict(u=u, v=v, A=A, conf=conf, border=border, el=el, fill=fill, n_blobs=int(n), lab=i + 1, sl=sl)
        if best is None or conf * A > best["conf"] * best["A"]:
            best = cand
    best.pop("sl"), best.pop("lab")
    return best


# --------------------------------------------------------------------------------------------- tracker
class BallTracker:
    def __init__(self, m, d, res=(320, 240), z_c=Z_C, c_min=C_MIN, sig_c=SIG_C, k_a=K_A, gate=GATE, conf_min=CONF_MIN, n_min=N_MIN):
        self.m, self.d, self.res = m, d, res
        self.cid = m.camera("eye").id
        self.cam = Cam(*res, fovy=float(m.cam_fovy[self.cid]))
        self.z_c, self.c_min, self.sig_c, self.k_a = z_c, c_min, sig_c, k_a
        self.gate, self.conf_min, self.n_min = gate, conf_min, n_min
        self.delta = delta_r(c_min)
        self.g = np.array([0.0, 0.0, -G])
        self.R_corr, self.t_corr = np.eye(3), np.zeros(3)        # poprawka ręka–oko (w układzie kamery)
        self.reset()

    def renderer(self):
        """Renderer kamery „eye” jak scene2.eye_renderer (bez cieni/odbić/nieba), ale w rozdzielczości trackera."""
        r = mujoco.Renderer(self.m, self.res[1], self.res[0])
        for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
            r.scene.flags[f] = False
        opt = mujoco.MjvOption()
        opt.sitegroup[:] = 0
        return r, opt

    def reset(self):
        self.t0 = self.t_last = None
        self.AtA = np.zeros((6, 6))
        self.Atb = np.zeros(6)
        self.n = self.miss = 0
        self.theta = self.cov_theta = None     # (p_a, v_a) w t0 i jego kowariancja

    # ---- geometria toru
    def _x(self, t):
        s = t - self.t0
        return self.theta[:3] + self.theta[3:] * s + 0.5 * self.g * s * s

    def _v(self, t):
        return self.theta[3:] + self.g * (t - self.t0)

    def _H(self, s):
        return np.hstack([np.eye(3), s * np.eye(3)])

    def _solve(self):
        if self.n < self.n_min:
            self.theta = self.cov_theta = None
            return
        self.cov_theta = np.linalg.inv(self.AtA + 1e-9 * np.eye(6))
        self.theta = self.cov_theta @ self.Atb

    def predict(self, z_c):
        """Przecięcie toru z płaszczyzną z = z_c w opadaniu: dict(p, v, T, cov_p, sigma_T) albo None (brak toru / tor nie sięga z_c)."""
        if self.theta is None:
            return None
        za, vz = self.theta[2], self.theta[5]
        disc = vz * vz - 2 * G * (z_c - za)           # z(s) = za + vz s − ½ G s² = z_c
        if disc < 0:
            return None
        T = self.t0 + (vz + np.sqrt(disc)) / G        # późniejszy pierwiastek (opadanie)
        Hh = self._H(T - self.t0)
        v = self._v(T)
        M = np.eye(3) - np.outer(v, [0, 0, 1]) / v[2]    # punkt leży na płaszczyźnie: δp = (I − v e_zᵀ/v_z) H δθ
        C = Hh @ self.cov_theta @ Hh.T
        return dict(p=self._x(T), v=v, T=T, cov_p=M @ C @ M.T, sigma_T=float(np.sqrt(max(C[2, 2], 0)) / abs(v[2])))

    def _sig_pred(self, t, n_w):
        """σ toru w chwili t: prostopadle do promienia (na 1 oś) i wzdłuż promienia."""
        Hh = self._H(t - self.t0)
        C = Hh @ self.cov_theta @ Hh.T
        P = np.eye(3) - np.outer(n_w, n_w)
        return float(np.sqrt(max(np.trace(P @ C @ P) / 2, 0))), float(np.sqrt(max(n_w @ C @ n_w, 0)))

    # ---- krok
    def step(self, rgb, t, pose=None):
        if self.t_last is not None and t - self.t_last > STALE:
            self.reset()
        out = dict(seen=False, p_meas=None, conf=0.0, n=self.n, ready=False, p_pred=None, v_pred=None, T_pred=None, tau=None,
                   cov_p=None, sigma_T=None, p_now=None, blob=None)
        det = detect(rgb, self.c_min, f=self.cam.f)
        out["blob"] = det
        if det is not None and det["conf"] >= self.conf_min:
            cam_pos, cam_R = (self.d.cam_xpos[self.cid], self.d.cam_xmat[self.cid].reshape(3, 3)) if pose is None else pose
            cam_pos = cam_pos + cam_R @ self.t_corr
            cam_R = cam_R @ self.R_corr
            n_c, D, sa, sD = blob_to_ray(self.cam, det["u"], det["v"], det["A"], self.delta, self.sig_c, self.k_a)
            sD = max(sD, SIG_FLOOR)
            sa = max(sa, SIG_FLOOR / D)
            n_w = cam_R @ n_c
            p = cam_pos + n_w * D
            ok = True
            if self.theta is not None:                 # bramka: reszta względem bieżącego toru, prostopadle i wzdłuż promienia
                e = p - self._x(t)
                el = e @ n_w
                sp, sl = self._sig_pred(t, n_w)
                ok = (np.linalg.norm(e - el * n_w) < self.gate * np.hypot(sa * D, sp)) and (abs(el) < self.gate * np.hypot(sD, sl))
            if ok:
                self.miss = 0
                self.t_last = t
                if self.t0 is None:
                    self.t0 = t
                s = t - self.t0
                P = np.outer(n_w, n_w)
                W = (np.eye(3) - P) / (sa * D) ** 2 + P / sD ** 2
                Phi = self._H(s)
                self.AtA += Phi.T @ W @ Phi
                self.Atb += Phi.T @ W @ (p - 0.5 * self.g * s * s)
                self.n += 1
                self._solve()
                out.update(seen=True, p_meas=p, conf=det["conf"])
            else:
                self.miss += 1
                if self.miss >= N_RESET:
                    self.reset()
        out["n"] = self.n
        if self.theta is not None:
            out.update(ready=True, p_now=self._x(t))
            pr = self.predict(self.z_c)
            if pr is not None:
                out.update(p_pred=pr["p"], v_pred=pr["v"], T_pred=pr["T"], tau=pr["T"] - t, cov_p=pr["cov_p"], sigma_T=pr["sigma_T"])
        return out


# --------------------------------------------------------------------------------------------- ewaluacja
TAUS = (0.6, 0.4, 0.3, 0.2, 0.1, 0.05)
CROSS_Z = 0.28


def true_crossing(thr, z_c):
    """Prawda (tylko ewaluacja): punkt i czas przecięcia płaszczyzny z = z_c przez tor dyskretny (ts.ball_pos), gałąź opadająca."""
    p0, v0 = thr["p0"], thr["v0"]
    dt = ts.DT
    # z(t) = z0 + vz (t − dt) − ½ G t (t − dt) = z_c  → ½ G t² − (G dt/2·… ) rozwiązuję numerycznie z pierwiastków wielomianu
    a = -0.5 * G
    b = v0[2] + 0.5 * G * dt
    c = p0[2] - v0[2] * dt - z_c
    roots = np.roots([a, b, c])
    T = float(np.max(roots.real))
    return ts.ball_pos(thr, T), T


def _final_frame(m, d2, q_star):
    """Obrót chwytaka w pozie q* — układ, w którym wyrocznia wymaga ~5 mm w y (tylko do ewaluacji)."""
    mujoco.mj_resetData(m, d2)
    d2.qpos[:5] = q_star
    mujoco.mj_kinematics(m, d2)
    return d2.xmat[m.body("gripper").id].reshape(3, 3).copy()


def run_throw(m, d, trk, thr, q_rest, mode, rend, step_ms=10, noise=0.0, lag_ms=0, rng=None):
    """Jeden rzut, klatki co step_ms do T − 10 ms. mode 'a': ramię nieruchome w q_rest, piłeczka ustawiana kinematycznie (tor
    dyskretny integratora); mode 'b': fizyka jak w oracle_trial (do D = 0,25 s ramię stoi, potem każdy staw jedzie do q* z prędkością
    serwa; piłeczka swobodna). noise: σ szumu obrazu [poziomy szarości]; lag_ms: poza kamery spóźniona o tyle ms względem obrazu.
    Zwraca listę rekordów na klatkę (t, tau = T − t, wyjście trackera, prawda do porównań)."""
    r, opt = rend
    T = thr["T"]
    ts.reset_throw(m, d, thr, q_rest)
    trk.reset()
    cam = trk.cam
    dt = m.opt.timestep
    qs = thr["q_star"]
    step = ts.SERVO_SPEED * dt
    ball = m.body("ball").id
    hist, rec = [], []
    n = int(round(T * 1000))
    for k in range(n + 1):
        t = d.time if mode == "b" else k * dt
        if mode == "a" and k % step_ms == 0:
            ts.place_ball(m, d, ts.ball_pos(thr, t), ts.ball_vel(thr, t))
            mujoco.mj_forward(m, d)
        hist.append((d.cam_xpos[trk.cid].copy(), d.cam_xmat[trk.cid].reshape(3, 3).copy()))
        if k % step_ms == 0 and t <= T - 0.01 + 1e-9:
            t0 = time.perf_counter()
            r.update_scene(d, camera="eye", scene_option=opt)
            rgb = r.render()
            t_rend = time.perf_counter() - t0
            if noise > 0:
                rgb = np.clip(rgb + rng.normal(0, noise, rgb.shape), 0, 255).astype(np.uint8)
            t0 = time.perf_counter()
            o = trk.step(rgb, t, pose=hist[max(k - lag_ms, 0)])
            o["cpu_ms"] = 1000 * (time.perf_counter() - t0)
            o["render_ms"] = 1000 * t_rend
            pb = d.xpos[ball].copy() if mode == "b" else ts.ball_pos(thr, t)
            u, v, A, D = project(cam, *hist[k], pb)
            rec.append(dict(t=t, tau=T - t, out=o, pb=pb, u=u, v=v, A=A, D=D))
        if mode == "b":
            if t >= ts.D_PERCEPT:
                d.ctrl[:5] += np.clip(qs - d.ctrl[:5], -step, step)
            d.ctrl[5] = np.clip(3.0 * (ts.Q_OPEN - d.qpos[5]) - 0.3 * d.qvel[5], -1, 1)
            mujoco.mj_step(m, d)
    return rec


def evaluate(seeds, mode, res=(320, 240), z_rule="p_star", rest=None, trk_kw=None, thr_cache=None, noise=0.0, lag_ms=0, hand_eye=None):
    """Przebieg trackera po rzutach `seeds`. z_rule 'p_star': płaszczyzna z_c = z prawdziwego p* (porównanie 1:1 z wymaganiami
    wyroczni); liczba: stała płaszczyzna (np. 0,28), prawda = przecięcie prawdziwego toru z tą płaszczyzną. hand_eye = (stopnie, mm):
    błąd kalibracji ręka–oko (losowa oś/kierunek na rzut). Zwraca listę dict(thr, R, p_ref, T_ref, rec)."""
    m, d = ts.load()
    d2 = mujoco.MjData(m)
    q_rest = ts.rest_pose(m, d) if rest is None else rest
    trk = BallTracker(m, d, res=res, **(trk_kw or {}))
    rend = trk.renderer()
    out = []
    for s in seeds:
        thr = ts.make_throw(s, m, d) if thr_cache is None else thr_cache[s]
        rng = np.random.default_rng(1000 + s)
        if hand_eye is not None:
            ax = rng.normal(size=3)
            ax *= np.radians(hand_eye[0]) / np.linalg.norm(ax)
            trk.R_corr = _rotvec(ax)
            tv = rng.normal(size=3)
            trk.t_corr = tv / np.linalg.norm(tv) * hand_eye[1] * 1e-3
        if z_rule == "p_star":
            trk.z_c, p_ref, T_ref = thr["p_star"][2], thr["p_star"], thr["T"]
        else:
            trk.z_c = z_rule
            p_ref, T_ref = true_crossing(thr, z_rule)
        rec = run_throw(m, d, trk, thr, q_rest, mode, rend, noise=noise, lag_ms=lag_ms, rng=rng)
        out.append(dict(thr=thr, R=_final_frame(m, d2, thr["q_star"]), p_ref=p_ref, T_ref=T_ref, rec=rec, res=res))
    rend[0].close()
    return out


def _rotvec(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def frame_at(rec, tau):
    """Rekord klatki najbliższy τ = T − t (|Δ| ≤ 5 ms) albo None."""
    if not rec:
        return None
    k = int(np.argmin([abs(r["tau"] - tau) for r in rec]))
    return rec[k] if abs(rec[k]["tau"] - tau) <= 0.005 + 1e-9 else None


def errors(res_l, tau):
    """Błędy przewidywanego p* (3 składowe w układzie chwytaka w q*, mm) i T_pred (ms) w chwili T − t = tau, tylko tory z predykcją.
    Zwraca (e [n, 3], eT [n], liczba rzutów mających klatkę w tej chwili, σ trackera w układzie chwytaka [n, 3] mm, indeksy rzutów)."""
    E, ET, S, idx, nthr = [], [], [], [], 0
    for i, r in enumerate(res_l):
        f = frame_at(r["rec"], tau)
        if f is None:
            continue
        nthr += 1
        o = f["out"]
        if o["p_pred"] is None:
            continue
        E.append(1000 * (r["R"].T @ (o["p_pred"] - r["p_ref"])))
        ET.append(1000 * (o["T_pred"] - r["T_ref"]))
        S.append(1000 * np.sqrt(np.diag(r["R"].T @ o["cov_p"] @ r["R"])))
        idx.append(i)
    return np.array(E).reshape(-1, 3), np.array(ET), nthr, np.array(S).reshape(-1, 3), idx


def table(res_l, label):
    """Tabela błędów vs czas do T. Zwraca listę linii."""
    L = [label,
         "T−t [s] | gotowe/rzuty | |e_x| med / p90 [mm] | |e_y| med / p90 [mm] | e_y<5 mm | e_y<10 mm | |e_z| med / p90 [mm] | "
         "|ΔT| med / p90 [ms] | med σ_y trackera [mm]"]
    for tau in TAUS:
        E, ET, nthr, S, _ = errors(res_l, tau)
        if len(E) == 0:
            L.append(f"{tau:5.2f}    | 0/{nthr}")
            continue
        a, pc = np.abs(E), np.percentile
        L.append(f"{tau:5.2f}    | {len(E):3d}/{nthr:3d}     | {pc(a[:, 0], 50):6.1f} / {pc(a[:, 0], 90):6.1f}    | "
                 f"{pc(a[:, 1], 50):6.1f} / {pc(a[:, 1], 90):6.1f}    | {100 * (a[:, 1] < 5).mean():4.0f} %   | {100 * (a[:, 1] < 10).mean():4.0f} %    | "
                 f"{pc(a[:, 2], 50):6.1f} / {pc(a[:, 2], 90):6.1f}    | {pc(np.abs(ET), 50):6.1f} / {pc(np.abs(ET), 90):6.1f}  | "
                 f"{np.median(S[:, 1]):7.1f}")
    return L


def short_row(res_l, label, taus=(0.4, 0.3, 0.2, 0.1)):
    """Jedna linia: |e_y| med/p90 [mm] i odsetek < 5 mm dla kilku τ (do porównań wariantów)."""
    s = f"{label:46s}"
    for tau in taus:
        E, _, nthr, _, _ = errors(res_l, tau)
        if len(E) == 0:
            s += f" | τ={tau}: brak"
            continue
        a = np.abs(E[:, 1])
        s += f" | τ={tau}: {np.median(a):4.1f}/{np.percentile(a, 90):5.1f} ({100 * (a < 5).mean():3.0f}%, {len(E)}/{nthr})"
    return s


def detection_stats(res_l):
    """Odsetek klatek z przyjętym wykryciem (wśród klatek, w których piłeczka ma wg prawdy ≥ A_MIN px w polu widzenia), powody braków,
    fałszywe wykrycia (przyjęta plamka daleko > 3 px od rzutu piłeczki albo piłeczki nie ma w obrazie), błąd środka i promienia."""
    n_vis = n_seen = n_false = n_acc = 0
    why = dict(brzeg=0, brak_plamki=0, odrzucona=0)
    err_uv, err_r = [], []
    for r in res_l:
        W, H = r["res"]
        d_ = delta_r(C_MIN)
        for f in r["rec"]:
            o = f["out"]
            vis = np.isfinite(f["u"]) and 0 <= f["u"] < W and 0 <= f["v"] < H and f["A"] >= A_MIN
            n_vis += vis
            b = o["blob"]
            if o["seen"]:
                n_acc += 1
                if not vis or np.hypot(b["u"] - f["u"], b["v"] - f["v"]) > 3.0:
                    n_false += 1
                else:
                    n_seen += 1
                    err_uv.append(np.hypot(b["u"] - f["u"], b["v"] - f["v"]))
                    err_r.append(np.sqrt(b["A"] / np.pi) - d_ - np.sqrt(f["A"] / np.pi))
            elif vis:
                why["brzeg" if (b is not None and b["border"]) else "brak_plamki" if b is None else "odrzucona"] += 1
    return dict(n_frames=sum(len(r["rec"]) for r in res_l), n_vis=int(n_vis), n_seen=n_seen, n_acc=n_acc, n_false=n_false,
                why=why, err_uv=np.array(err_uv), err_r=np.array(err_r))


def false_alarm_test(n=3000, res=(320, 240), seed=0):
    """Fałszywe wykrycia bez piłeczki: kamera w losowych pozach ramienia (cały zakres stawów + szczęka), piłeczka zdjęta ze sceny."""
    m, d = ts.load()
    trk = BallTracker(m, d, res=res)
    r, opt = trk.renderer()
    ids = ts._ids(m)
    rng = np.random.default_rng(seed)
    hits = []
    for _ in range(n):
        d.qpos[:5] = rng.uniform(ids["lo"], ids["hi"])
        d.qpos[5] = rng.uniform(0.0, 1.2)
        ts.place_ball(m, d, (0.0, 0.0, 60.0), (0, 0, 0))
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera="eye", scene_option=opt)
        b = detect(r.render(), trk.c_min, f=trk.cam.f)
        if b is not None and b["conf"] >= trk.conf_min:
            hits.append(b)
    r.close()
    return n, len(hits)


def true_cross_stats(res_l):
    """Odległość punktu przecięcia z_c = const od generatora p* i osiągalność IK (te same kryteria co generator) — dla reguły stałej płaszczyzny."""
    m, d = ts.load()
    dist, ok = [], []
    for r in res_l:
        thr = r["thr"]
        dist.append(1000 * np.linalg.norm(r["p_ref"] - thr["p_star"]))
        q, err, ang = ts.ik_reach(m, d, r["p_ref"], thr["approach"], q0=thr["q_star"])
        ok.append(err < 1e-3 and ang <= ts.RANGES["ang_max"])
    return np.array(dist), np.array(ok)


def error_curve(res_l, comp, taus):
    """Mediana i p90 |e_comp| (comp 0,1,2) oraz |ΔT| (comp 3) dla siatki τ."""
    med, p90 = [], []
    for tau in taus:
        E, ET, _, _, _ = errors(res_l, tau)
        a = np.abs(ET) if comp == 3 else np.abs(E[:, comp])
        med.append(np.median(a) if len(a) else np.nan)
        p90.append(np.percentile(a, 90) if len(a) else np.nan)
    return np.array(med), np.array(p90)


# --------------------------------------------------------------------------------------------- uruchomienie
def self_test():
    """Szybki test (~15 s): 3 rzuty, ramię w ruchu (mode b): brak fałszywych wykryć, błąd y < 5 mm przy T − t = 0,2 s, API."""
    rl = evaluate([100, 101, 102], "b")
    ds = detection_stats(rl)
    assert ds["n_false"] == 0 and ds["n_seen"] > 100, ds
    E, ET, nthr, S, _ = errors(rl, 0.2)
    assert len(E) == 3 and np.abs(E[:, 1]).max() < 5.0 and np.abs(ET).max() < 10.0, (E, ET)
    print("OK: wykryto", ds["n_seen"], "klatek, 0 fałszywych; błąd y przy T−t=0,2 s [mm]:", np.round(E[:, 1], 2), "ΔT [ms]:", np.round(ET, 1))


def figure(rep, dev, path, res_cmp=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    taus = np.arange(0.05, 0.62, 0.01)
    fig, ax = plt.subplots(2, 3, figsize=(17, 9.5))
    col = dict(a="tab:blue", b="tab:red")
    lab = dict(a="(a) ramię nieruchome", b="(b) ramię jedzie jak w wyroczni")
    for k, (comp, ttl, unit, req) in enumerate(((1, "błąd p* w osi y chwytaka", "mm", 5), (0, "błąd p* w osi x chwytaka", "mm", 10),
                                                (2, "błąd p* w osi z chwytaka (wzdłuż lotu)", "mm", 10))):
        a = ax.flat[k]
        for md in "ab":
            med, p90 = error_curve(rep[md], comp, taus)
            a.plot(taus, med, color=col[md], label=lab[md] + " — mediana")
            a.plot(taus, p90, color=col[md], ls="--", label="p90")
        a.axhline(req, color="k", lw=0.8, ls=":")
        a.text(0.58, req * 1.1, f"tolerancja wyroczni ~{req} mm", ha="right", fontsize=8)
        a.set_yscale("log"); a.set_xlim(0.65, 0.0); a.set_ylim(0.03, 300)
        a.set_xlabel("czas do T (T − t) [s]"); a.set_ylabel(f"|e| [{unit}]"); a.set_title(ttl + " (seedy 0–49)"); a.grid(alpha=0.3)
        if k == 0:
            a.legend(fontsize=7)
    a = ax.flat[3]
    for md in "ab":
        med, p90 = error_curve(rep[md], 3, taus)
        a.plot(taus, med, color=col[md]); a.plot(taus, p90, color=col[md], ls="--")
    a.set_yscale("log"); a.set_xlim(0.65, 0.0); a.set_xlabel("T − t [s]"); a.set_ylabel("|T_pred − T| [ms]")
    a.set_title("błąd czasu przechwycenia (mediana, p90)"); a.grid(alpha=0.3)
    a = ax.flat[4]
    for md in "ab":
        for i, r in enumerate(rep[md][:25]):
            t_ = [f["tau"] for f in r["rec"] if f["out"]["p_pred"] is not None]
            e_ = [1000 * (r["R"].T @ (f["out"]["p_pred"] - r["p_ref"]))[1] for f in r["rec"] if f["out"]["p_pred"] is not None]
            a.plot(t_, e_, color=col[md], lw=0.6, alpha=0.5, label=lab[md] if i == 0 else None)
    a.axhspan(-5, 5, color="g", alpha=0.15); a.set_ylim(-30, 30); a.set_xlim(0.8, 0.0)
    a.set_xlabel("T − t [s]"); a.set_ylabel("e_y [mm] (ze znakiem)"); a.set_title("przebieg błędu y w czasie, 25 rzutów (pasmo = ±5 mm)"); a.legend(fontsize=7)
    a = ax.flat[5]
    if res_cmp:
        names = list(res_cmp)
        x = np.arange(len(names))
        for j, tau in enumerate((0.4, 0.3, 0.2)):
            v = []
            for nme in names:
                E, _, _, _, _ = errors(res_cmp[nme], tau)
                v.append(np.median(np.abs(E[:, 1])) if len(E) else np.nan)
            a.bar(x + 0.27 * (j - 1), v, 0.27, label=f"T−t = {tau} s")
        a.set_xticks(x); a.set_xticklabels(names); a.set_yscale("log"); a.axhline(5, color="k", ls=":", lw=0.8)
        a.set_ylabel("mediana |e_y| [mm]"); a.set_title("rozdzielczość kamery (seedy 100–149, ramię jedzie)"); a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=105)
    plt.close(fig)


def main():
    t_all = time.time()
    L = []
    pr = lambda s="": (L.append(s), print(s, flush=True))
    pr("Etap 5 — percepcja 3D i predyktor toru (throw_percept.py): kamera „eye” 320×240, detekcja po kolorze, parabola balistyczna")
    pr("WARSTWA INŻYNIERSKA (oko robota w pełnej rozdzielczości), nie siatkówka muchy 32×24. Tryb (a): ramię nieruchome w rest_pose; "
       "(b): ramię stoi do D = 0,25 s, potem jedzie do q* z prędkością serwa jak w oracle_trial (kamera się rusza).")
    pr("Błąd p*: p_pred (punkt toru na płaszczyźnie z = z prawdziwego p*) − prawdziwe p*, w układzie chwytaka w pozie q* "
       "(oś z = kierunek lotu, oś y = poprzeczna w pionie; wyrocznia: tolerancja y ≈ ±5 mm, x ≈ ±10 mm, z ≈ −10…+20 mm; stage5_throw_scene.txt).")
    pr(f"Parametry: c_min {C_MIN}, A_MIN {A_MIN}, σ_c {SIG_C} px, K_A {K_A}, N_MIN {N_MIN}, GATE {GATE}σ, N_RESET {N_RESET}, kroki klatek 10 ms (100 Hz), "
       f"klatki do T − 10 ms.")
    pr("")
    m, d = ts.load()
    rep_seeds, dev_seeds = list(range(0, 50)), list(range(100, 150))
    thr_rep = {s: ts.make_throw(s, m, d) for s in rep_seeds}
    thr_dev = {s: ts.make_throw(s, m, d) for s in dev_seeds}

    pr("=" * 30 + " RAPORT: seedy 0–49 (jeden przebieg) " + "=" * 30)
    rep = {md: evaluate(rep_seeds, md, thr_cache=thr_rep) for md in "ab"}
    for md in "ab":
        for ln in table(rep[md], f"({md}) " + ("ramię nieruchome w rest_pose" if md == "a" else "ramię jedzie jak w wyroczni (po D = 0,25 s do q*)")):
            pr(ln)
        ds = detection_stats(rep[md])
        pr(f"  detekcja: klatek {ds['n_frames']}, z piłeczką w polu widzenia (prawda: ≥ {A_MIN} px) {ds['n_vis']}, wykryta i przyjęta {ds['n_seen']} = "
           f"{100 * ds['n_seen'] / ds['n_vis']:.1f} %; braki: na brzegu obrazu {ds['why']['brzeg']}, brak plamki {ds['why']['brak_plamki']}, odrzucona (bramka/pewność) {ds['why']['odrzucona']}; "
           f"fałszywe przyjęcia: {ds['n_false']} z {ds['n_acc']}")
        pr(f"  dokładność pomiaru: błąd środka plamki mediana {np.median(ds['err_uv']):.3f} px, p99 {np.percentile(ds['err_uv'], 99):.2f} px; błąd promienia po poprawce δ: "
           f"średnia {ds['err_r'].mean():+.3f} px, odch. std {ds['err_r'].std():.3f} px")
        z = []
        for tau in (0.3, 0.2, 0.1):
            E, _, _, S, _ = errors(rep[md], tau)
            z.append(f"τ={tau}: " + ", ".join(f"{c} {np.median(np.abs(E[:, i] / S[:, i])):.2f}" for i, c in enumerate("xyz")))
        pr("  kalibracja niepewności: mediana |e|/σ_trackera (rozkład normalny: 0,67): " + "; ".join(z))
        cpu = np.array([[f["out"]["cpu_ms"], f["out"]["render_ms"]] for r in rep[md] for f in r["rec"]])
        pr(f"  koszt na klatkę: render kamery 320×240 {cpu[:, 1].mean():.1f} ms (mediana {np.median(cpu[:, 1]):.1f}), detekcja + tracker {cpu[:, 0].mean():.2f} ms "
           f"(p99 {np.percentile(cpu[:, 0], 99):.2f} ms)")
        pr("")
    n_fa, k_fa = false_alarm_test()
    pr(f"Fałszywe wykrycia bez piłeczki: {k_fa} / {n_fa} klatek z losowych póz ramienia i rozwarć szczęk (cały zakres stawów; ściany, stół, pady, ramię w kadrze).")
    pr("")

    pr("-- reguła praktyczna: STAŁA płaszczyzna z_c = 0,28 m (tracker nie zna p*), prawda = przecięcie prawdziwego toru z tą płaszczyzną --")
    fixed = evaluate(rep_seeds, "b", z_rule=CROSS_Z, thr_cache=thr_rep)
    for ln in table(fixed, "(b) z_c = 0,28 m, błąd względem punktu i czasu przecięcia prawdziwego toru"):
        pr(ln)
    dist, okik = true_cross_stats(fixed)
    pr(f"  punkt przecięcia z_c = 0,28 m jest od generatora p* o {np.median(dist):.0f} mm (mediana), max {dist.max():.0f} mm; IK dochodzi do niego z osią w ang_max "
       f"(jak generator) u {int(okik.sum())}/{len(okik)} rzutów — to nie jest test chwytu (wyrocznia nie była uruchamiana na tym punkcie)")
    pr("")

    pr("=" * 30 + " STROJENIE / BADANIA: seedy 100–149 " + "=" * 30)
    dev = {md: evaluate(dev_seeds, md, thr_cache=thr_dev) for md in "ab"}
    for md in "ab":
        for ln in table(dev[md], f"({md}) seedy 100–149 (te same parametry)"):
            pr(ln)
        pr("")
    pr("Wpływ rozdzielczości (ramię jedzie (b); |e_y| mediana/p90 [mm] (% < 5 mm, rzuty z predykcją/rzuty)); koszt na klatkę:")
    res_cmp = {}
    for res in ((128, 96), (160, 120), (320, 240), (640, 480)):
        rl = dev["b"] if res == (320, 240) else evaluate(dev_seeds, "b", res=res, thr_cache=thr_dev)
        res_cmp[f"{res[0]}×{res[1]}"] = rl
        cpu = np.array([[f["out"]["cpu_ms"], f["out"]["render_ms"]] for r in rl for f in r["rec"]])
        ds = detection_stats(rl)
        pr(short_row(rl, f"{res[0]}×{res[1]}") + f" | render {cpu[:, 1].mean():.1f} ms, tracker {cpu[:, 0].mean():.2f} ms, wykrycie {100 * ds['n_seen'] / ds['n_vis']:.0f} %")
    pr("")
    pr("Poza spoczynkowa kamery (ramię jedzie (b), 320×240):")
    for p, el in (((0.25, 0, 0.30), 40), ((0.25, 0, 0.30), 60), ((0.25, 0, 0.30), 20), ((0.20, 0, 0.26), 40), ((0.20, 0, 0.35), 40)):
        try:
            q = ts.rest_pose(m, d, p, el)
        except AssertionError:
            pr(f"  paszcza {p}, oś +{el}°: nieosiągalna")
            continue
        rl = dev["b"] if (p, el) == (ts.REST["p"], ts.REST["el_deg"]) else evaluate(dev_seeds, "b", rest=q, thr_cache=thr_dev)
        pr(short_row(rl, f"paszcza {p}, oś +{el}°" + ("  <- obecna" if (p, el) == (ts.REST["p"], ts.REST["el_deg"]) else ""), taus=(0.6, 0.4, 0.3, 0.2)))
    pr("")
    pr("Odporność (ramię jedzie (b), 320×240, seedy 100–149; tracker z σ_c = 0,25 px, K_A = 0,8; c_min = 5σ dla szumu):")
    for sg in (1.0, 2.0, 4.0):
        rl = evaluate(dev_seeds, "b", thr_cache=thr_dev, noise=sg, trk_kw=dict(c_min=int(round(5 * sg)), sig_c=0.25, k_a=0.8))
        ds = detection_stats(rl)
        pr(short_row(rl, f"szum obrazu σ = {sg:g}/255 (c_min {int(round(5 * sg))})") + f" | wykrycie {100 * ds['n_seen'] / ds['n_vis']:.0f} %, fałszywe {ds['n_false']}")
    for deg, mm in ((0.05, 0), (0.1, 0), (0.25, 0), (0.5, 0), (0, 2), (0, 5)):
        rl = evaluate(dev_seeds, "b", thr_cache=thr_dev, hand_eye=(deg, mm))
        pr(short_row(rl, f"błąd kalibracji ręka–oko: {deg}° / {mm} mm"))
    for lag in (1, 3, 5, 10):
        rl = evaluate(dev_seeds, "b", thr_cache=thr_dev, lag_ms=lag)
        pr(short_row(rl, f"poza kamery spóźniona o {lag} ms względem obrazu"))
    pr("")
    pr(f"[czas {time.time() - t_all:.0f} s]")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "stage5_percept.txt"), "w").write("\n".join(L) + "\n")
    figure(rep, dev, os.path.join(HERE, "results", "stage5_percept.png"), res_cmp)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        self_test()
    else:
        main()
