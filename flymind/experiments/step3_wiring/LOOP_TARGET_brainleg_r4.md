# Krok 6 r4 — czy wynik r2/r3 przetrwa szum neuronów (cel zapisany PRZED testem, 16 XI 2026)

## Dlaczego
r2 i r3 liczyłem bez szumu (sieć deterministyczna, wyniki 0 / 100 %). Pytanie: czy ruch po dotyku, spokój bez dotyku
i podwójna dysocjacja zostają, gdy każdy neuron dostaje szum prądu.

## Zmiana
Tylko szum: `ALIFParams(noise=σ)`, σ = **2 mV** (standard projektu, jak V5) — główny; σ = **6 mV** — próba „stres”.
Nowe ziarno szumu w każdej próbie (`brainleg_noise.py`). Reszta jak r2/r3 (sonda dłoni, te same skrypty bez zmian).

## Trening (21421, 3 pozy, 9 par na Glu; σ 2 i 6) — NIE dowód
N: łokieć 9, nadgarstek 9, C stoi 15/15. Bez DNg15: łokieć 0, nadgarstek 9. Bez DNge078: łokieć 9, nadgarstek 0.
Oba Glu, oba σ. Największy ruch bez dotyku 0,006 rad (próg spoczynku 0,01).

## Test
Sceny `--seed 21631`, 6 póz, **raz**, `STEP6D_FINAL_TEST=1`. Ziarna szumu: 21 641 000 + 100·k (σ 2), 21 642 000 + 100·k (σ 6),
+1 na próbę. Przebiegi: {N, bez DNg15, bez DNge078} × Glu ±1 × σ {2, 6} = 12.

## Kryteria (`analyze_lesion.py` bez zmian, osobno dla każdego σ i Glu; prefiks te_s2 / te_s6)
LZ_1, LZ_2, LZ_3 jak w `LOOP_TARGET_brainleg_r3.md`. Wynik główny: σ = 2 mV. σ = 6 mV raportuję obok jako próbę obciążenia.

## Zastrzeżenia z góry
Szum prądu to model szumu, nie pomiar. Symulacja MuJoCo, bez prawdziwego robota.
