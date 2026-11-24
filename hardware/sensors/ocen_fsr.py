"""Ocena krótkiego nagrania FSR (ms,A0,A1): wykres obu kanałów, 6 naciśnięć, powrót do spoczynku, reakcja drugiego kanału.
Tylko SUROWE zliczenia ADC (0–1023), bez niutonów. Niczego nie wysyła do sprzętu. CAŁY czas pochodzi ze znaczników Arduino (kolumna ms),
nigdy z numeru wiersza — brakujące wiersze widać jako lukę.
  ocen_fsr.py NAGRANIE.csv WYKRES.png [--kolejnosc 000111]     ocen_fsr.py --check     ocen_fsr.py --przypadki
Progi (ustalone przed nagraniem): spoczynek kanału = mediana z najcichszej sekundy bez luk; naciśnięcie = odchyłka ≥ 100 zliczeń (słabsze widać
tylko na wykresie); osobne naciśnięcia dzieli ≥ 0,3 s ZAOBSERWOWANEGO spokoju (luka się nie liczy); kanał naciśnięty = większa odchyłka.
Rozdzielone = drugi kanał, od początku naciśnięcia do powrotu obu, ≤ 60 ponad spoczynek i ≤ 15 % odchyłki naciśniętego.
Powrót = OBA kanały jednocześnie w ±20 zliczeń przez ≥ 0,2 s, nie później niż 1 s po puszczeniu (ostatnia próbka ≥ 100). Luka = odstęp > 50 ms.
Luka między puszczeniem a końcem powrotu → „NIE DO OCENY” (powrotu nie widziano), chyba że i tak widać powrót za późny → „NIE”."""
import sys

import numpy as np

PROG, CICHO_S, OBCY, OBCY_U, POWROT, POWROT_S, SPOKOJ_S, LUKA_S, SLABE = 100, 0.3, 60, 0.15, 20, 1.0, 0.2, 0.05, 300
TAK, NIE, NIEWIEM, EPS = "TAK", "NIE", "NIE DO OCENY", 1e-9


def wczytaj(p):
    """Zwraca (tablica [ms, A0, A1], liczba odrzuconych wierszy poza nagłówkiem)."""
    d, zle = [], 0
    for i, ln in enumerate(open(p)):
        r = ln.strip().split(",")
        if len(r) == 3 and all(x.strip().isdigit() for x in r):
            d.append([int(x) for x in r])
        elif ln.strip() and i > 0:
            zle += 1
    return np.array(d), zle


def spoczynek(t, x):
    """Mediana z najcichszej (najniższej) sekundy bez luk, osobno dla kanału."""
    best = None
    for t0 in np.arange(t[0], max(t[-1] - 1.0, t[0]) + EPS, 0.25):
        m = (t >= t0) & (t < t0 + 1.0)
        tt = t[m]
        if len(tt) >= 5 and tt[-1] - tt[0] >= 0.9 and np.diff(tt).max() <= LUKA_S + EPS:
            v = float(np.median(x[m]))
            best = v if best is None else min(best, v)
    return best


def powrot(t, w_spoczynku, z, koniec):
    """Pierwsza chwila po próbce z, od której w_spoczynku trwa ≥ 0,2 s bez luk. → (czas od puszczenia albo None, indeks albo None)."""
    i = z + 1
    while i < koniec:
        if w_spoczynku[i]:
            j = i
            while j + 1 < koniec and w_spoczynku[j + 1] and t[j + 1] - t[j] <= LUKA_S + EPS:
                j += 1
                if t[j] - t[i] >= SPOKOJ_S - EPS:
                    return float(t[i] - t[z]), i
            i = j + 1
        else:
            i += 1
    return None, None


