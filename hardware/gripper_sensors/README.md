# Czujniki FSR402 na chwytaku SO-101 (projekt, 18 XI 2026)

`chwytak_czujniki.png` / `.blend`: chwytak (serwo + szczęka stała biała + ruchoma czarna, otwarta 0,6 rad) z siatek producenta
i 2× FSR402 tam, gdzie je proponuję. `export_gripper.py` liczy miejsca z geometrii (`.venv/bin/python hardware/gripper_sensors/export_gripper.py 0.6`
→ `gripper_mm.json`, niewersjonowany, do wczytania w Blenderze).

- **FSR 1 → A0, szczęka stała:** wewnętrzny schodek (ten, który przy zamykaniu dotyka pierwszy po samym czubku), środek ok. 30 mm od czubka.
- **FSR 2 → A1, „dłoń” (zmiana 19 XI):** płaski spód serwa między nasadami szczęk (ściana zwrócona ku czubkom, ok. 42 × 32 mm),
  środek ok. 7 mm od krawędzi po stronie szczęki stałej ku środkowi ściany, czyli na środku ściany. Ogonek w stronę szczęki stałej
  (ona się nie rusza, więc kabelek nie zostanie przytrzaśnięty).
  Dlaczego: w symulacji dotyk dłoni trafia do szczecinek głowy muchy i uruchamia cofnięcie ramienia; dotyk szczęk trafia do
  szczecinek nogi i daje dociśnięcie. Z czujnikami na obu szczękach ramię nie unikało ręki w żadnej z 15 prób
  (`flymind/results/step3_20261115/avoid_r1/REPORT_20261119.md`). Miejsce dłoni nie jest sprawdzone na prawdziwym ramieniu.
- Pierwotny projekt FSR 2 (szczęka ruchoma, wewnętrzna ściana, 22 mm od czubka) jest w `export_gripper.py` / `gripper_mm.json`.
- Ogonek FSR 1 do tyłu, ku nadgarstkowi. Na polu czynnym gumowy krążek ~10 mm (nacisk w środek, mniej poślizgu).
- **Uwaga:** szczęki w tych miejscach mają tylko 13–15 mm wysokości, a folia FSR402 ma 18,3 mm (pole czynne 12,7 mm).
  Pole czynne się mieści, brzeg folii wystaje 2–3 mm. Nie zaginać go na krawędzi, tylko zostawić wystający.
Wymiary FSR402 z karty katalogowej (przybliżone dla ogonka). Ze sprzętem jeszcze niesprawdzone.
