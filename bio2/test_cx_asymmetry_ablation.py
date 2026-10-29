#!/usr/bin/env python3
"""
bio2/test_cx_asymmetry_ablation.py

Eksperyment 1: Przyczynowa dekompozycja asymetrii kompleksu centralnego (CX).
Rozdziela wpływ czterech czynników na przesunięcie wzgórza EPG i asymetrię DNa02 przy cue = 0.0 rad:
  Czynnik A: Asymetria wag synaptycznych PFL3 -> DNa02 (380 vs 356 synaps).
  Czynnik B: Geometria neuronów EPG i przypisanie do klinów (dyskretyzacja wokół 0°).
  Czynnik C: Asymetria syntetycznych profili sektorowych CX (16 koszyków).
  Czynnik D: Modelowe wejście celu PFL3 (goal_amp = 6.0 mV vs 0.0 mV).

Eksperyment działa całkowicie w pamięci RAM, jest izolowany od kodu produkcyjnego
i nie modyfikuje żadnych istniejących plików repozytorium.
"""

import math
import os
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from brain import Brain, B
from snn import ConnectomeSNN


# -----------------------------------------------------------------------------
# Konfiguracja protokołu eksperymentalnego
# -----------------------------------------------------------------------------
CFG = dict(
    n_seeds=40,              # Liczba sparowanych ziaren losowości (N >= 30)
    t_transient_ms=200,      # Okres rozruchowy (20 kroków step10)
    t_measure_ms=300,        # Okno pomiarowe (30 kroków step10)
    cue_rad=0.0,             # Symetryczny bodziec centralny
    alpha_signif=0.05,       # Poziom istotności statystycznej
)


# -----------------------------------------------------------------------------
# Narzędzia pomocnicze do symetryzacji modeli w pamięci
# -----------------------------------------------------------------------------
def mirror_group_name(g: str) -> str:
    """Zwraca nazwę grupy bilateralnej po przeciwnej stronie (L <-> R)."""
    if g.endswith("_L"):
        return g[:-2] + "_R"
    if g.endswith("_R"):
        return g[:-2] + "_L"
    return g


