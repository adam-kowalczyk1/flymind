#!/usr/bin/env python3
"""
bio2/test_openloop_cx.py

Minimalny, samodzielny test open-loop podsieci CX -> PFL3 -> DNa02 / DNa01 w ConnectomeSNN.
Bada odpowiedź modelu na syntetyczny prąd kątowy 'cue' wstrzykiwany do EPG.
Działa całkowicie w pamięci RAM, bez MuJoCo, kamery, geometrii robota i serwomechanizmów.

UWAGA METODOLOGICZNA:
Ten test NIE bada biologicznego przetwarzania obrazu ani zintegrowanego odruchu wzrokowego.
Bada wyłącznie właściwości dynamiczne wyciętego atraktora sieciowego pod wpływem syntetycznego
profilu prądu depolaryzującego.
"""

import math
import os
import sys
import time
import numpy as np

# Upewnienie się, że moduły z katalogu bio2 są widoczne
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from brain import Brain
from snn import ConnectomeSNN


# -----------------------------------------------------------------------------
# Konfiguracja i parametry eksperymentu (jawnie parametryzowane)
# -----------------------------------------------------------------------------
CFG = dict(
    n_angles=16,             # liczba dyskretnych kątów na pełnym okręgu [-pi, +pi)
    t_transient_ms=200,      # czas stabilizacji (stan przejściowy, 20 kroków step10)
    t_measure_ms=300,        # okno pomiaru stacjonarnego (30 kroków step10)
    seeds=[0, 1, 2, 3, 4],   # ziarna losowości do oceny wariancji szumu
    bump_min_rate_hz=5.0,    # próg minimalnej aktywności EPG dla wiarygodnego wzgórza
    bump_min_coh=0.20,       # próg minimalnego skupienia (koherencji fazowej)
)


def validate_api_and_structure(b: Brain):
    """Walidacja wstępna API, struktury populacji i skończoności stanów."""
    print("=" * 80)
    print("1. WALIDACJA STRUKTURY SIECI I API")
    print("=" * 80)
    print(f"Liczba neuronów w modelu Brain: {b.N} (oczekiwano 220)")
    assert b.N == 220, f"Nieoczekiwana liczba neuronów: {b.N} != 220"

    expected_groups = ["EPG", "PFL3_L", "PFL3_R", "DNa02_L", "DNa02_R", "DNa01_L", "DNa01_R"]
    for grp in expected_groups:
        assert grp in b.groups, f"Brak oczekiwanej grupy w b.groups: {grp}"
        count = len(b.groups[grp])
        print(f"  - Grupa {grp:<10}: {count:2d} neuron(ów), indeksy: {b.groups[grp].tolist()}")

    # Sprawdzenie pojedynczego kroku zerowego
    b.reset()
    spk0 = b.step10(cue=0.0)
    assert spk0.shape == (10, b.N), f"Błędny kształt tablicy iglic: {spk0.shape}"
    assert np.isfinite(b.rate).all(), "Wykryto NaN/Inf w wektorze b.rate po kroku 0!"
    print("  -> Wyniki wstępnego kroku są skończone (brak NaN/Inf). API sprawne.\n")


