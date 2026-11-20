# Cel: „mucha wie, gdzie czuje” — czubek vs A0 w całym mózgu (r1, 20 XI 2026) — spisany PRZED uruchomieniem

## Ustawienie
- Mózg: ten sam co na żywo (`live_avoid.build(glu=-1, brake="hub")`: HeadLife z okiem, szczecinki głowy, DN).
  Wejście dotyku bez zmian w mechanice (40 mV/N, maks. 40 mV). Zmienia się TYLKO przypisanie:
  czubek → 84 szczecinki „końca nogi”, A0 → 93 „środkowe” (`results/bristle_map_r1.json`, reguła Elabbady 2026).
- Bez oka (wejście oka 0), bez ruchu ramienia (kąty stałe, startowe). Każdy warunek: 1 s (100 taktów po 10 ms).
- Warunki: nic; tylko czubek 1 N; tylko A0 1 N; oba 1 N. Szum sieci σ = 2 mV, ziarna 2011210–2011214 (5).
- Odpowiedź: średnie częstości grup DN (ucieczka DNp01/02/04/11, MDN, DNg15, DNge078) i różnice pul stawów 1–3 (r[j]).

## Hipotezy i kryteria
- **W1 (kierunkowa, z literatury: dotyk końca nogi → unikanie, Medeiros 2024):** MDN przy czubku > MDN przy A0
  w ≥ 4/5 ziaren.
- **W2 (czy w ogóle „wie, gdzie”):** klasyfikator najbliższego środka (zostaw-jedno-ziarno) odróżnia czubek od A0
  z trafnością ≥ 0,9 na wektorze odpowiedzi (8 liczb).
- **W3 (kontrola):** odległość odpowiedzi czubek–A0 porównana z 100 losowymi podziałami tych samych 310 szczecinek
  na grupy 84/93 (ziarna 2011215, 2 ziarna szumu). Opis: percentyl prawdziwej odległości (bez progu), bo dowolne dwie
  różne grupy dadzą jakąś różnicę.
- Brak odpowiedzi dla „nic” (DN < 1 Hz) jest warunkiem poprawności.
Wynik idzie do raportu bez zmian kryteriów, także „nie wie, gdzie”.
