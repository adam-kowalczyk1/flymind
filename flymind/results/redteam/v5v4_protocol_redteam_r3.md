# Red Team protokołu FlyMind V5 v4 — runda 3 (wąska: weryfikacja diffów po r2)

Data: 2026-10-29. Osobna instancja modelu (ograniczona niezależność). Zapisano tylko ten plik. Bez bio2, bez pętli zamkniętej, bez commitów, ziarna wyłącznie 8001–8999 (tu: żadne ziarno nie było potrzebne). Scratch: `.../scratchpad/redteam_v5v4/r3a.py`.

## Werdykt: **READY** (0 BLOCKER, 0 MAJOR; 3 drobne uwagi MINOR, żadna nie blokuje zamrożenia)

## Komendy
```
cd /Users/admin/so101_fly_project
diff flymind/results/v5v4_r2_runner_superseded.py.txt flymind/v5v4.py
diff flymind/validation/v5v4_protocol_DRAFT_r2_superseded.md flymind/validation/v5v4_protocol_DRAFT.md
.venv/bin/python -I -B flymind/test_v5v4.py      # OK: V5 v4 r2 testy techniczne (24 asercji)
.venv/bin/python -I -B $S/r3a.py                 # append_record po uciętej linii; etykiety N8
```

## Weryfikacja poprawek r2 → r3
| Poprawka | Status |
|---|---|
| N2 ziarna RNG 9401/9402 (`v5v4.py:36`) | OK — poza pulami prób; protokół §6 zgodny z kodem. (Uwaga formalna: 9401/9402 to nie 8001–8999 użyte przeze mnie, nie ma kolizji z pulami eksperymentów.) |
| N8 etykieta wielkości wg CI (`v5v4.py:112-117`) | OK — „pomijalny” tylko gdy oba CI95 ⊂ ±0,5°; sprawdziłem: średnia −0,45, CI [−0,9; −0,05] → „wielkość względem SESOI nieustalona”; [−0,45; −0,05] → „pomijalny”; [−1,6; −0,6] → „≥ SESOI”. Etykieta „≥ SESOI” nadal wg średniej punktowej (CI może dopuszczać mniej) — zgodnie z protokołem §6, akceptowalne. |
| N7 `read_records`/`append_record` (`v5v4.py:202-228`) | OK — test na uciętej linii bez „\n”: po dopisaniu rekordów 2 i 3 odczyt daje ziarna [1, 2, 3] i 1 linię uszkodzoną (pomijaną i liczoną); analiza już nie wywala się na uszkodzonym wierszu. |
| N1 błędy z rekordów sprzed wznowienia (`v5v4.py:254`) | OK — `errs` startuje od błędów już zapisanych dla ziaren z `seeds`; limit nadal per shard (zgodne z protokołem §7). |
| N6 walidacja w `--analyze` (`v5v4.py:314-327`) | W zasadzie OK (kod vs manifest przy analizie, flagi VALID, `validity.VALID`), z uwagami M-a/M-b poniżej. |
| N9 testy | OK — dodano odmowę bez `--shard` (24 asercje: odczyt z uszkodzoną linią, odmowa). |
| N3–N5 | Przyjęte jako ograniczenia w §9 protokołu; opis post-hoc nachyleń SWS nie jest zamrożonym kodem (zadanie analizy, nie wpływa na decyzje). |

## Nowe uwagi (wszystkie MINOR)
- **M-a — walidacja shardów jest luźna.** `v5v4.py:322-323`: pliki `run_meta_*` czytane są tylko z katalogu PIERWSZEGO pliku `--analyze` i nie jest sprawdzane, że jest jeden meta na każdy shard (`meta["shard"]`) ani że ich zakresy ziaren pokrywają komplet. Przy shardach w różnych katalogach, albo gdy shard B zginął po ostatnim rekordzie, a przed zapisem meta, `all_shards_VALID` może być `True` na podstawie samego meta shardu A (analiza tak czy inaczej wymaga kompletu ziaren przez `--expect`). Dodatkowo meta z testu dymnego w tym samym katalogu wchodzi do `all(...)`. Naprawa (opcjonalna, lecz tania): wymagać po jednym meta na plik JSONL (`meta["shard"]` = sufiks pliku) i `meta["seeds"]` w puli; w protokole zapisać jedną kanoniczną ścieżkę `--out`.
- **M-b — `--expect` jest opcjonalny w kodzie** (`exp = None`, gdy brak flagi → komplet ziaren niesprawdzany). Protokół §7 podaje polecenie z `--expect 4001-4450`, więc jest zgodny; ale wynik potwierdzający powinien być uznany tylko z tym parametrem — dopisać do §7/§8 jako warunek raportu lub zrobić flagę wymaganą dla `VALID`.
- **M-c — drobiazgi.** `append_record` czyta cały plik, by sprawdzić ostatni bajt (wystarczy `seek(-1, 2)`; bez znaczenia przy ~450 liniach). Stage 1 nie jest ponownie sprawdzany w trybie `--analyze` (tylko kod vs manifest), co jest akceptowalne, bo `VALID` z meta uwzględnia Stage 1 po przebiegu.

## Podsumowanie (5 linii)
1. Jestem osobną instancją modelu (ograniczona niezależność).
2. READY: 0 BLOCKER, 0 MAJOR; poprawki N1, N2, N6, N7, N8, N9 zweryfikowane diffem, testem (24/24 OK) i próbą na uciętym JSONL.
3. N7 działa: po uciętej linii rekordy 2 i 3 poprawnie odczytane, 1 linia uszkodzona pomijana; N8 daje właściwe etykiety (w tym „nieustalona”).
4. MINOR: M-a walidacja shardów tylko z katalogu pierwszego pliku bez dopasowania meta do shardu, M-b `--expect` opcjonalny, M-c `append_record` czyta cały plik; nie blokują zamrożenia.
5. Raport: `/Users/admin/so101_fly_project/flymind/results/redteam/v5v4_protocol_redteam_r3.md`.
