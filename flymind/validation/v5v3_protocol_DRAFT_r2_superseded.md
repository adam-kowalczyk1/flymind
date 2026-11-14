# V5 v3 — izolacja topologii od lateralizacji (SZKIC do zatwierdzenia, NIEURUCHOMIONY)

Status: SZKIC 2026-10-29 (kontrola v2 po Red Team). Po zatwierdzeniu przez użytkownika: kopia jako `validation/v5v3_protocol.md`, manifest z hashami
kodu, a `v5v3.py` uruchamiany z `--approved-protocol-sha256` (runner odmawia bez zgodności). Protokół V5 v2 nie jest
zmieniany. Kod: `flymind/v5v3.py`, kontrola `flymind/side_shuffle.py`, testy `test_side_shuffle.py`, `test_v5v3_analysis.py`.

## Wiedza posiadana przed napisaniem (jawnie)
- V5 v2 (3001–3050): DATA vs SHUF_STR — DATA lepsza o 1,61° (konwencja v2: kontrola − DATA); efekt w ρ 0,24–0,30 m; SHUF_STR
  traci 68–89 % lateralizacji ścieżek. Audyt V5 v2: liczby odtworzone; p zależą od obsługi zer (16/50 par d = 0) —
  H1 v2 odporna, mechanizm CUT nie (test znaków p_Holm 0,36).
- Kontrola v1 (tylko strona somy) ODRZUCONA po Red Team (`results/redteam/v5v3_control_redteam.md`): tworzyła krawędzie
  LC10a → DNa02 (0 → 78–95), zmieniała architekturę warstw i λ_max (26,1 → 34–36).
- Walidacja techniczna kontroli v2 (pętla otwarta, ziarna dev 1001–1015, `results/v5v3_prep/v5v3_control_check_v2_*.json`):
  lateralizacja strukturalna 1,0000 × DATA, odpowiedź kontralateralna 0 Hz, λ_max 26,3 (DATA 26,1), architektura warstw
  identyczna; DNa02 ipsi przy napędzie 0,50 / 0,55 / 0,60 / 0,70: DATA 17 / 61 / 98 / 163 Hz, SWS v2 1–3 / 51 / 90–93 /
  167–169 Hz; dekompozycja: różnica przy słabym napędzie w całości z bloku LC10a×LC10a (wzajemne pary 2450 vs ~560).
  Wskazuje to kierunek i małą skalę spodziewanego efektu; żaden parametr nie został na tej podstawie zmieniony.

- Audyt wspólnego dekodera (`results/audit_shared_decoder_20261029.txt`): własne nachylenie kalibracji SHUF_STR (instancje
  V5 v2) 101–147 Hz/rad vs DATA 496 → w V5 v2 SHUF_STR pracowała przy ~20–30 % wzmocnienia pętli DATA (zakłócenie skalą
  sygnału). SHUF_WITHIN_SIDE v2: 491–494 Hz/rad (≤ 1 % różnicy) — wspólny dekoder nie zmienia jej wzmocnienia. Dlatego H2
  (DATA vs SHUF_STR) interpretujemy jako replikację z zastrzeżeniem skali, a H1 jako porównanie bez tego zakłócenia.
  Po przebiegu (opisowo): nachylenie własnej kalibracji 5 pierwszych instancji każdej kontroli (ziarna 3051–3055).

## Hipotezy (konwencja znaku: d = błąd_końcowy(pierwszy) − błąd_końcowy(drugi); d < 0 ⇔ pierwszy lepszy)
- **H1 (główna):** DATA vs SHUF_WITHIN_SIDE — czy organizacja połączeń z danych daje mniejszy błąd niż losowa organizacja
  zachowująca stopnie, siły i skład stron (somaSide) partnerów każdego neuronu.
- H2 (replikacja V5 v2): DATA vs SHUF_STR.
- H3 (rola stron): SHUF_WITHIN_SIDE vs SHUF_STR — czy samo zachowanie stron zmniejsza błąd.
- D1, D2 (opis, w tej samej rodzinie korekty): DATA vs TOY_RELAY; DATA vs P_CTRL.

## Warunki (5) i statusy
| Warunek | Definicja | Status |
|---|---|---|
| DATA | `visual_path.network(0.2)`, 424 neurony, 13 510 krawędzi | DATA + MODEL (J0, ALIF, Glu = −) |
| SHUF_WITHIN_SIDE | `side_shuffle.shuffle_within_side` v2 (warstwa × strona), ziarno próby + 400 000 (definicja niżej) | MODEL (kontrola) |
| SHUF_STR | `visual_path.shuffle(equal_weight=True)`, ziarno + 200 000 (jak V5 v2) | MODEL (kontrola) |
| TOY_RELAY | `loop_v2.toy_relay`, kalibracja V4 v2 | MODEL |
| P_CTRL | regulator P na gL − gR | ENGINEERING |
Pominięte (brak roli w H1–H3): NO_VISION, SWAP, SHUF_DEG, ablacje. Dekoder wspólny dla DATA i obu tasowań (slope 495,6 Hz/rad).

