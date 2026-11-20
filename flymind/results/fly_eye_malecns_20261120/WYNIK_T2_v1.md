# T2 v1 — komórki zbliżania MaleCNS na oku flyvis: **FAILED (technicznie)** (20 XI 2026)

Liczby oka: flyvis (T1, T1b FAILED → hybryda wg PREREG_T2). Modele 000–002.

| wariant | AUC test (m0 / m1 / m2) | uwagi |
|---|---|---|
| LPLC2 full, prawdziwe | NaN / NaN / NaN | wszystkie 3 starty → NaN |
| LPLC2 full, potasowane | NaN / NaN / NaN | j.w. |
| LPLC2 bez LPi | 0,23 / 0,62 / 0,19 | |
| LPLC2 nieuczony (siły 1) | 0,27 / 0,35 / 0,18 | |
| LC4 full | 0,30 / 0,30 / 0,10 | |

K1–K3: niespełnione w żadnym modelu → **FAILED**.

## Przyczyny (diagnoza po wyniku)
1. **Błąd uprzęży:** komórki milkły (relu = 0, brak gradientu), potem stała czasowa LPi spadała < dt/2 → Euler eksplodował → NaN.
   Wybór startu porównywał NaN (`NaN < x` = False) → zostawał pierwszy start.
2. **Błąd uprzęży:** próg odczytu `a` mógł być ujemny — model uczył się „zbliżanie = MNIEJ aktywności”, a AUC liczone na
   surowej aktywności (stąd AUC trening 0,03 przy małej stracie).
3. **Wynik merytoryczny (opis):** szczyt napędu synaptycznego z KAŻDEGO typu wejścia oka do LPLC2 jest na zbiorze testowym
   wyższy dla ruchu kamery/przesuwanych obiektów niż dla zbliżania (AUC pojedynczych typów ≤ 0,5; T4/T5 0,17–0,23;
   suma 0,30, potasowane 0,26). Czyli liniowa suma wejść nie wystarczy — odrzucenie ruchu własnego musi zrobić hamowanie
   (LPi / dynamika), jak u prawdziwej muchy (Mauss 2015, Klapoetke 2017).