def ocen(d, kolejnosc="000111"):
    ms = d[:, 0].astype(float)
    if len(d) < 50 or (np.diff(ms) <= 0).any():
        return dict(werdykt=NIEWIEM, powody=["znaczniki czasu Arduino cofają się lub stoją (reset?) albo zapis za krótki"], P=[], t=(ms - ms[0]) / 1000 if len(d) else ms, x=d[:, 1:].astype(float), b=np.array([np.nan] * 2), luki=[], kol="")
    t, x = (ms - ms[0]) / 1000.0, d[:, 1:].astype(float)
    dt = np.diff(t)
    luki = [(float(t[i]), float(t[i + 1])) for i in np.flatnonzero(dt > LUKA_S + EPS)]
    b = [spoczynek(t, x[:, k]) for k in (0, 1)]
    if None in b:
        return dict(werdykt=NIEWIEM, powody=["brak spokojnej sekundy bez luk"], P=[], t=t, x=x, b=np.array([np.nan] * 2), luki=luki, kol="")
    b = np.array(b)
    dx = x - b
    on = np.flatnonzero(dx.max(1) >= PROG)
    grupy = []
    for i in on:
        if grupy:
            a = grupy[-1][1]
            cicho = dt[a + 1:i]                                             # odstępy między kolejnymi cichymi próbkami a+1 … i−1
            if cicho[cicho <= LUKA_S + EPS].sum() < CICHO_S - EPS:
                grupy[-1][1] = i
                continue
        grupy.append([i, i])
    P = []
    for n, (a, z) in enumerate(grupy):
        kanal = int(dx[a:z + 1].max(0).argmax())
        o, kon = 1 - kanal, grupy[n + 1][0] if n + 1 < len(grupy) else len(t)
        spok = np.abs(dx) <= POWROT
        pk = [powrot(t, spok[:, c], z, kon)[0] for c in (0, 1)]
        pw, iw = powrot(t, spok.all(1), z, kon)
        do_i = iw if iw is not None else kon - 1
        do_i = min(do_i, int(np.searchsorted(t, t[z] + POWROT_S + SPOKOJ_S, "right")) - 1)
        do_i = max(do_i, z)
        tz_p = next((v for u, v in luki if abs(u - t[z]) < EPS), float(t[z]))     # luka tuż po ostatniej próbce ≥ 100: puszczenie mogło nastąpić aż do jej końca
        l_nac = [(u, v) for u, v in luki if u >= t[a] - EPS and v <= t[z] + EPS]
        gr = t[z] + (pw if pw is not None else POWROT_S)                    # do tej chwili powrót musi być widziany w całości
        l_pow = [(u, v) for u, v in luki if u >= t[z] - EPS and u < gr - EPS and u < t[z] + POWROT_S - EPS]
        pozno = (t > tz_p + POWROT_S + EPS) & (np.arange(len(t)) < kon) & ~spok.all(1)
        za_pozno = pw is not None and t[z] + pw - tz_p > POWROT_S + EPS       # liczone od NAJPÓŹNIEJSZEGO możliwego puszczenia
        zakres = f"po {t[z] + pw - tz_p:.2f}–{pw:.2f} s" if pw is not None and tz_p > t[z] else f"po {pw:.2f} s" if pw is not None else ""
        if pw is not None and not za_pozno:
            r = (NIEWIEM, f"luka {l_pow[0][0]:.2f}–{l_pow[0][1]:.2f} s w czasie powrotu; powrotu nie widziano, oba w spoczynku {zakres} (granice niepewne)") if l_pow else (TAK, f"oba po {pw:.2f} s")
        elif pozno.any() or (za_pozno and not l_pow):
            r = (NIE, f"oba dopiero {zakres} (> {POWROT_S:.0f} s)" if pw is not None else "brak wspólnego spoczynku do następnego naciśnięcia / końca zapisu")
        elif l_pow:
            r = (NIEWIEM, f"luka {l_pow[0][0]:.2f}–{l_pow[0][1]:.2f} s w czasie powrotu")
        elif kon == len(t):
            r = (NIEWIEM, "zapis kończy się przed końcem powrotu")
        else:
            r = (NIE, "następne naciśnięcie przed powrotem obu kanałów")
        seg = dx[a:do_i + 1]
        dn, kn = float(seg[:, o].max()), float(dx[a:z + 1, kanal].max())
        roz = NIE if dn > OBCY or dn / kn > OBCY_U else NIEWIEM if l_nac or l_pow else TAK
        P.append(dict(nr=n + 1, kanal=kanal, od=float(t[a]), do=float(t[z]), szczyt=float(x[a:z + 1, kanal].max()), szczyt_nad=kn, drugi_szczyt=float(x[a:do_i + 1, o].max()), drugi_nad=dn, udzial=dn / kn,
                      drugi_czas=float(t[a + int(seg[:, o].argmax())]), rozdzielone=roz, powrot=r[0], powrot_opis=r[1], powrot_kanalow=pk, powrot_obu=pw, luka_w_nacisku=l_nac))
    kol = "".join(str(p["kanal"]) for p in P)
    odwr = kolejnosc.translate(str.maketrans("01", "10"))
    pow_, nw = [], []
    nap = lambda s: ", ".join("A" + c for c in s) or "brak"  # noqa: E731
    if kol == odwr and kol != kolejnosc:
        pow_.append(f"kolejność kanałów ODWROTNA do planu: zapisano {nap(kol)}, plan {nap(kolejnosc)} — czujniki zamienione albo naciskano w odwrotnej kolejności (z zapisu nie da się rozróżnić)")
    elif kol != kolejnosc:
        pow_.append(f"naciśnięcia inne niż w planie: zapisano {len(P)} ({nap(kol)}), plan {len(kolejnosc)} ({nap(kolejnosc)})")
    for p in P:
        for nazwa, w, opis in (("kanały", p["rozdzielone"], f"drugi kanał +{p['drugi_nad']:.0f} ({100 * p['udzial']:.0f} %)"), ("powrót", p["powrot"], p["powrot_opis"])):
            if w == NIE:
                pow_.append(f"naciśnięcie {p['nr']}: {nazwa} {NIE} — {opis}")
            elif w == NIEWIEM:
                nw.append(f"naciśnięcie {p['nr']}: {nazwa} {NIEWIEM}" + (f" — {opis}" if nazwa == "powrót" else " — luka w zapisie tego odcinka"))
    return dict(t=t, x=x, b=b, P=P, luki=luki, kol=kol, dt_med=float(np.median(dt)) * 1000, dt_maks=float(dt.max()) * 1000, werdykt="ODRZUCONE" if pow_ else NIEWIEM if nw else "PRZYJĘTE", powody=pow_ + nw,
                szum=[float(np.std(x[dx.max(1) < 20, k])) if (dx.max(1) < 20).any() else float("nan") for k in (0, 1)])