def measure_single_condition(b: Brain, cue, t_trans_ms: int, t_meas_ms: int):
    """
    Wykonuje stabilizację i pomiar dla zadanego kąta cue.
    Zwraca słownik z surowymi zliczeniami iglic, przefiltrowanymi częstościami oraz stanem EPG.
    """
    n_trans_steps = t_trans_ms // 10
    n_meas_steps = t_meas_ms // 10

    # 1. Faza przejściowa (stabilizacja atraktora)
    for _ in range(n_trans_steps):
        b.step10(cue=cue, u=0.0, rest=False)

    # 2. Faza pomiarowa (rejestracja iglic i próbek rate)
    spk_chunks = []
    rate_samples = []

    for _ in range(n_meas_steps):
        spk = b.step10(cue=cue, u=0.0, rest=False)
        spk_chunks.append(spk)
        rate_samples.append(b.rate.copy())

    # Sklejanie buforów: spk_all ma kształt (T_meas_total_ms, N)
    spk_all = np.concatenate(spk_chunks, axis=0)
    rate_arr = np.array(rate_samples)  # (n_meas_steps, N)

    # Wyciąganie populacji
    idx_dna02_l = b.groups["DNa02_L"]
    idx_dna02_r = b.groups["DNa02_R"]
    idx_dna01_l = b.groups["DNa01_L"]
    idx_dna01_r = b.groups["DNa01_R"]

    # A. Surowe częstości ze zliczeń iglic w całym oknie: sum(spk) / T_sec
    dur_sec = spk_all.shape[0] / 1000.0
    raw_spike_dna02_l = float(spk_all[:, idx_dna02_l].sum() / dur_sec)
    raw_spike_dna02_r = float(spk_all[:, idx_dna02_r].sum() / dur_sec)
    raw_spike_dna01_l = float(spk_all[:, idx_dna01_l].sum() / dur_sec)
    raw_spike_dna01_r = float(spk_all[:, idx_dna01_r].sum() / dur_sec)

    # B. Średnie z przefiltrowanej zmiennej self.rate
    cont_dna02_l = float(rate_arr[:, idx_dna02_l].mean())
    cont_dna02_r = float(rate_arr[:, idx_dna02_r].mean())
    cont_dna01_l = float(rate_arr[:, idx_dna01_l].mean())
    cont_dna01_r = float(rate_arr[:, idx_dna01_r].mean())

    # C. Odczyt wzgórza EPG przez Brain.bump()
    raw_ang, bump_coh, bump_rate = b.bump(spk_all)

    # Ocena wiarygodności odczytu kąta EPG
    is_reliable = (bump_rate >= CFG["bump_min_rate_hz"]) and (bump_coh >= CFG["bump_min_coh"])

    return dict(
        raw_spike=dict(
            dna02_l=raw_spike_dna02_l,
            dna02_r=raw_spike_dna02_r,
            diff_dna02=raw_spike_dna02_l - raw_spike_dna02_r,
            dna01_l=raw_spike_dna01_l,
            dna01_r=raw_spike_dna01_r,
            diff_dna01=raw_spike_dna01_l - raw_spike_dna01_r,
        ),
        cont_rate=dict(
            dna02_l=cont_dna02_l,
            dna02_r=cont_dna02_r,
            diff_dna02=cont_dna02_l - cont_dna02_r,
            dna01_l=cont_dna01_l,
            dna01_r=cont_dna01_r,
            diff_dna01=cont_dna01_l - cont_dna01_r,
        ),
        epg=dict(
            raw_angle_rad=raw_ang,
            coherence=bump_coh,
            rate_hz=bump_rate,
            reliable=is_reliable,
            angle_deg=math.degrees(raw_ang),
        )
    )


def run_baseline_control(seed=0):
    """Faza A: Kontrola bazowa (spoczynek bez bodźca oraz bodziec w zerze)."""
    print("=" * 80)
    print("2. FAZA A: KONTROLA BAZOWA")
    print("=" * 80)
    b = Brain(seed=seed)

    # A1: Brak bodźca (cue = None)
    b.reset()
    b.net.rng = np.random.default_rng(seed)
    res_none = measure_single_condition(b, cue=None, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])

    # A2: Bodziec centralny (cue = 0.0 rad)
    b.reset()
    b.net.rng = np.random.default_rng(seed)
    res_zero = measure_single_condition(b, cue=0.0, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])

    print("Warunek A1 (Brak bodźca, cue=None):")
    print(f"  EPG Rate: {res_none['epg']['rate_hz']:5.1f} Hz | Skupienie: {res_none['epg']['coherence']:5.3f} | Wiarygodny kąt: {res_none['epg']['reliable']}")
    print(f"  DNa02: L={res_none['cont_rate']['dna02_l']:5.1f} Hz, R={res_none['cont_rate']['dna02_r']:5.1f} Hz, L-R={res_none['cont_rate']['diff_dna02']:+6.1f} Hz")
    print(f"  DNa01: L={res_none['cont_rate']['dna01_l']:5.1f} Hz, R={res_none['cont_rate']['dna01_r']:5.1f} Hz, L-R={res_none['cont_rate']['diff_dna01']:+6.1f} Hz")

    print("\nWarunek A2 (Bodziec centralny na wprost, cue=0.0 rad):")
    print(f"  EPG Rate: {res_zero['epg']['rate_hz']:5.1f} Hz | Skupienie: {res_zero['epg']['coherence']:5.3f} | Kąt: {res_zero['epg']['angle_deg']:+6.1f}° (wiarygodny: {res_zero['epg']['reliable']})")
    print(f"  DNa02: L={res_zero['cont_rate']['dna02_l']:5.1f} Hz, R={res_zero['cont_rate']['dna02_r']:5.1f} Hz, L-R={res_zero['cont_rate']['diff_dna02']:+6.1f} Hz")
    print(f"  DNa01: L={res_zero['cont_rate']['dna01_l']:5.1f} Hz, R={res_zero['cont_rate']['dna01_r']:5.1f} Hz, L-R={res_zero['cont_rate']['diff_dna01']:+6.1f} Hz")
    print("  -> Wrodzone przesunięcie zera (L-R w punkcie 0°) wynika z asymetrii konektomu.\n")
    return res_none, res_zero


