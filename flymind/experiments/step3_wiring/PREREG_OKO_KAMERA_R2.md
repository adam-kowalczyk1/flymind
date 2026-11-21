# P1b — oko v3 na NOWYM nagraniu oko_r2 (spisane PRZED nagraniem r2, 21 XI 2026)

## Skąd v3
P1 (oko v2 z testu 2) na oko_r1: FAILED (WYNIK.md). oko_r1 stało się **nagraniem roboczym**: na nim szukałem poprawek
(ok. 25 wariantów: odczyt ramion, zegar, rozdzielczość, opóźnienie, otoczenie, kontrola kontrastu, stała błony). Wybrana v3
(`oko_mucha.FlyEye3`): kontrola wzmocnienia kontrastu (σ 6 pól, ε 0,05), pola 5×5, opóźnienie detektora 20 ms, VS/HS jak w v2.
Stałe z oko_r1: OUT_FULL3 = 0,11096 (mediana szczytów 7 zbliżań → 1), G3 = 0,13140 (90. percentyl ruchu całego obrazu).
Wynik v3 na oko_r1 (roboczy, NIE test — oko_r1_v3_DEV.json): zbliżania 0,53–1,19; dłoń w poprzek 0,34–0,87; odsuwanie
0,11–0,15; obrót 0,16–0,33; pochylanie 0,13–0,61; zbliżanie w obrocie 0,20–0,23; światło 0,36–0,55; spokój 0,13; strony
zgodne (przy zamianie stron — kamera patrzyła na Adama). Sceny syntetyczne testu 2: PASS (`OKO=v3 oko_kamera.py --check`).

## Test: oko_r2 (nowe nagranie, ten sam scenariusz głosowy `nagraj_oko.py --out ~/Desktop/oko_r2`)
Oko v3 bez żadnych zmian, stałe jak wyżej. Ocena `OKO=v3 oko_kamera.py`. Jedno nagranie = jeden wynik.
**Kryteria główne** = te same K1–K5 co w P1 (PREREG_OKO_KAMERA.md) — żeby było porównanie. Na nagraniu roboczym v3 ich NIE
spełnia (K1, K4, K5), więc spodziewam się FAILED.
**Kryteria „użyteczne”** (niższa poprzeczka, wybrana PO obejrzeniu oko_r1 — świadomie, zapisuję to):
- U1: zbliżania ≥ 0,5 w ≥ 6 z 7 okien (mózg dostaje ≥ 20 mV).
- U2: kamera leży: mediana szczytów „w poprzek” + „odsuwanie” ≤ 0,5 × mediana zbliżań, a każde z tych okien < 1,0.
- U3: kamera w ręce: mediana „obrót” + „pochylanie” ≤ 0,5 × mediana zbliżań.
- U4: strony lewa/prawa zgodne w 4 / 4 przy tym samym przypisaniu co na oko_r1 (zamienione).
PASS „użyteczne” = U1–U4. Tylko raport: zbliżanie w obrocie (do P2 — kopia ruchu), światło, spokój.
Co dalej po wyniku: PASS „użyteczne” → v3 jako `--eye mucha3` w live_avoid (z `--flip` wg U4) i przejście do P2;
FAILED → opisuję, nie stroję na r2.
