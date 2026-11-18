# Test czujników (bez ramienia)

Sprawdza tylko, czy kamerka i 2 czujniki nacisku FSR402 w ogóle działają. Nic nie wysyła do ramienia SO-101.

1. **Kamerka:** podłącz ją do Maca, otwórz `test_czujnikow.html` w **Google Chrome** → „Włącz kamerkę” (zezwól na kamerę)
   → wybierz ją z listy → „Test zasłonięcia” i zasłoń obiektyw dłonią, gdy strona poprosi.
2. **Czujniki nacisku:** potrzebne Arduino i 2 oporniki 10 kΩ. Każdy czujnik: 5V → FSR → pin A0 (czujnik 1) / A1 (czujnik 2);
   z tego samego pinu opornik 10 kΩ do GND. W Arduino IDE otwórz `fsr_test/fsr_test.ino` i kliknij „Wgraj”.
   Potem na stronie: „Połącz z Arduino” → wybierz port → „Test krok po kroku” (nie dotykaj → naciskaj czujnik 1 → naciskaj czujnik 2).
3. Na dole strony pojawi się wynik: ✅ DZIAŁA albo ❌ NIE DZIAŁA z powodem. „Zapisz wynik” zapisuje plik do Pobranych.

Progi (te same co w modelu nerwów `flymind/experiments/step3_wiring/nerves.py`): spoczynek ≤ 60 zliczeń, nacisk ≥ 300 zliczeń
(ok. 0,8 N wg krzywej katalogowej), drugi czujnik przy nacisku pierwszego ≤ 30 % (inaczej kable zamienione/zwarte).
Program Arduino skompilowany 18 XI dla Uno, Nano, Uno R4 Minima i Uno R4 WiFi. Ze sprzętem jeszcze niesprawdzone.
