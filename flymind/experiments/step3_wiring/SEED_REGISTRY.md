# Rejestr ziaren — krok 3 (większa sieć z danych + sprawiedliwe tasowania)

Zakres zarezerwowany: **21 000 000 – 21 999 999** (sprawdzone 2026-11-15: brak w innych SEED_REGISTRY.md pod flymind/;
najwyższe wcześniej użyte 20 999 999). Wpis zawsze PRZED użyciem.

| Ziarna | Użycie | Data | Status |
|---|---|---|---|
| 21 100 001 – 21 100 005 | EKSPLORACJA: tasowania swobodne (równa waga) sieci „pre” — bez robota i w pętli treningowej | 2026-11-15 | w użyciu |
| 21 100 006 – 21 100 010 | EKSPLORACJA: tasowania zachowujące warstwy sieci „pre” — bez robota i w pętli treningowej | 2026-11-15 | w użyciu |
| 21 101 000 – 21 101 449 | TRENING: sceny `--seed 21101` (45 przedmiotów × 1 poza) | 2026-11-15 | w użyciu |
| 21 201 000 – 21 201 449 | TEST: sceny `--seed 21201` (45 przedmiotów × 3 pozy = 135) — RAZ | 2026-11-15 | zarezerwowane |
| 21 210 001 – 21 210 005 | TEST: tasowania swobodne S1–S5 | 2026-11-15 | zarezerwowane |
| 21 220 001 – 21 220 005 | TEST: tasowania zachowujące warstwy L1–L5 | 2026-11-15 | zarezerwowane |
| 21 299 998, 21 299 999 | bootstrap przedziałów ufności (Glu −1, Glu +1) | 2026-11-15 | zarezerwowane |
| 21 230 001 – 21 230 020 | H-cisza (bez robota): 20 tasowań swobodnych | 2026-11-15 | zarezerwowane |
| 21 240 001 – 21 240 020 | H-cisza (bez robota): 20 tasowań zachowujących warstwy | 2026-11-15 | zarezerwowane |
| 21 100 001 – 21 100 010 (dopisek) | te same tasowania eksploracyjne użyte także w `explore_specificity.py` (bez robota: wybiórczość noga→noga) | 2026-11-15 | w użyciu |
| 21 250 001 – 21 250 020 | H-W: 20 tasowań swobodnych (bez robota) | 2026-11-15 | zarezerwowane |
| 21 260 001 – 21 260 020 | H-W: 20 tasowań zachowujących warstwy | 2026-11-15 | zarezerwowane |
| 21 270 001 – 21 270 020 | H-W: 20 tasowań zachowujących warstwy i przynależność do nóg | 2026-11-15 | zarezerwowane |
| 21 100 010 (dopisek) | próba dymna rodziny G (jedno tasowanie, wynik nie liczy się do testu) | 2026-11-15 | w użyciu |
| 21 301 000 – 21 301 449 | TEST r2 (limit 10 s): sceny `--seed 21301` (135 prób) — RAZ; bootstrap: te same ziarna RNG co r1 (21 299 998/999) | 2026-11-15 | zarezerwowane |
| 21 401 000 – 21 401 449 | KROK 4 (odruchy) TRENING / uruchamianie: sceny `--seed 21401` (walec × 5 materiałów × pozy) | 2026-11-15 | w użyciu |
| 21 100 001 – 21 100 010 (dopisek) | tasowania eksploracyjne także w treningu kroku 4 (F: 001–005, L: 006–010, G: 006–010 z grupami nóg) | 2026-11-15 | w użyciu |
| 21 501 000 – 21 501 149 | KROK 4 TEST: sceny `--seed 21501` (W: 000–049, C: 100–149; 6 póz) — RAZ | 2026-11-15 | zarezerwowane |
| 21 510 001 – 005 / 21 520 001 – 005 / 21 530 001 – 005 | KROK 4 TEST: tasowania F / L / G | 2026-11-15 | zarezerwowane |
| 21 401 000 – 21 401 449 (dopisek) | te same sceny treningowe także w kroku 5 (nadgarstek: `reflex5.py`) | 2026-11-15 | w użyciu |
| 21 100 001 – 21 100 010 (dopisek) | tasowania eksploracyjne także w treningu kroku 5 (F: 001–002, L: 006–007, B: 006–007) | 2026-11-15 | w użyciu |
| 21 701 000 – 21 701 149 | KROK 5 TEST (nadgarstek): sceny `--seed 21701` (W: 000–049, C: 100–149; 6 póz) — RAZ | 2026-11-16 | zarezerwowane |
| 21 710 001 – 005 / 21 720 001 – 005 | KROK 5 TEST: tasowania F / L | 2026-11-16 | zarezerwowane |
| 21 411 000 – 21 411 449 | KROK 5b TRENING (nadgarstek, próg F_ON 3 N): sceny `--seed 21411`, pozy 0–2 | 2026-11-16 | zarezerwowane (trening) |
| 21 411 001 – 21 411 005 / 21 412 001 – 21 412 005 | KROK 5b TRENING: tasowania F / L (eksploracja) | 2026-11-16 | zarezerwowane (trening) |
| 21 801 000 – 21 801 149 | KROK 5b TEST (nadgarstek, F_ON 3 N): sceny `--seed 21801` (W: 000–049, C: 100–149; 6 póz) — RAZ | 2026-11-16 | zarezerwowane |
| 21 810 001 – 005 / 21 820 001 – 005 | KROK 5b TEST: tasowania F / L | 2026-11-16 | zarezerwowane |
| 21 910 001 – 020 / 21 920 001 – 020 / 21 930 001 – 020 | SPRAWA 2 TEST dawki (bez robota, `dose_test.py`, cel `LOOP_TARGET_dose_r1.md`): tasowania F / L / G, oba Glu — RAZ | 2026-11-16 | zarezerwowane |
| 21 421 000 – 21 421 449 | KROK 6 TRENING (dwa szlaki głowa→noga, `brainleg.py`): sceny `--seed 21421`, pozy 0–2; tasowania eksploracyjne 21 100 001 (F) i 21 100 006 (L) | 2026-11-16 | w użyciu (trening) |
| 21 701 000 – 21 701 149 (zużyte) | KROK 5 TEST: wykonany 16 XI, 22 sieci — wynik w audit_log_step3_20261115.md (wiersz przywrócony 16 XI: zginął przy zapisie pliku przez drugą sesję ze starszej kopii) | 2026-11-16 | ZUŻYTE |
| 21 801 000 – 21 801 149 (zużyte) | KROK 5b TEST (F_ON 3 N): wykonany 16 XI, 22 sieci — wynik w audit_log_step3_20261115.md (wiersz przywrócony 16 XI, jw.) | 2026-11-16 | ZUŻYTE |
| 21 831 000 – 21 831 149 | KROK 6 TEST (dwa szlaki głowa→noga, `brainleg.py`, cel `LOOP_TARGET_brainleg_r1.md`): sceny `--seed 21831` (W: 000–049, C: 100–149; 6 póz) — RAZ | 2026-11-16 | zarezerwowane |
| 21 840 001 – 005 / 21 850 001 – 005 | KROK 6 TEST: tasowania F / L | 2026-11-16 | zarezerwowane |
| 21 831 000 – 21 831 149, 21 840 001 – 005, 21 850 001 – 005 (zużyte) | KROK 6 TEST: wykonany 16 XI 11:41–11:51, 22 sieci — wynik w audit_log_step3_20261115.md (kroki 54–56) | 2026-11-16 | ZUŻYTE |
| 21 421 000 – 21 421 449 (dopisek) | KROK 6 r2 TRENING i eksploracja (sonda dłoni, `brainleg_probe.py`, `explore_slick.py`): te same sceny treningowe; tasowania eksploracyjne 21 100 001 (F), 21 100 006 (L) | 2026-11-16 | w użyciu (trening) |
| 21 861 000 – 21 861 149 | KROK 6 r2 TEST (sonda dłoni, `brainleg_probe.py`, cel `LOOP_TARGET_brainleg_r2.md`): sceny `--seed 21861` (W: 000–049, C: 100–149; 6 póz) — RAZ | 2026-11-16 | zarezerwowane |
| 21 870 001 – 005 / 21 880 001 – 005 | KROK 6 r2 TEST: tasowania F / L | 2026-11-16 | zarezerwowane |
| 21 861 000 – 21 861 149, 21 870 001 – 005, 21 880 001 – 005 (zużyte) | KROK 6 r2 TEST: wykonany 16 XI 12:34–12:44, 22 sieci — wynik w audit_log_step3_20261115.md (kroki 62–63) | 2026-11-16 | ZUŻYTE |
| 21 100 006 – 21 100 007 (dopisek) | KROK 6 r3 TRENING: tasowania B (BM i DN jako osobne grupy) na scenach treningowych 21 421 xxx, `brainleg_probe_b.py` | 2026-11-16 | w użyciu (trening) |
| 21 421 000 – 21 421 449 (dopisek) | KROK 6 r3 TRENING: wycięcie szlaku (`brainleg_lesion.py`, d15 / d78) na scenach treningowych | 2026-11-16 | w użyciu (trening) |
| 21 891 000 – 21 891 149 | KROK 6 r3 TEST (wycięcie szlaku, `brainleg_lesion.py` + `brainleg_probe.py`, cel `LOOP_TARGET_brainleg_r3.md`): sceny `--seed 21891`, 6 póz — RAZ | 2026-11-16 | zarezerwowane |
| 21 891 000 – 21 891 149 (zużyte) | KROK 6 r3 TEST: wykonany 16 XI 12:53–12:56, 6 przebiegów — wynik w audit_log_step3_20261115.md (krok 68) | 2026-11-16 | ZUŻYTE |
| 21 601 000 – 21 602 999 | KROK 6 r4 TRENING: ziarna szumu neuronów (`brainleg_noise.py`; baza przebiegu = 21 601 000 / 21 602 000 + 100·k, +1 na próbę), sceny treningowe 21 421 xxx | 2026-11-16 | w użyciu (trening) |
| 21 631 000 – 21 631 149 | KROK 6 r4 TEST (szum, `brainleg_noise.py`, cel `LOOP_TARGET_brainleg_r4.md`): sceny `--seed 21631`, 6 póz — RAZ | 2026-11-16 | zarezerwowane |
| 21 641 000 – 21 642 999 | KROK 6 r4 TEST: ziarna szumu (21 641 000 + 100·k dla σ 2, 21 642 000 + 100·k dla σ 6) | 2026-11-16 | zarezerwowane |
| 21 631 000 – 21 631 149, 21 641 000 – 21 642 999 (zużyte) | KROK 6 r4 TEST: wykonany 16 XI 13:37–13:42, 12 przebiegów — wynik w audit_log_step3_20261115.md (krok 73) | 2026-11-16 | ZUŻYTE |
| 21 101 000 – 21 101 449 (dopisek) | KROK 6 integracja (eksploracja): zadanie całego ramienia z siecią kroku 6 (`run3_ext.py`), sceny treningowe 21101 | 2026-11-16 | w użyciu (trening) |
| 21 951 000 – 149 / 21 952 000 – 149 / 21 953 000 – 149 | KROK 4 r2 TEST (dwa odruchy, 3× scen, `reflex.py`, cel `LOOP_TARGET_reflex_r2.md`): sceny `--seed 21951/21952/21953`, 6 póz — RAZ | 2026-11-16 | zarezerwowane |
| 21 960 001 – 005 / 21 970 001 – 005 / 21 980 001 – 005 | KROK 4 r2 TEST: tasowania F / L / G, oba Glu | 2026-11-16 | zarezerwowane |
| 21 951 000 – 149, 21 952 000 – 149, 21 953 000 – 149, 21 960/970/980 001 – 005 (zużyte) | KROK 4 r2 TEST: wykonany 16 XI 15:36, 96 przebiegów — wynik w audit_log_step3_20261115.md (R1–R4) | 2026-11-16 | ZUŻYTE |