def run_deterministic_repeatability_test(seed=42):
    """Faza C: Sprawdzenie determinizmu przy identycznym ziarnie."""
    print("=" * 80)
    print("3. SPRAWDZENIE DETERMINIZMU PRZY IDENTYCZNYM SEEDZIE")
    print("=" * 80)
    test_cue = math.radians(45.0)

    # Przebieg 1
    b1 = Brain(seed=seed)
    b1.reset()
    b1.net.rng = np.random.default_rng(seed)
    r1 = measure_single_condition(b1, cue=test_cue, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])

    # Przebieg 2
    b2 = Brain(seed=seed)
    b2.reset()
    b2.net.rng = np.random.default_rng(seed)
    r2 = measure_single_condition(b2, cue=test_cue, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])

    diff_dna02 = abs(r1["cont_rate"]["diff_dna02"] - r2["cont_rate"]["diff_dna02"])
    diff_bump = abs(r1["epg"]["raw_angle_rad"] - r2["epg"]["raw_angle_rad"])

    print(f"Test dla cue = +45.0° (seed={seed}):")
    print(f"  Przebieg 1: ΔDNa02 = {r1['cont_rate']['diff_dna02']:+7.3f} Hz, Bump = {r1['epg']['angle_deg']:+6.2f}°")
    print(f"  Przebieg 2: ΔDNa02 = {r2['cont_rate']['diff_dna02']:+7.3f} Hz, Bump = {r2['epg']['angle_deg']:+6.2f}°")
    print(f"  Różnica bezwzględna: |Δ1 - Δ2| = {diff_dna02:.6e} Hz, |Bump1 - Bump2| = {diff_bump:.6e} rad")

    assert diff_dna02 < 1e-9, f"Brak determinizmu w modelu: różnica {diff_dna02}"
    print("  -> Determinizm przy identycznym ziarnie POTWIERDZONY w 100%.\n")


def run_angular_sweep(seed=0):
    """Faza B: Skan dyskretnych kątów po pełnym okręgu."""
    print("=" * 80)
    print(f"4. FAZA B: SKAN KĄTÓW STATYCZNYCH (seed={seed}, {CFG['n_angles']} punktów)")
    print("=" * 80)
    b = Brain(seed=seed)

    angles = np.linspace(-np.pi, np.pi, CFG["n_angles"], endpoint=False)
    results = []

    header = (
        f"{'Kąt [°]':>8} | {'EPG [°]':>8} {'Wiaryg.':>7} {'Skup.':>6} {'Rate':>6} | "
        f"{'DNa02 L':>7} {'R':>7} {'ΔDNa02':>8} | {'DNa01 L':>7} {'R':>7} {'ΔDNa01':>8}"
    )
    print(header)
    print("-" * len(header))

    for ang in angles:
        # Reset stanu i generatora przed każdym kątem
        b.reset()
        b.net.rng = np.random.default_rng(seed)
        m = measure_single_condition(b, cue=ang, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])
        results.append((ang, m))

        ang_deg = math.degrees(ang)
        epg_deg_str = f"{m['epg']['angle_deg']:+6.1f}" if m['epg']['reliable'] else "   NaN"
        rel_str = "TAK" if m['epg']['reliable'] else "NIE"

        line = (
            f"{ang_deg:+8.1f} | {epg_deg_str:>8} {rel_str:>7} {m['epg']['coherence']:6.3f} {m['epg']['rate_hz']:6.1f} | "
            f"{m['cont_rate']['dna02_l']:7.1f} {m['cont_rate']['dna02_r']:7.1f} {m['cont_rate']['diff_dna02']:+8.1f} | "
            f"{m['cont_rate']['dna01_l']:7.1f} {m['cont_rate']['dna01_r']:7.1f} {m['cont_rate']['diff_dna01']:+8.1f}"
        )
        print(line)

    print("-" * len(header))
    return results


def run_multiseed_analysis(seeds):
    """Faza D: Ocena wariancji odpowiedzi po niezależnych ziarnach szumu."""
    print("=" * 80)
    print(f"5. FAZA D: OCENA STOCHASTYKI NA {len(seeds)} ZIARNACH LOSOWOŚCI")
    print("=" * 80)

    test_angles = [math.radians(-90.0), math.radians(-45.0), 0.0, math.radians(45.0), math.radians(90.0)]
    print(f"{'Kąt [°]':>8} | {'Śr. ΔDNa02 [Hz]':>16} {'SD [Hz]':>10} | {'Śr. ΔDNa01 [Hz]':>16} {'SD [Hz]':>10} | {'Korelacja DNa01/02':>18}")
    print("-" * 88)

    for ang in test_angles:
        d02_diffs = []
        d01_diffs = []
        for s in seeds:
            b = Brain(seed=s)
            b.reset()
            b.net.rng = np.random.default_rng(s)
            m = measure_single_condition(b, cue=ang, t_trans_ms=CFG["t_transient_ms"], t_meas_ms=CFG["t_measure_ms"])
            d02_diffs.append(m["cont_rate"]["diff_dna02"])
            d01_diffs.append(m["cont_rate"]["diff_dna01"])

        mean_02, sd_02 = np.mean(d02_diffs), np.std(d02_diffs)
        mean_01, sd_01 = np.mean(d01_diffs), np.std(d01_diffs)

        # Korelacja między realizacjami szumu
        if sd_02 > 1e-6 and sd_01 > 1e-6:
            corr = float(np.corrcoef(d02_diffs, d01_diffs)[0, 1])
            corr_str = f"{corr:+7.3f}"
        else:
            corr_str = "    N/A"

        ang_deg = math.degrees(ang)
        print(f"{ang_deg:+8.1f} | {mean_02:+16.2f} {sd_02:10.2f} | {mean_01:+16.2f} {sd_01:10.2f} | {corr_str:>18}")

    print("-" * 88)


