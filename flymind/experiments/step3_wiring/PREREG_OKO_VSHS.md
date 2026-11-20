# Plan testu 2: oko + komórki VS/HS — spisany PRZED uruchomieniem, 20 XI 2026 (Adam wybrał „1: komórki VS/HS”)
Test 1 (PREREG_OKO_EMD.md) FAILED; diagnoza: zła scena + czułość na bardzo kontrastowe krawędzie (results/oko_emd_20261120/WYNIK.md).

## Zmiana w oku (jedna)
HS i VS u muchy: duże komórki płata bocznego zbierające ruch z całego oka (HS poziomy, VS pionowy). Tu: HS = średnia H
z całego kadru, VS = średnia V (ze znakiem). **Nasza hipoteza (nie znany obwód muchy):** ruch całego obrazu dzieli wyjście
LPLC2: out = LPLC2 / (1 + (|HS| + |VS|) / G0). G0 = średnia z 4 ramion najlepszej jednostki w scenie kalibracyjnej
(ziarno 24 100 900) w chwili θ = 37° — „cały obraz rusza się tak mocno jak krawędzie zbliżania → wyjście o połowę”.
OUT_FULL liczony od nowa tą samą procedurą co w teście 1 (już z VS/HS). Reszta oka bez zmian.

## Sceny (jak w teście 1 + poprawki)
Faktura 6× większa niż kadr i środek próbkowania w jej środku — tło nie może się skończyć (sprawdzane w kodzie).
Sceny 1–10 jak w teście 1 oraz: 11. **kamera po skosie** 50°/s; 12. **ciemne pole wjeżdża** z dołu 50°/s (jasność 5,
kamera stoi); 13. **zbliżanie w czasie ruchu kamery** — scena 1 przy pionowym ruchu kamery 20°/s.
Nowe ziarna 24 101 001–010; kąt 100°, 80 kl./s, σ = 3 jak wcześniej.

## Kryteria (PASS = wszystkie w ≥ 9 z 10)
K1 sceny 4–12: szczyt ≤ 0,25 × szczyt sceny 1. K2 strona (sceny 2, 3) jak w teście 1. K3 zapominanie (scena 9) jak w teście 1.
**K4 (nowe):** szczyt sceny 13 ≥ 0,5 × szczyt sceny 1 — VS/HS nie może „zabić” zbliżania, gdy ramię się rusza.
Tylko raport: to samo oko BEZ VS/HS na nowych scenach (czy VS/HS w ogóle coś daje). Po wyniku nic nie stroję.