def drukuj(r, zle=0):
    f = lambda w: "nie wrócił" if w is None else f"{w:.2f} s"  # noqa: E731
    if r["P"] or "dt_med" in r:
        print(f"czas ze znaczników Arduino: {r['t'][-1]:.2f} s, próbek {len(r['t'])}, odstęp {r['dt_med']:.0f} ms (maks {r['dt_maks']:.0f} ms), luk > 50 ms: {len(r['luki'])}" + (f", odrzucone wiersze: {zle}" if zle else ""))
        for u, v in r["luki"]:
            print(f"   luka {u:.2f}–{v:.2f} s ({1000 * (v - u):.0f} ms)")
        print(f"spoczynek: A0 = {r['b'][0]:.0f}, A1 = {r['b'][1]:.0f} zliczeń; szum A0 {r['szum'][0]:.1f}, A1 {r['szum'][1]:.1f}; zakres A0 {r['x'][:, 0].min():.0f}–{r['x'][:, 0].max():.0f}, A1 {r['x'][:, 1].min():.0f}–{r['x'][:, 1].max():.0f}")
    for p in r["P"]:
        k, o = p["kanal"], 1 - p["kanal"]
        print(f"{p['nr']}. A{k} {p['od']:.2f}–{p['do']:.2f} s, szczyt {p['szczyt']:.0f} (+{p['szczyt_nad']:.0f}){' SŁABE' if p['szczyt'] < SLABE else ''} | A{o} najwyżej {p['drugi_szczyt']:.0f} (+{p['drugi_nad']:.0f} = {100 * p['udzial']:.0f} %, w {p['drugi_czas']:.2f} s)"
              f" | rozdzielone: {p['rozdzielone']} | powrót A0 {f(p['powrot_kanalow'][0])}, A1 {f(p['powrot_kanalow'][1])}, oba: {p['powrot']} ({p['powrot_opis']})")
    print("WERDYKT:", r["werdykt"])
    for s in r["powody"]:
        print("   -", s)


