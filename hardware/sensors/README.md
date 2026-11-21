# Test czujników (bez ramienia)

Sprawdza tylko, czy kamerka i 2 czujniki nacisku FSR402 w ogóle działają. Nic nie wysyła do ramienia SO-101.

1. **Kamerka:** podłącz ją do Maca, otwórz `test_czujnikow.html` w **Google Chrome** → „Włącz kamerkę” (zezwól na kamerę)
   → wybierz ją z listy → „Test zasłonięcia” i zasłoń obiektyw dłonią, gdy strona poprosi.
2. **Czujniki nacisku:** potrzebne Arduino i 2 oporniki 10 kΩ (albo 5,1 / 4,7 kΩ — wybór na stronie). Każdy czujnik: 5V → FSR → pin A0
   (czujnik 1, szczęka stała) / A1 (czujnik 2, „dłoń” = spód serwa między szczękami, zmiana 19 XI); z tego samego pinu opornik do GND (rysunek na płytce stykowej: `plytka_stykowa.png`). W Arduino IDE otwórz `fsr_test/fsr_test.ino` i kliknij „Wgraj”.
   Potem na stronie: „Połącz z Arduino” → wybierz port → „Test krok po kroku” (nie dotykaj → naciskaj czujnik 1 → naciskaj czujnik 2).
3. Na dole strony pojawi się wynik: ✅ DZIAŁA albo ❌ NIE DZIAŁA z powodem. „Zapisz wynik” zapisuje plik do Pobranych.

Progi (te same co w modelu nerwów `flymind/experiments/step3_wiring/nerves.py`): spoczynek ≤ 60 zliczeń, nacisk ≥ 300 zliczeń
(ok. 0,8 N wg krzywej katalogowej), drugi czujnik przy nacisku pierwszego ≤ 30 % (inaczej kable zamienione/zwarte).
Program Arduino skompilowany 18 XI dla Uno, Nano, Uno R4 Minima i Uno R4 WiFi. Ze sprzętem jeszcze niesprawdzone.

## Bez płytki stykowej (21 XI)
Te same 4 elementy: 2 × FSR, 2 oporniki (te same co na płytce; `--r-fix` w programie musi się zgadzać). FSR i opornik nie mają biegunów.
Co ma się stykać (4 węzły):
1. **5V** → nóżka FSR 1 **i** nóżka FSR 2 (rozgałęzienie „Y”, bo pin 5V jest jeden).
2. druga nóżka FSR 1 + nóżka opornika R1 + kabel do **A0**.
3. druga nóżka FSR 2 + nóżka opornika R2 + kabel do **A1**.
4. druga nóżka R1 → **GND**, druga nóżka R2 → **inny pin GND** (Uno ma 3 piny GND, więc tu rozgałęzienie niepotrzebne).

Węzły 1–3: lutowanie + koszulka termokurczliwa albo szybkozłączki (np. WAGO 221 na 3 przewody). Nie lutuj przy samym czujniku,
bo folia się topi; lutuj na kablu lub złączce. Kable przypnij do ramienia opaskami; ogonek FSR nie może się zginać przy polu czynnym.
Sprawdzenie: `fsr_test.ino` + „Test krok po kroku” na `test_czujnikow.html` (spoczynek ≤ 60, nacisk ≥ 300).
