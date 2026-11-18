# V5 v3 — wkład wzorca połączeń wewnątrz bloków warstwa×strona (SZKIC do zatwierdzenia, NIEURUCHOMIONY)

Status: SZKIC r3, 2026-10-29 (po Red Team: `results/redteam/v5v3_control_redteam.md`, `v5v3_control_v2_redteam.md`).
Poprzednia wersja zachowana: `v5v3_protocol_DRAFT_r2_superseded.md`. Po zatwierdzeniu przez użytkownika: kopia jako
`validation/v5v3_protocol.md`, manifest z hashami kodu, kopia kodu, test dymny na ziarnach dev, jeden przebieg
`v5v3.py --approved-protocol-sha256 <sha>` (runner odmawia bez zgodności). Protokół V5 v2 bez zmian.

## 1. Wiedza posiadana przed napisaniem (jawnie; nic z niej nie zmieniło J0, progu synaps, enkodera ani scen)
- V5 v2 (3001–3050): DATA lepsza od SHUF_STR o 1,61°; efekt w ρ 0,24–0,30 m. Audyt: SHUF_STR traci 68–89 % lateralizacji
  i ma własne nachylenie kalibracji 101–147 Hz/rad (DATA 496) → różnica miesza topologię, lateralizację i skalę sygnału.
- Kontrola v1 (tylko strona somy) odrzucona przez Red Team (tworzy krawędzie LC10a → DNa02, zmienia λ_max i warstwy).
- Kontrola v2 (warstwa × strona), pętla otwarta, ziarna dev: lateralizacja ścieżek 1,0000 × DATA, wejścia DNa02 identyczne,
  architektura warstw identyczna, λ_max 26,3 (DATA 26,1), nachylenie kalibracji 491–494 (DATA 496), kontra 0 Hz.
  Różnica funkcjonalna = przesunięcie progu odpowiedzi DNa02 w CAŁOŚCI z bloku LC10a×LC10a (zamiana samego bloku odtwarza ją,
  przywrócenie bloku z DATA ją znosi). Znak zależy od napędu: g 0,50–0,55 DATA wyżej o ~9–10 Hz, g 0,70 kontrola wyżej o 3–6 Hz,
  g 1,0 brak różnicy. Przegląd stabilności (`results/v6_stability/`): Δg30 > 0 w 18/20 ustawień, wielkość ≤ 0,014 g.
- Martwa strefa SNN (ρ ≥ 0,28 m) wynika z enkodera i progu LC10a (12 mV·g < ~7 mV; `results/v7_encoder_distance_20261029.txt`),
  nie z sieci — dotyczy obu warunków SNN jednakowo.
- Przewidywanie (z powyższego, nie kryterium): efekt w pętli zamkniętej mały; symulacja RT dla prawdziwego d = −0,5°:
  P(„pierwszy lepszy”) 0,15, P(„równoważne”) 0,38, P(„nierozstrzygnięte”) 0,47.

## 2. Pytanie i hipotezy (znak: d = błąd_końcowy(pierwszy) − błąd_końcowy(drugi); d < 0 ⇔ pierwszy lepszy)
- **H1 (jedyna główna, α = 0,05 bez korekty):** DATA vs SHUF_WITHIN_SIDE v2. Pytanie w ograniczonej postaci: czy wzorzec
  połączeń z danych WEWNĄTRZ bloków warstwa×strona — przy zachowanej lateralizacji ścieżek, architekturze warstw, wejściach
  DNa02, składzie grup partnerów i multizbiorach wag każdego neuronu — zmienia błąd końcowy? W praktyce (pętla otwarta)
  jedynym aktywnym składnikiem jest blok LC10a×LC10a (wzajemność, trójkąty, klasteryzacja, asortatywność zmieniają się razem
  — test nie rozróżnia, który z nich działa).
- H2 (replikacja V5 v2): DATA vs SHUF_STR. H3: SHUF_WITHIN_SIDE v2 vs SHUF_STR — czy zachowanie lateralizacji, warstw, wejść
  DNa02 i skali sygnału zmniejsza błąd. H2 i H3: rodzina Holma z dwóch porównań, α = 0,05.
- D1 DATA vs TOY_RELAY, D2 DATA vs P_CTRL: opis (p bez korekty, bez decyzji).

## 3. Warunki (5), statusy, sceny
| Warunek | Definicja | Status |
|---|---|---|
| DATA | `visual_path.network(0.2)`: 424 neurony, 13 510 krawędzi | DATA + MODEL (J0 0,2, ALIF, Glu = hamowanie) |
| SHUF_WITHIN_SIDE v2 | `side_shuffle.shuffle_within_side(spec, layer_side_labels(...), ziarno + 400 000)` | CONTROL |
| SHUF_STR | `visual_path.shuffle(equal_weight=True)`, ziarno + 200 000 (jak V5 v2) | CONTROL |
| TOY_RELAY | `loop_v2.toy_relay`, własna kalibracja V4 v2 | MODEL |
| P_CTRL | regulator P na gL − gR | ENGINEERING |
Wspólne: enkoder (ENGINEERING), kamera/MuJoCo/warstwa bezpieczeństwa (ENGINEERING), dekoder sieci DATA (496 Hz/rad) dla DATA
i obu tasowań. Sceny: `loop_v2.trial_spec_v2` (az0 ~ U(−30°, 30°), ρ ~ U[0,16; 0,35] m), identyczne dla wszystkich warunków
danego ziarna; Q_POSE, 3 s, takt 10 ms.

