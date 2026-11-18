# Czujniki FSR402 na chwytaku SO-101 (projekt, 18 XI 2026)

`chwytak_czujniki.png` / `.blend`: chwytak (serwo + szczęka stała biała + ruchoma czarna, otwarta 0,6 rad) z siatek producenta
i 2× FSR402 tam, gdzie je proponuję. `export_gripper.py` liczy miejsca z geometrii (`.venv/bin/python hardware/gripper_sensors/export_gripper.py 0.6`
→ `gripper_mm.json`, niewersjonowany, do wczytania w Blenderze).

- **FSR 1 → A0, szczęka stała:** wewnętrzny schodek (ten, który przy zamykaniu dotyka pierwszy po samym czubku), środek ok. 30 mm od czubka.
- **FSR 2 → A1, szczęka ruchoma:** wewnętrzna ściana, środek 22 mm od czubka.
- Ogonki do tyłu, ku nadgarstkowi. Na polu czynnym gumowy krążek ~10 mm (nacisk w środek, mniej poślizgu).
- **Uwaga:** szczęki w tych miejscach mają tylko 13–15 mm wysokości, a folia FSR402 ma 18,3 mm (pole czynne 12,7 mm).
  Pole czynne się mieści, brzeg folii wystaje 2–3 mm. Nie zaginać go na krawędzi, tylko zostawić wystający.
Wymiary FSR402 z karty katalogowej (przybliżone dla ogonka). Ze sprzętem jeszcze niesprawdzone.