def wykres(r, path, tytul):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 10.5, "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.edgecolor": "#c9c8c2"})
    fig, a = plt.subplots(figsize=(13, 5.2), facecolor="#fcfcfb")
    a.set_facecolor("#fcfcfb")
    cut = np.flatnonzero(np.diff(r["t"]) > LUKA_S + EPS) + 1
    tt = np.insert(r["t"], cut, np.nan)                                     # przerwa w linii tam, gdzie jest luka
    for k, (c, l) in enumerate((("#2a78d6", "A0"), ("#eb6834", "A1"))):
        a.plot(tt, np.insert(r["x"][:, k], cut, np.nan), color=c, lw=1.6, label=l, zorder=3)
        a.axhline(r["b"][k], color=c, lw=0.8, ls=(0, (2, 3)), alpha=0.7)
    top = max(700.0, r["x"].max() * 1.08)
    for p in r["P"]:
        a.axvspan(p["od"], p["do"], color="#0b0b0b", alpha=0.05, lw=0)
        a.text((p["od"] + p["do"]) / 2, top * 1.015, f"{p['nr']}: A{p['kanal']}", ha="center", va="bottom", fontsize=10)
    for u, v in r["luki"]:
        a.axvspan(u, v, facecolor="none", edgecolor="#52514e", hatch="////", lw=0, alpha=0.6)
        a.text(v, top * 0.94, " luka", fontsize=9, color="#52514e")
    a.set_ylim(-15, top)
    a.set_xlim(r["t"][0], r["t"][-1])
    a.set_xlabel("czas ze znaczników Arduino [s]")
    a.set_ylabel("surowe zliczenia ADC (0–1023)")
    a.grid(axis="y", color="#e8e7e2", lw=0.8)
    a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.legend(loc="upper left", bbox_to_anchor=(0, 1.17), ncol=2, frameon=False)
    fig.suptitle(f"{tytul} — werdykt: {r['werdykt']}", x=0.065, ha="left", fontsize=13.5, fontweight="bold", y=0.985)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.8, bottom=0.13)
    fig.savefig(path, dpi=140)


# ---------------------------------------------------------------- sztuczne przypadki ---------------------------------------------------------
STARTY = (8, 15, 22, 32, 39, 46)


def syn(ogon=None, seed=1, odstepy=None, tylko=None):
    """60 s, 6 naciśnięć po 2 s (3 × A0, 3 × A1), narastanie i opadanie 0,1 s, szczyt +600. ogon(u, kanał_naciśnięty) → (dod. A0, dod. A1) u s po puszczeniu."""
    rng = np.random.default_rng(seed)
    ms = np.arange(0, 60000, 10) if odstepy is None else np.cumsum(rng.integers(*odstepy, 6000))
    t = ms / 1000
    x = np.c_[2 + rng.integers(0, 2, len(t)), 4 + rng.integers(0, 2, len(t))].astype(float)
    for j, t0 in enumerate(STARTY):
        k = int(j >= 3)
        x[:, k] += 600 * np.clip(np.minimum((t - t0) / 0.1, (t0 + 2.1 - t) / 0.1), 0, 1)
        if ogon is not None and tylko in (None, j):
            u = t - (t0 + 2.1)                                              # 0 = koniec opadania
            m = (u >= -0.1) & (u < 4)
            e = np.array([ogon(v, k) for v in u[m]])
            x[m, k] += e[:, 0]
            x[m, 1 - k] += e[:, 1]
    return np.c_[ms + 26050, np.round(x)].astype(int)


def luka(d, t0, t1):
    s = (d[:, 0] - d[0, 0]) / 1000
    return d[(s < t0) | (s > t1)]