### SHUF_WITHIN_SIDE v2 — definicja
Grupa = warstwa × strona. Strona = `somaSide` (MaleCNS v1.0; 'L'/'R', inne → 'U'; tu L 194, R 230, U 0; `rootSide` pusty;
nie z nazwy). Warstwa: 'in' = typ LC10a, 'dn' = DNa02 (adnotacje), 'mid' = reguła selekcji visual_path. Grupy: in_L 135,
in_R 140, mid_L 58, mid_R 89, dn_L 1, dn_R 1. Zamiana (a→b, c→d) → (a→d, c→b) tylko przy identycznej wadze ze znakiem,
grupa(a) = grupa(c), grupa(b) = grupa(d), b ≠ d, a ≠ d, c ≠ b, bez duplikatów; 5 zamian na krawędź. Asercja w KAŻDEJ próbie
(`side_shuffle.KEYS`, 17 własności, w tym multizbiory par (grupa, waga) per neuron) + osiągnięty cel zamian; inaczej przerwanie.
Nietestowane przez tę kontrolę: 57–58 % masy |w| zostaje na miejscu (97–99 % najsilniejszego 1 % krawędzi), tożsamość LC10a
jest niewidoczna dla pętli (jednakowy prąd na stronę). Wynik „równoważne” NIE znaczy „topologia nieistotna”.

## 4. Próby i ziarna
Ziarna **3051–3100** (n = 50): sprawdzone — brak użycia w wynikach, manifestach i scratchpadzie; pula 3001–3100 zarejestrowana
2026-10-29, 3001–3050 zużyte w V5 v2. Tasowania: 403 051–403 100 i 203 051–203 100 (nieużyte). 0–39 i 300–399 odrzucane.
n wynika z puli. Moc (σ_d ≈ 2,6°, α = 0,05 dla H1): efekt 1,0° → 0,78; 1,6° → 0,99; równoważność TOST przy d = 0 → 0,72.

## 5. Metryki i analiza (kod `v5v3.analyze`, testy `test_v5v3_analysis.py`)
- Główna: d dla błędu końcowego (średnie |e| w 2,5–3,0 s; e z prawdy symulatora — tylko ocena).
- Test: permutacyjny zmiany znaku średniej d, dwustronny, 100 000 permutacji, ziarno 3401, zera w danych (RT: błąd I rodzaju
  5,0–5,7 % w symulacji). Pomocniczo Wilcoxon (Pratt). CI: bootstrap par 95 % i 90 % (10 000, ziarno 3402). d_z, liczba zer,
  liczba par z |d| > 1°.
- **SESOI = 1,0°** (≈ 1,5 kolumny obrazu; 20 % tolerancji sukcesu).
- Decyzja dla H1: p < 0,05 ∧ CI95 < 0 → „DATA lepsza” (+ „≥ SESOI” jeśli średnie d ≤ −1,0°, inaczej „< SESOI”);
  p < 0,05 ∧ CI95 > 0 → „kontrola lepsza”; CI90 ⊂ (−1,0; +1,0) → „równoważne w granicach SESOI — dotyczy średniej łącznej
  po rozkładzie scen V5 v2”; inaczej „nierozstrzygnięte”. Ta sama reguła dla H2, H3 z p_Holm.
- **Warstwy (ustalone teraz, opis):** ρ ∈ [0,16; 0,24), [0,24; 0,30), [0,30; 0,35] — średnie d z CI95 w każdej warstwie dla
  H1–H3. Ponieważ znak efektu w pętli otwartej zależy od napędu, równoważność łączna nie wyklucza efektów przeciwnych znaków
  w warstwach — raportowane obok, bez testów decyzyjnych.
- Pomocnicze: sukces (|e| < 5° w 2,5–3,0 s), czas do pierwszego |e| < 5°; po przebiegu nachylenia kalibracji 5 pierwszych
  instancji każdej kontroli (opis).

## 6. Wykluczenia, przerwanie, analiza wrażliwości
- Próba z błędem symulatora → ziarno wykluczone ze wszystkich porównań błędu końcowego (sparowanie); w sukcesie = porażka.
- Przerwanie: niezgodność hashy Stage 1 przed/po; naruszenie własności kontroli; > 2 błędy symulatora w JEDNYM warunku
  (> 4 % jego prób) lub > 5 % wszystkich; niezgodność kodu z manifestem; ziarno zakazane.
- Wrażliwość (jeśli są wykluczenia): analiza H1 z wykluczonymi ziarnami wstawionymi jako d = +max|d| (najbardziej niekorzystne
  dla DATA) — raportowana obok.

## 7. Interpretacja i raportowanie
- „DATA lepsza” → „wzorzec połączeń z danych wewnątrz bloków warstwa×strona (w praktyce LC10a×LC10a) zmniejsza błąd przy
  zachowanej lateralizacji, warstwach, wejściach DNa02 i skali sygnału” — nie „topologia całej drogi wzrokowej”, nie biologia.
- „Równoważne”, „nierozstrzygnięte” lub „kontrola lepsza” → raport dosłownie: „Hipoteza nie została potwierdzona.” z liczbami
  i warstwami; bez zmian J0, progu synaps, enkodera, scen ani metryk.
- Wszystkie próby i warunki raportowane; jakość sterowania (P_CTRL) raportowana osobno od wartości wyjaśniającej topologii.