def fit_harmonic_model_helper(results):
    """Pomocnicze dopasowanie harmoniczne (1. rząd Fouriera): Δr = a0 + c1*sin(θ) + c2*cos(θ)."""
    angles = np.array([r[0] for r in results])
    y_02 = np.array([r[1]["cont_rate"]["diff_dna02"] for r in results])
    y_01 = np.array([r[1]["cont_rate"]["diff_dna01"] for r in results])

    # Macierz planu dla liniowego dopasowania harmonicznego
    X = np.column_stack([np.ones_like(angles), np.sin(angles), np.cos(angles)])
    c02, _, _, _ = np.linalg.lstsq(X, y_02, rcond=None)
    c01, _, _, _ = np.linalg.lstsq(X, y_01, rcond=None)

    amp_02 = math.sqrt(c02[1]**2 + c02[2]**2)
    phase_02_deg = math.degrees(math.atan2(c02[2], c02[1]))

    amp_01 = math.sqrt(c01[1]**2 + c01[2]**2)
    phase_01_deg = math.degrees(math.atan2(c01[2], c01[1]))

    print("\n" + "=" * 80)
    print("6. POMOCNICZY RAPORT DOPASOWANIA HARMONICZNEGO (BEZ PROGÓW DYSKWALIFIKUJĄCYCH)")
    print("=" * 80)
    print(f"Kanał DNa02: Średnia a0 = {c02[0]:+5.2f} Hz | Amplituda A = {amp_02:5.2f} Hz | Faza phi = {phase_02_deg:+6.1f}°")
    print(f"Kanał DNa01: Średnia a0 = {c01[0]:+5.2f} Hz | Amplituda A = {amp_01:5.2f} Hz | Faza phi = {phase_01_deg:+6.1f}°")
    print("  -> Znak i faza pokazują kierunek komendy skrętu (komparator kątowy EPG <-> PFL3).")


def print_methodological_disclaimers():
    """Wypisanie ostrzeżeń o ograniczeniach modelu i interpretacji naukowej."""
    print("\n" + "=" * 80)
    print("7. OGRANICZENIA NAUKOWE I METODOLOGICZNE WYNIKÓW")
    print("=" * 80)
    print("1. Wejście 'cue' jest syntetycznym prądem wstrzykiwanym numerycznie do komórek EPG,")
    print("   a NIE wynikiem biologicznego przetwarzania siatkówkowego ani optokinetycznego.")
    print("2. Wagi wewnątrz kompleksu centralnego (CX) pochodzą ze zsyntetyzowanego profilu")
    print("   uśrednionego po 16 sektorach, a NIE z surowego, asymetrycznego konektomu EM.")
    print("3. Połączenia PFL3 -> DNa01 są programową kopią PFL3 -> DNa02 (dna01_frac=1.0).")
    print("4. Adaptacja ALIF w neuronach CX została trwale wyzerowana w kodzie (b_a[cx] = 0.0).")
    print("5. Wynik ten demonstruje działanie algorytmicznego komparatora kątowego SNN,")
    print("   a nie behawioralnego sterowania robotem w zamkniętej pętli sensorycznej.")
    print("=" * 80 + "\n")


def main():
    t0 = time.time()
    b = Brain(seed=0)

    # 1. Sprawdzenie spójności modelu
    validate_api_and_structure(b)

    # 2. Kontrola bazowa
    run_baseline_control(seed=0)

    # 3. Sprawdzenie determinizmu
    run_deterministic_repeatability_test(seed=42)

    # 4. Skan kątowy
    results = run_angular_sweep(seed=0)

    # 5. Badanie odporności na szum
    run_multiseed_analysis(seeds=CFG["seeds"])

    # 6. Analiza harmoniczna
    fit_harmonic_model_helper(results)

    # 7. Ograniczenia
    print_methodological_disclaimers()

    elapsed = time.time() - t0
    print(f"Test zakończony pomyślnie w {elapsed:.2f} s. Brak zmian w plikach źródłowych modelu.")


if __name__ == "__main__":
    main()
