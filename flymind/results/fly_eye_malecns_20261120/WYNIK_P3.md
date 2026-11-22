# P3 — oko flyvis uczone od zera na połączeniach MaleCNS: **FAILED na bramce G0′** (22 XI 2026, 19:40)

Plan: `PREREG_P3.md` (z kolejnymi zmianami spisanymi przed wynikami). Sprawdzian G0′: spadek straty modelu 000 (MaleCNS)
≥ połowa spadku kontroli K0 (oryginalny konektom flyvis, uczony od zera tym samym przepisem), przy tym samym k.

| | strata, kroki 0–1000 | strata, kroki 13 412–14 412 | spadek |
|---|---|---|---|
| model 000 (MaleCNS) | 1301,1 | 1305,0 | **−0,3 %** |
| K0 (flyvis od zera) | 1306,0 | 1287,3 | **+1,4 %** |

Warunek: −0,3 % ≥ 0,7 % → **nie**. Zgodnie z planem uczenie 000 zatrzymane (19:40); K0 też zatrzymana (była tylko punktem
odniesienia). Modele 001–003 wstrzymane od 12:59 (punkty kontrolne zostają, wznowienie możliwe).
DSI T4/T5 modelu 000 (tylko raport) — nie policzone: błąd w moim skrypcie (`init_network(chkpt=…)` — zły argument).

## Uczciwie
- Kontrola K0 też uczy się bardzo wolno (+1,4 % po 14 400 krokach z 250 000) — bramka porównuje dwa bardzo małe spadki,
  więc jest słaba. Wynik znaczy: **po ~14 000 krokach oko na MaleCNS nie pokazuje żadnego uczenia, a oryginał pokazuje mały
  początek**. Nie znaczy, że nigdy by się nie nauczyło.
- Możliwe przyczyny (niesprawdzone): inne skale napędu po zmianie liczby przesunięć (siła startowa wyrównana tylko średnio),
  usunięte 27 par, hybryda R*/CT1/Am z mapy samicy; albo po prostu za mało kroków.
- Koszt: ~23 h liczenia Maca (4 modele), Sintel 5,8 GB zostaje na dysku.
