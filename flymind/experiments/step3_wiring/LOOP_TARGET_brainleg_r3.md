# Krok 6 r3 — wycięcie jednego szlaku (podwójna dysocjacja), cel zapisany PRZED testem, 16 XI 2026

## Pytanie
Czy to właśnie dwa szlaki z danych sterują dwoma stawami: BM→DNg15→łokieć i BM→DNge078→nadgarstek?
Przewidywanie: bez DNg15 łokieć stoi, a nadgarstek działa; bez DNge078 odwrotnie.

## Dlaczego nie rodzina B (zapisane jawnie)
Trening tasowań B (BM i DN jako osobne grupy; 21 100 006/007): ruch po dotyku zostaje (9/9), bo tasowanie prawie nie
rusza połączeń DN→pule (tylko 4 DN, brak krawędzi do zamiany o równej wadze; `explore_dn_targets.py`:
DNge078→nadgarstek +28/−1 vs +28/−0, DNg15→łokieć −17 bez zmian). B w tej sieci nie jest kontrolą szlaków — tylko reszty
sieci. Pokazuje, że ruch niosą szlaki, a nie pozostałe ~3000 neuronów; spokój bez dotyku zależy od reszty (B7: C stoi 0/9).
Dlatego zamiast B — bezpośrednie wycięcie szlaku (`brainleg_lesion.py`: zerowanie wyjść 2 neuronów).

## Trening (21421, 3 pozy, 9 par na Glu) — NIE dowód
Bez DNg15: łokieć 0/9, nadgarstek 9/9, C stoi 15/15. Bez DNge078: łokieć 9/9, nadgarstek 0/9, C stoi 15/15. Oba Glu.

## Test
Sceny `--seed 21891` (W: 21 891 000–049, C: 21 891 100–149), 6 póz, **raz**, `STEP6C_FINAL_TEST=1`, sonda dłoni jak r2.
Przebiegi: N nienaruszone (`brainleg_probe.py`), N bez DNg15, N bez DNge078 (`brainleg_lesion.py`); oba Glu; 6 przebiegów.

## Kryteria (`analyze_lesion.py`, osobno dla każdego Glu)
- LZ_1 (bez DNg15): łokieć ≤ 10 % par, nadgarstek ≥ 80 %, C stoi ≥ 95 %, utrata łokcia vs N istotna (McNemar, Holm ×2, p < 0,05).
- LZ_2 (bez DNge078): nadgarstek ≤ 10 %, łokieć ≥ 80 %, C stoi ≥ 95 %, utrata nadgarstka istotna (jw.).
- LZ_3 (N nienaruszone na tych scenach): łokieć i nadgarstek ≥ 80 %, C stoi ≥ 95 % (powtórzenie r2 na nowych scenach).

## Zastrzeżenia z góry
Szlaki wybrałem z danych sam; wycięcie w modelu pokazuje, że w TYM modelu ruch idzie tymi szlakami — nie, że mucha tak robi.
Sieć jest bez szumu, więc wynik może być bardzo równy (0 lub 100 %). Symulacja MuJoCo, bez prawdziwego robota.