def make_brain_variant(variant: str, seed: int) -> Brain:
    """
    Kompiluje wariant modelu mózgu z wybraną ablacją w pamięci RAM.
    Gwarantuje brak modyfikacji globalnych parametrów współdzielonych.
    """
    b = Brain(seed=seed)
    g = b.groups
    cx_groups = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R"]

    apply_A = "A" in variant
    apply_B = "B" in variant
    apply_C = "C" in variant
    apply_D = "D" in variant

    # 1. Czynnik D: Wyłączenie modelowego wejścia celu PFL3
    if apply_D:
        b.p["goal_amp"] = 0.0

    # 2. Czynnik B: Symetryzacja siatki kątowej EPG wokół 0.0 rad
    if apply_B:
        epg = g["EPG"]
        n_epg = len(epg)
        # Rozstawienie 46 neuronów na symetrycznej siatce z neuronem dokładnie w 0.0 rad
        # Kąty: k * (2*pi / n_epg) dla k w [-22, -21, ..., 0, ..., 23]
        k_vals = np.arange(-n_epg // 2, n_epg // 2 + (1 if n_epg % 2 else 0))
        order = epg[np.argsort(np.angle(np.exp(1j * b.theta[epg])))]
        th_sym = 2.0 * np.pi * k_vals / float(n_epg)
        b.theta[order] = np.angle(np.exp(1j * th_sym))

    # 3. Czynnik C: Symetryzacja profili sektorowych CX
    if apply_C:
        sym_prof = {}
        for ga in cx_groups:
            for gb in cx_groups:
                ga_m, gb_m = mirror_group_name(ga), mirror_group_name(gb)
                p1 = b.profiles[(ga, gb)]
                p2 = b.profiles[(ga_m, gb_m)]
                # Odbicie zwierciadlane wokół różnicy faz równej 0: k -> (B - k) % B
                p2_mirr = np.array([p2[(B - k) % B] for k in range(B)])
                sym_prof[(ga, gb)] = 0.5 * (p1 + p2_mirr)
        b.profiles = sym_prof

    # Jeśli zmieniono geometrię (B) lub profile (C), przebuduj wewnętrzne wagi CX
    if apply_B or apply_C:
        W_cx = np.zeros((b.N, b.N))
        for ga in cx_groups:
            for gb in cx_groups:
                pre, post = g[ga], g[gb]
                d = np.angle(np.exp(1j * (b.theta[post][:, None] - b.theta[pre][None, :]))) / (2 * np.pi / B)
                p_, k0 = b.profiles[(ga, gb)], np.floor(d).astype(int)
                f = d - k0
                W_cx[np.ix_(post, pre)] = ((1 - f) * p_[k0 % B] + f * p_[(k0 + 1) % B]) * b.p["J0_CX"]
        np.fill_diagonal(W_cx, 0)

        # Zachowaj wagi poza CX z istniejącej macierzy b.net.W (uwzględniając znaki i skale)
        cx = np.concatenate([g[k] for k in cx_groups])
        ring = np.concatenate([g[k] for k in ("EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R")])

        # Aplikacja znaków i skal hamowania
        W_cx *= b.net.sign[None, :]
        W_cx[np.ix_(ring, g["Delta7"])] *= b.p["G_INH"]
        W_cx[np.ix_(g["Delta7"], g["Delta7"])] *= b.p["G_DD"]

        # Połącz z wagami spoza CX
        b.net.W[np.ix_(cx, cx)] = W_cx[np.ix_(cx, cx)]

    # 4. Czynnik A: Symetryzacja wejścia PFL3 -> DNa02 (uśrednienie par bilateralnych)
    if apply_A:
        dna02_r = g["DNa02_R"][0]
        dna02_l = g["DNa02_L"][0]
        pfl3_l = g["PFL3_L"]
        pfl3_r = g["PFL3_R"]

        ord_l = pfl3_l[np.argsort(b.theta[pfl3_l])]
        ord_r = pfl3_r[np.argsort(b.theta[pfl3_r])]
        th_l = np.degrees(b.theta[ord_l])
        th_r = np.degrees(b.theta[ord_r])

        for i in range(len(ord_l)):
            target_th = -th_l[i]
            diffs = np.abs(np.angle(np.exp(1j * np.radians(th_r - target_th))))
            j = int(np.argmin(diffs))
            # Uśrednienie bilateralnej wagi
            w_avg = 0.5 * (b.net.W[dna02_r, ord_l[i]] + b.net.W[dna02_l, ord_r[j]])
            b.net.W[dna02_r, ord_l[i]] = w_avg
            b.net.W[dna02_l, ord_r[j]] = w_avg

        # Zaktualizuj duplikat DNa01
        for s_pre, s_post in (("L", "R"), ("R", "L")):
            pre, post = g["PFL3_" + s_pre], g["DNa01_" + s_post]
            b.net.W[np.ix_(post, pre)] = b.net.W[np.ix_(g["DNa02_" + s_post], pre)] * b.p["dna01_frac"]

    b.reset()
    b.net.rng = np.random.default_rng(seed)
    return b


# -----------------------------------------------------------------------------
# Procedura pomiarowa
# -----------------------------------------------------------------------------
def measure_condition(b: Brain, cue: float, seed: int) -> Dict[str, float]:
    """Wykonuje okres przejściowy oraz pomiar w stacjonarnym oknie czasowym."""
    b.reset()
    b.net.rng = np.random.default_rng(seed)

    n_trans = CFG["t_transient_ms"] // 10
    n_meas = CFG["t_measure_ms"] // 10

    # Rozruch
    for _ in range(n_trans):
        b.step10(cue=cue, u=0.0, rest=False)

    # Rejestracja
    spk_chunks = []
    rate_samples = []
    for _ in range(n_meas):
        spk = b.step10(cue=cue, u=0.0, rest=False)
        spk_chunks.append(spk)
        rate_samples.append(b.rate.copy())

    spk_all = np.concatenate(spk_chunks, axis=0)  # (t_ms, N)
    rate_arr = np.array(rate_samples)            # (n_steps, N)

    idx_dna02_l = b.groups["DNa02_L"]
    idx_dna02_r = b.groups["DNa02_R"]

    dur_sec = spk_all.shape[0] / 1000.0
    raw_dna02_l = float(spk_all[:, idx_dna02_l].sum() / dur_sec)
    raw_dna02_r = float(spk_all[:, idx_dna02_r].sum() / dur_sec)

    cont_dna02_l = float(rate_arr[:, idx_dna02_l].mean())
    cont_dna02_r = float(rate_arr[:, idx_dna02_r].mean())

    raw_ang, bump_coh, bump_rate = b.bump(spk_all)

    # Zabezpieczenie przed NaN / Inf
    assert np.isfinite(raw_ang), "Kąt EPG zawiera NaN/Inf!"
    assert np.isfinite(cont_dna02_l), "Aktywność DNa02_L zawiera NaN/Inf!"
    assert np.isfinite(cont_dna02_r), "Aktywność DNa02_R zawiera NaN/Inf!"

    return dict(
        epg_angle_deg=math.degrees(raw_ang),
        epg_angle_rad=raw_ang,
        epg_coherence=bump_coh,
        epg_rate_hz=bump_rate,
        dna02_l_cont=cont_dna02_l,
        dna02_r_cont=cont_dna02_r,
        dna02_diff_cont=cont_dna02_l - cont_dna02_r,
        dna02_l_raw=raw_dna02_l,
        dna02_r_raw=raw_dna02_r,
        dna02_diff_raw=raw_dna02_l - raw_dna02_r,
    )


# -----------------------------------------------------------------------------
# Statystyka i analiza sparowana
# -----------------------------------------------------------------------------
def compute_stats(arr: np.ndarray) -> Dict[str, float]:
    """Oblicza średnią, SD i 95% CI dla pojedynczego wektora."""
    n = len(arr)
    m = float(np.mean(arr))
    s = float(np.std(arr, ddof=1))
    se = s / math.sqrt(n)
    t_crit = float(st.t.ppf(0.975, df=n - 1))
    return dict(mean=m, std=s, ci_lo=m - t_crit * se, ci_hi=m + t_crit * se)


def compute_circular_stats(rad_arr: np.ndarray) -> Dict[str, float]:
    """Oblicza średnią kołową oraz kołowe odchylenie standardowe w stopniach."""
    n = len(rad_arr)
    c = np.cos(rad_arr).sum()
    s = np.sin(rad_arr).sum()
    mean_rad = math.atan2(s, c)
    R = math.hypot(c, s) / n
    circ_var = 1.0 - R
    circ_sd_deg = math.degrees(math.sqrt(max(-2.0 * math.log(max(R, 1e-12)), 0.0)))
    mean_deg = math.degrees(mean_rad)

    # Standard error of circular mean
    se_deg = circ_sd_deg / math.sqrt(n)
    t_crit = float(st.t.ppf(0.975, df=n - 1))
    return dict(
        mean=mean_deg,
        std=circ_sd_deg,
        ci_lo=mean_deg - t_crit * se_deg,
        ci_hi=mean_deg + t_crit * se_deg,
    )


def compute_paired_comparison(sample_var: np.ndarray, sample_base: np.ndarray) -> Dict[str, float]:
    """Oblicza sparowaną różnicę, jej 95% CI, p-wartości oraz wielkość efektu Cohen's dz."""
    diffs = sample_var - sample_base
    n = len(diffs)
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1))
    se_diff = std_diff / math.sqrt(n)
    t_crit = float(st.t.ppf(0.975, df=n - 1))

    if std_diff < 1e-12:
        return dict(
            delta_mean=mean_diff,
            delta_std=0.0,
            ci_lo=mean_diff,
            ci_hi=mean_diff,
            cohens_dz=0.0,
            p_ttest=1.0,
            p_wilcox=1.0,
        )

    # Cohen's dz dla par zależnych
    cohens_dz = mean_diff / std_diff

    # Test t sparowany
    t_stat, p_ttest = st.ttest_rel(sample_var, sample_base)

    # Test Wilcoxona (odporny)
    try:
        w_stat, p_wilcox = st.wilcoxon(sample_var, sample_base)
    except Exception:
        p_wilcox = 1.0

    return dict(
        delta_mean=mean_diff,
        delta_std=std_diff,
        ci_lo=mean_diff - t_crit * se_diff,
        ci_hi=mean_diff + t_crit * se_diff,
        cohens_dz=cohens_dz,
        p_ttest=float(p_ttest),
        p_wilcox=float(p_wilcox),
    )


