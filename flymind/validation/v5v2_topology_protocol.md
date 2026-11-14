# V5 v2 — topologia vs lateralizacja (protokół zamrożony 2026-10-29, PRZED przebiegiem)

Kod: `flymind/v5v2_topology.py` (+ `loop.py`, `loop_v2.py` bez zmian zachowania). Hashe: `v5v2_topology_manifest.json`.
Kopia kodu: `v5v2_topology_frozen_code/`. Po uruchomieniu nic się nie zmienia; błąd techniczny = nowa wersja, raportowana.

## Pytanie i hipoteza
Czy szczegółowa topologia connectomu daje powtarzalną korzyść w sterowaniu ponad lateralizację?
**H1:** DATA ma mniejszy błąd końcowy niż SHUF_STR (kontrola zachowująca stopnie, siłę wejścia i wyjścia każdego neuronu).

## Warunki (dokładnie 9) i statusy
| Warunek | Opis | Status |
|---|---|---|
| DATA | sieć LC10a (275) + 147 pośrednich + DNa02 L/R, 13 510 krawędzi z MaleCNS v1.0 | DATA (tożsamości, krawędzie, liczby synaps, przekaźnik*) + MODEL (J0 0,2 liniowo, Glu = hamowanie, ALIF) |
| SHUF_DEG | podwójne zamiany: stopnie, siła wyjściowa, Dale, zbiór wag zachowane; ziarno próby + 100 000 | MODEL (kontrola) |
| SHUF_STR | jw. + siła wejściowa każdego neuronu zachowana; ziarno + 200 000 | MODEL (kontrola) |
| CUT_LC10a_AOTU | krawędzie LC10a → 51 neuronów AOTU* (w tym 2 × AOTU019) = 0: 3234 krawędzie, 58 458 synaps; bez renormalizacji | MODEL (ablacja) |
| ABL_AOTU019 | 2 neurony (10005, 10070) usunięte: 399 krawędzi; bez renormalizacji | MODEL (ablacja) |
| TOY_RELAY | 275 krawędzi modelowych LC10a → DNa02 ipsilateralnie (n_syn 19,8 / 18,9), własna kalibracja V4 v2 (300,2 Hz/rad) | MODEL |
| P_CTRL | regulator P na gL − gR, omija SNN | ENGINEERING |
| NO_VISION | klatki bez obrazu | ENGINEERING |
| SWAP | DATA z zamienionym napędem stron LC10a | MODEL (kontrola) |
Wspólne: enkoder (MODEL: detektor kontrastu barwnego), kamera, MuJoCo, warstwa bezpieczeństwa, poza ramienia (ENGINEERING).
Dekoder (MODEL): DATA, SHUF_*, CUT, ABL, SWAP — wspólny dekoder sieci z danych (495,6 Hz/rad, V4 v2).
*przekaźnik: ground truth albo predykcja z danych MaleCNS (kolumna źródła w `SNNSpec.nt`).

## Weryfikacja kontroli (wykonana przed zamrożeniem, `results/v5v2_topology_verification.json`)
Wszystkie asercje własności tasowań i ablacji spełnione (liczby jw.). **Indeks lateralizacji** (znakowany napęd 1+2-skokowy
LC10a → DNa02, ipsi − kontra) względem DATA: SHUF_DEG ≈ 0 (0,001; 0,003; −0,002), SHUF_STR 0,12–0,27, CUT 0,086,
ABL_AOTU019 0,458. **Ograniczenie zapisane przed przebiegiem:** SHUF_STR NIE zachowuje lateralizacji (traci 73–88 %);
porównanie DATA vs SHUF_STR nie oddziela topologii od lateralizacji. Zestaw 9 warunków jest narzucony; nie dodaję kontroli.

## Zadanie i próby
`loop_v2.trial_spec_v2`: az0 ~ U(−30°, 30°), ρ ~ U[0,16; 0,35] m (zadanie V5 v2, bez dystraktora), Q_POSE, 3 s, takt 10 ms.
Ziarna **3001–3050** (n = 50, pula 3001–3100 zarejestrowana przed użyciem; 0–39 i 300–399 odrzucane w kodzie). Próby
sparowane między warunkami. Wykluczeń brak; błąd symulatora = porażka, raportowana.

## Metryki
- Główna: błąd końcowy = średnie |e| w 2,5–3,0 s (e z prawdy symulatora, tylko ocena).
- Pomocnicze: sukces (|e| < 5° przez całe 2,5–3,0 s), czas do pierwszego |e| < 5°, stabilność = połowa amplitudy e w
  ostatniej 1 s, przeregulowanie, takty z flagą bezpieczeństwa.

## Statystyka
- Każdy warunek vs DATA: różnica w parach d = warunek − DATA (°). Średnia d z 95 % CI (bootstrap par, ziarno 3301,
  10 000), mediana d, wielkość efektu: Cohen d_z i korelacja rangowo-dwuseryjna; test Wilcoxona (dwustronny) na d ≠ 0.
- Korekta: Holm–Bonferroni na 8 porównaniach (α = 0,05, rodzina).
- **H1 potwierdzona** ⇔ p_Holm(SHUF_STR) < 0,05 ∧ średnie d > 0 ∧ dolna granica CI > 0. Inaczej: „Hipoteza nie została
  potwierdzona.”
- Mechanizm: deficyt CUT = średnie d(CUT); udział wyjaśniony = d(CUT)/d(SHUF_STR) z 95 % CI (bootstrap ilorazu); część
  niewyjaśniona = 1 − udział. Udział interpretowany TYLKO gdy deficyt SHUF_STR ma dolną granicę 95 % CI > 0; inaczej
  raport „udział nieokreślony” (dzielenie przez wartość bliską 0 — wykryte w teście dymnym na ziarnach 1231–1233). Sukces: pary rozbieżne i McNemar (opis, bez korekty).
- Pomocniczo: korelacja Spearmana między indeksem lateralizacji instancji SHUF_STR a błędem końcowym (czy deficyt
  śledzi utratę lateralizacji); opis, bez testu potwierdzającego.

## Interpretacja ustalona teraz
- H1 potwierdzona → „organizacja połączeń z danych daje mniejszy błąd niż losowa organizacja o tych samych stopniach
  i siłach”. Z powodu ograniczenia powyżej NIE → „topologia ponad lateralizację”, chyba że korelacja pomocnicza nie
  wykazuje zależności deficytu od indeksu lateralizacji (i to tylko jako przesłanka, nie dowód).
- H1 niepotwierdzona → raport: „Hipoteza nie została potwierdzona.” Bez strojenia J0, progów ani sceny.
- Żaden wynik nie oznacza biologicznego modelu widzenia ani przewagi SNN nad P.