### SHUF_WITHIN_SIDE (wersja 2) — definicja
Grupa neuronu = warstwa × strona. Strona = `somaSide` (MaleCNS v1.0; 'L'/'R', inne → 'U'; w tej sieci L 194, R 230, U 0;
`rootSide` pusty — nieużywany; nie z nazwy). Warstwa: 'in' = typ LC10a, 'dn' = DNa02 (adnotacje), 'mid' = pośrednie z reguły
selekcji visual_path. Grupy: in_L 135, in_R 140, mid_L 58, mid_R 89, dn_L 1, dn_R 1. Podwójna zamiana (a→b, c→d) → (a→d, c→b)
tylko gdy w(a→b) = w(c→d) (ze znakiem), grupa(a) = grupa(c), grupa(b) = grupa(d), b ≠ d, a ≠ d, c ≠ b, nowe krawędzie nie
istnieją; 5 zamian na krawędź (RT: mieszanie nasyca się od 2). Zachowane (asercja w KAŻDEJ próbie, inaczej przerwanie):
liczba neuronów, krawędzi, synaps, zbiór wag, Dale, stopnie i siły we/wy, multizbiory wag we/wy każdego neuronu, skład grup
partnerów każdego neuronu (liczba, suma wag dodatnich, suma ujemnych), macierz grupa×grupa, brak krawędzi modelowych,
nietrywialność; cel liczby zamian osiągnięty. Konsekwencje: wejścia DNa02 identyczne jak w DATA; lateralizacja ścieżek ≤ 2
skoki identyczna. Zmienia się: który neuron w grupie jest partnerem — przy jednakowym prądzie enkodera na stronę dynamicznie
istotne są głównie wzorce rekurencji w blokach (LC10a↔LC10a: wzajemne pary 2450 → ~560; pośrednie↔pośrednie 599 → ~260).
Wersja 1 (tylko strona) odrzucona — patrz wyżej.

## Sceny, próby, ziarna
`loop_v2.trial_spec_v2` (az0 ~ U(−30°, 30°), ρ ~ U[0,16; 0,35] m), bez dystraktora, Q_POSE, 3 s, takt 10 ms — identyczne sceny
dla wszystkich warunków danego ziarna. **Ziarna 3051–3100 (n = 50)** — sprawdzone: brak użycia w wynikach, manifestach
i scratchpadzie (pula 3001–3100 zarejestrowana 2026-10-29; 3001–3050 zużyte w V5 v2). Ziarna tasowań 403 051–403 100
i 203 051–203 100 — nieużyte. 0–39 i 300–399 odrzucane w kodzie. Liczba prób wynika z wyczerpania puli (50); moc
(przybliżenie normalne, σ_d ≈ 2,6° z V5 v2; α po Holmie od 0,01 do 0,05 zależnie od rangi): efekt 1,6° → 0,96–0,99;
efekt = SESOI 1,0° → 0,56–0,78; równoważność (TOST, prawdziwe d = 0) ≈ 0,72. Jeśli moc dla SESOI jest za niska — decyzja użytkownika o nowej puli przed przebiegiem.

## Metryki
- Główna: d (powyżej) dla błędu końcowego = średnie |e| w 2,5–3,0 s (e z prawdy symulatora, tylko ocena).
- Pomocnicze: sukces (|e| < 5° przez 2,5–3,0 s), czas do pierwszego |e| < 5°, lateralizacja ścieżek per instancja tasowania.

## Statystyka (ustalona; `v5v3.analyze`, testy `test_v5v3_analysis.py`)
- Test główny: permutacyjny test zmiany znaku średniej d (dwustronny, 100 000 permutacji, ziarno 3401, zera w danych —
  rozwiązuje niejednoznaczność obsługi zer z V5 v2). Pomocniczo: Wilcoxon z metodą Pratta.
- CI: bootstrap par (10 000, ziarno 3402) 95 % i 90 % dla średniej d. Wielkość efektu: d_z; liczby par z |d| > 1°; zera.
- Korekta: Holm–Bonferroni na rodzinie {H1, H2, H3, D1, D2}, α = 0,05.
- **SESOI = 1,0°** (≈ 1,5 kolumny obrazu: 0,67°/kolumnę; 20 % tolerancji sukcesu 5°; poniżej efektu V5 v2).
- Decyzja dla każdego porównania: p_Holm < 0,05 ∧ CI95 < 0 → „pierwszy lepszy” (z dopiskiem ≥ / < SESOI wg średniej d);
  p_Holm < 0,05 ∧ CI95 > 0 → „drugi lepszy”; CI90 ⊂ (−1,0; +1,0) → „równoważne w granicach SESOI”; inaczej „nierozstrzygnięte”.

## Wykluczenia (ustalone przed przebiegiem)
Ziarno, na którym w KTÓRYMKOLWIEK warunku wystąpił błąd symulatora (SimError), jest wykluczane ze wszystkich porównań
błędu końcowego (sparowanie) i raportowane; w sukcesie liczy się jako porażka. Żadnych innych wykluczeń.

## Kryteria przerwania (przebieg kończy się, wynik nie jest analizowany jako potwierdzający)
Niezgodność hashy Stage 1 przed lub po; naruszenie którejkolwiek własności kontroli w dowolnej próbie; > 5 % prób z błędem
symulatora; niezgodność kodu z manifestem; ziarno z zakresów zakazanych.

## Interpretacja i raportowanie
- H1 „pierwszy lepszy” (≥ lub < SESOI) → „wzorzec połączeń wewnątrz bloków warstwa×strona (głównie rekurencja LC10a↔LC10a)
  z danych daje mniejszy błąd przy zachowanej lateralizacji, architekturze warstw, wejściach DNa02 i składzie grup” — NIE
  „topologia całej drogi wzrokowej”. Ograniczenia: strona somy ≠ strona synaps (17 % pośrednich działa głównie kontralateralnie,
  ale ich wyjścia do DNa02 są zachowane bez zmian); jednakowy prąd na stronę (enkoder) ukrywa tożsamość LC10a; jedna sieć,
  J0 0,2, próg 5 synaps.
- H1 „równoważne” lub „nierozstrzygnięte” albo „drugi lepszy” → raport dosłownie: „Hipoteza nie została potwierdzona.” wraz
  z liczbami; bez zmian J0, progu synaps, enkodera, scen ani metryk.
- Wszystkie warunki i próby raportowane, także negatywne i wykluczone.