def przypadki():
    """(nazwa, dane, oczekiwany werdykt, fragment oczekiwanego powodu)."""
    return [
        ("0. wzorzec (kontrola)", syn(), "PRZYJĘTE", ""),
        ("1. zamienione kanały", syn()[:, [0, 2, 1]], "ODRZUCONE", "ODWROTNA"),
        ("2a. różne chwile: naciśnięty ~0,1 s, drugi (+45) ~0,6 s", syn(lambda u, k: (0, 45 if u < 0.5 else 0)), "PRZYJĘTE", ""),
        ("2b. różne chwile: drugi (+45) wraca po ~1,4 s", syn(lambda u, k: (0, 45 if u < 1.3 else 0)), "ODRZUCONE", "oba dopiero"),
        ("2c. każdy wraca osobno, ale nigdy razem w 1 s", syn(lambda u, k: (40 if 0.45 <= u < 1.5 else 0, 45 if u < 0.5 else 0)), "ODRZUCONE", "oba dopiero"),
        ("3a. luka 0,4 s podczas powrotu 2. naciśnięcia", luka(syn(), 17.03, 17.43), NIEWIEM, "luka"),
        ("3b. luka 0,4 s + powrót na granicy (0,97–1,39 s)", luka(syn(lambda u, k: (0, 45 if u < 1.3 else 0), tylko=1), 17.03, 17.43), NIEWIEM, "luka"),
        ("3d. luka 0,4 s + powrót na pewno za późny (~2 s)", luka(syn(lambda u, k: (0, 45 if u < 2.0 else 0), tylko=1), 17.03, 17.43), "ODRZUCONE", "oba dopiero"),
        ("3c. luka 0,4 s daleko od naciśnięć (kontrola)", luka(syn(), 28.0, 28.4), "PRZYJĘTE", ""),
    ]


def check():
    for nazwa, d, w, frag in przypadki():
        r = ocen(d)
        assert r["werdykt"] == w and (not frag or any(frag in s for s in r["powody"])), (nazwa, r["werdykt"], r["powody"])
    for p in ocen(syn(odstepy=(8, 15)))["P"]:                               # nierówne odstępy 8–14 ms: czasy nadal prawdziwe
        assert abs(p["od"] - STARTY[p["nr"] - 1]) < 0.06 and abs(p["do"] - STARTY[p["nr"] - 1] - 2.08) < 0.06 and p["powrot"] == TAK
    g = syn()[::2]                                                          # co drugi wiersz (20 ms): ten sam wynik czasowy
    assert ocen(g)["werdykt"] == "PRZYJĘTE" and abs(ocen(g)["P"][0]["powrot_obu"] - ocen(syn())["P"][0]["powrot_obu"]) <= 0.021
    q = syn()
    q[3000:, 0] -= 5000                                                     # reset Arduino
    assert ocen(q)["werdykt"] == NIEWIEM
    h = luka(syn(), 15.5, 16.3)                                             # luka W nacisku nie dzieli go na dwa
    assert ocen(h)["kol"] == "000111" and ocen(h)["werdykt"] == NIEWIEM
    assert ocen(syn(lambda u, k: (0, 0)))["werdykt"] == "PRZYJĘTE" and len(ocen(np.c_[np.arange(3000) * 10, np.full(3000, 2), np.full(3000, 4)])["P"]) == 0
    c = syn()
    c[:, 2] += (c[:, 1] * 0.3).astype(int)                                  # przenikanie 30 %
    assert ocen(c)["werdykt"] == "ODRZUCONE"
    print("check OK")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--check"]:
        check()
    elif a[:1] == ["--przypadki"]:
        for nazwa, d, w, _ in przypadki():
            print("\n###", nazwa, "| oczekiwano:", w)
            drukuj(ocen(d))
    else:
        dane, zle = wczytaj(a[0])
        r = ocen(dane, a[a.index("--kolejnosc") + 1] if "--kolejnosc" in a else "000111")
        drukuj(r, zle)
        wykres(r, a[1], "Nagranie dwóch czujników: surowe zliczenia")