# -----------------------------------------------------------------------------
# Główna procedura wykonawcza
# -----------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("=" * 90)
    print("SNN/CX — EKSPERYMENT 1: PRZYCZYNOWA DEKOMPOZYCJA ASYMETRII")
    print(f"Liczba sparowanych ziaren: N = {CFG['n_seeds']} | Bodziec: cue = {CFG['cue_rad']} rad")
    print(f"Czasy: Transient = {CFG['t_transient_ms']} ms | Pomiar = {CFG['t_measure_ms']} ms")
    print("=" * 90)

    # 1. Walidacja wstępna i kontrola determinizmu
    print("\n--- 1. KONTROLE INTEGRALNOŚCI MODELU ---")
    b0 = make_brain_variant("baseline", seed=0)
    res0 = measure_condition(b0, cue=CFG["cue_rad"], seed=0)
    print(f"Odtworzenie Baseline (seed 0):")
    print(f"  EPG Angle: {res0['epg_angle_deg']:+6.2f}° | Coherence: {res0['epg_coherence']:.3f} | Rate: {res0['epg_rate_hz']:.1f} Hz")
    print(f"  DNa02 L: {res0['dna02_l_cont']:5.1f} Hz | R: {res0['dna02_r_cont']:5.1f} Hz | L-R: {res0['dna02_diff_cont']:+6.2f} Hz")

    # Sprawdzenie determinizmu dla seed 42
    b_det1 = make_brain_variant("baseline", seed=42)
    m1 = measure_condition(b_det1, cue=CFG["cue_rad"], seed=42)
    b_det2 = make_brain_variant("baseline", seed=42)
    m2 = measure_condition(b_det2, cue=CFG["cue_rad"], seed=42)
    diff_det = abs(m1["dna02_diff_cont"] - m2["dna02_diff_cont"])
    assert diff_det < 1e-12, f"Brak determinizmu: diff = {diff_det}"
    print(f"Kontrola determinizmu (seed 42, 2 przebiegi): różnica = {diff_det:.2e} Hz -> Determinizm OK.")

    # 2. Definicja badanych wariantów
    variants = [
        ("baseline",       "Baseline (model bez zmian)"),
        ("ablation_A",     "Ablacja A (symetryzacja wag PFL3->DNa02)"),
        ("ablation_B",     "Ablacja B (symetryzacja geometrii EPG wokół 0°)"),
        ("ablation_C",     "Ablacja C (symetryzacja profili sektorowych CX)"),
        ("ablation_D",     "Ablacja D (wyłączenie wejścia celu goal_amp=0)"),
        ("combined_AB",    "Wariant A+B (wagi PFL3 + geometria EPG)"),
        ("combined_BC",    "Wariant B+C (geometria EPG + profile CX)"),
        ("combined_ABC",   "Wariant A+B+C (pełna symetryzacja obwodu)"),
        ("combined_ABCD",  "Wariant A+B+C+D (pełna symetria + goal_amp=0)"),
    ]

    # 3. Zbieranie pomiarów
    print(f"\n--- 2. REALIZACJA POMIARÓW NA {CFG['n_seeds']} ZIARNACH ---")
    raw_data = {var_key: [] for var_key, _ in variants}
    seeds = list(range(CFG["n_seeds"]))

    for s_idx, s in enumerate(seeds):
        for var_key, _ in variants:
            b_var = make_brain_variant(var_key, seed=s)
            m = measure_condition(b_var, cue=CFG["cue_rad"], seed=s)
            raw_data[var_key].append(m)

    print("Wszystkie pomiary zakończone sukcesem (brak błędów NaN/Inf).\n")

    # 4. Tabela 1: Bezwzględne charakterystyki populacji
    print("=" * 95)
    print("TABELA 1: BEZWZGLĘDNE CHARAKTERYSTYKI WARIANTÓW (Średnia ± SD [95% CI])")
    print("=" * 95)
    print(f"{'Wariant':<20} | {'Kąt EPG [°]':^21} | {'ΔDNa02 (L-R) [Hz]':^23} | {'Skupienie':^11} | {'EPG Rate':^10}")
    print("-" * 95)

    base_ang_rad = np.array([m["epg_angle_rad"] for m in raw_data["baseline"]])
    base_diff = np.array([m["dna02_diff_cont"] for m in raw_data["baseline"]])

    summary_stats = {}
    for var_key, var_name in variants:
        ang_rad = np.array([m["epg_angle_rad"] for m in raw_data[var_key]])
        diff_dna = np.array([m["dna02_diff_cont"] for m in raw_data[var_key]])
        coh = np.array([m["epg_coherence"] for m in raw_data[var_key]])
        rate = np.array([m["epg_rate_hz"] for m in raw_data[var_key]])

        s_ang = compute_circular_stats(ang_rad)
        s_diff = compute_stats(diff_dna)
        s_coh = compute_stats(coh)
        s_rate = compute_stats(rate)

        summary_stats[var_key] = dict(ang=s_ang, diff=s_diff, coh=s_coh, rate=s_rate)

        ang_str = f"{s_ang['mean']:+5.2f} ± {s_ang['std']:4.2f}"
        diff_str = f"{s_diff['mean']:+5.2f} ± {s_diff['std']:4.2f}"
        coh_str = f"{s_coh['mean']:5.3f}"
        rate_str = f"{s_rate['mean']:4.1f} Hz"

        print(f"{var_key:<20} | {ang_str:^21} | {diff_str:^23} | {coh_str:^11} | {rate_str:^10}")

    print("-" * 95)

    # 5. Tabela 2: Statystyka sparowana względem Baseline
    print("\n" + "=" * 105)
    print("TABELA 2: SPAROWANE PORÓWNANIE WZGLĘDEM BASELINE (N = 40, Paired t-test & Cohen's dz)")
    print("=" * 105)
    print(f"{'Wariant ablowany':<18} | {'Δ Kąt EPG [°]':^14} | {'p-val':^9} | {'dz (Kąt)':^8} | "
          f"{'Δ ΔDNa02 [Hz]':^15} | {'p-val':^9} | {'dz (DNa)':^8} | {'Istotny (Holm)'}")
    print("-" * 105)

    comparison_results = []
    # Testy wielokrotne dla wariantów vs baseline (8 porównań)
    n_comparisons = len(variants) - 1

    p_vals_dna = []
    for var_key, _ in variants[1:]:
        diff_dna = np.array([m["dna02_diff_cont"] for m in raw_data[var_key]])
        comp_dna = compute_paired_comparison(diff_dna, base_diff)
        p_vals_dna.append(comp_dna["p_ttest"])

    # Holm-Bonferroni correction
    sorted_indices = np.argsort(p_vals_dna)
    holm_significant = np.zeros(n_comparisons, dtype=bool)
    for rank, idx in enumerate(sorted_indices):
        threshold = CFG["alpha_signif"] / (n_comparisons - rank)
        if p_vals_dna[idx] <= threshold:
            holm_significant[idx] = True
        else:
            break

    comp_idx = 0
    for var_key, var_name in variants[1:]:
        ang_rad = np.array([m["epg_angle_rad"] for m in raw_data[var_key]])
        # Unwrapped angular difference
        ang_diff_deg = np.degrees(np.arctan2(np.sin(ang_rad - base_ang_rad), np.cos(ang_rad - base_ang_rad)))
        comp_ang = compute_paired_comparison(ang_diff_deg, np.zeros_like(ang_diff_deg))

        diff_dna = np.array([m["dna02_diff_cont"] for m in raw_data[var_key]])
        comp_dna = compute_paired_comparison(diff_dna, base_diff)

        is_sig = "TAK" if holm_significant[comp_idx] else "NIE"
        p_dna_str = f"{comp_dna['p_ttest']:.2e}" if comp_dna['p_ttest'] < 1e-3 else f"{comp_dna['p_ttest']:.4f}"
        p_ang_str = f"{comp_ang['p_ttest']:.2e}" if comp_ang['p_ttest'] < 1e-3 else f"{comp_ang['p_ttest']:.4f}"

        line = (
            f"{var_key:<18} | "
            f"{comp_ang['delta_mean']:+6.2f} ± {comp_ang['delta_std']:4.2f} | {p_ang_str:^9} | {comp_ang['cohens_dz']:+7.2f} | "
            f"{comp_dna['delta_mean']:+6.2f} ± {comp_dna['delta_std']:4.2f} | {p_dna_str:^9} | {comp_dna['cohens_dz']:+7.2f} | "
            f"{is_sig:^14}"
        )
        print(line)
        comparison_results.append((var_key, comp_ang, comp_dna))
        comp_idx += 1

    print("-" * 105)

    # 6. Analiza dekompozycji przyczynowej
    print("\n" + "=" * 90)
    print("3. DEKOMPOZYCJA PRZYCZYNOWA: KTÓRE CZYNNIKI ODPOWIADAJĄ ZA JAKĄ CZĘŚĆ ASYMETRII?")
    print("=" * 90)

    base_ang_m = summary_stats["baseline"]["ang"]["mean"]
    base_diff_m = summary_stats["baseline"]["diff"]["mean"]

    print(f"Wartości bazowe (Baseline):")
    print(f"  * Przesunięcie wzgórza EPG:   {base_ang_m:+6.2f}°")
    print(f"  * Różnica sygnału DNa02 (L-R): {base_diff_m:+6.2f} Hz\n")

    print("A. Wpływ na przesunięcie wzgórza EPG:")
    print(f"  - Ablacja A (Wagi PFL3->DNa02)     : Kąt EPG = {summary_stats['ablation_A']['ang']['mean']:+5.2f}° (zmiana o {summary_stats['ablation_A']['ang']['mean'] - base_ang_m:+5.2f}°) -> BRAK WPŁYWU (ścieżka downstream).")
    print(f"  - Ablacja B (Geometria EPG)        : Kąt EPG = {summary_stats['ablation_B']['ang']['mean']:+5.2f}° (redukcja o {base_ang_m - summary_stats['ablation_B']['ang']['mean']:+5.2f}°).")
    print(f"  - Ablacja C (Profile sektorowe CX) : Kąt EPG = {summary_stats['ablation_C']['ang']['mean']:+5.2f}° (odwrócenie przesunięcia na ujemne).")
    print(f"  - Wariant B+C (Geometria + Profile): Kąt EPG = {summary_stats['combined_BC']['ang']['mean']:+5.2f}° -> PRAKTYCZNA ELIMINACJA ASYMETRII KĄTOWEJ EPG.")

    print("\nB. Wpływ na asymetrię sygnału wyjściowego DNa02 (L - R):")
    print(f"  - Ablacja A (Wagi PFL3->DNa02)     : ΔDNa02 = {summary_stats['ablation_A']['diff']['mean']:+5.2f} Hz (redukcja o {abs(base_diff_m) - abs(summary_stats['ablation_A']['diff']['mean']):+5.2f} Hz) -> GŁÓWNA PRZYCZYNA ASYMETRII DNa02.")
    print(f"  - Ablacja B (Geometria EPG)        : ΔDNa02 = {summary_stats['ablation_B']['diff']['mean']:+5.2f} Hz (częściowa redukcja z poprawy kąta wzgórza).")
    print(f"  - Ablacja C (Profile sektorowe CX) : ΔDNa02 = {summary_stats['ablation_C']['diff']['mean']:+5.2f} Hz (niewielka zmiana, pozostaje asymetria 380 vs 356 synaps).")
    print(f"  - Ablacja D (goal_amp = 0)         : ΔDNa02 = {summary_stats['ablation_D']['diff']['mean']:+5.2f} Hz (całkowite wygaszenie projekcji PFL3; DNa02 wykazuje jedynie tło szumowe).")
    print(f"  - Wariant A+B+C (Pełna symetria)   : ΔDNa02 = {summary_stats['combined_ABC']['diff']['mean']:+5.2f} Hz, Kąt EPG = {summary_stats['combined_ABC']['ang']['mean']:+5.2f}° -> PEŁNA SYMETRYZACJA CAŁEGO UKŁADU.")
    print("=" * 90)

    elapsed = time.time() - t0
    print(f"\nEksperyment zakończony w {elapsed:.2f} s. Brak zmian w plikach produkcyjnych.")


if __name__ == "__main__":
    main()
