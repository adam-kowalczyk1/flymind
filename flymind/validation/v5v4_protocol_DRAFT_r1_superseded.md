# V5 v4 — protokół (SZKIC r1, 2026-10-29; do Red Team, NIEZAMROŻONY, NIEURUCHOMIONY)

Kod: `flymind/v5v4.py` (runner + analiza), testy `flymind/test_v5v4.py` (18 asercji, zielone), moc `flymind/v5v4_power.py`
(`results/v5v4_power_20261029.txt`), kalibracja `results/v5v4_calibration_check_20261029.txt`. V5 v3 nie jest zmieniany.
Etykiety: DATA (connectom MaleCNS v1.0), MODEL (ALIF, J0, znak Glu, przekaźnik), ENGINEERING (enkoder, kamera, MuJoCo,
bezpieczeństwo, regulator P), CONTROL (tasowania, kalibracja dekodera).

## 0. Wiedza przed napisaniem (jawnie)
V5 v3 (3051–3100): H1 DATA − SWS v2 = −0,19° (CI90 −0,51; +0,10) → równoważne ±1° łącznie; warstwy (opis): ρ 0,16–0,24 +0,53°
(kontrola lepsza), 0,24–0,30 −1,02° (DATA lepsza), 0,30–0,35 −0,47°; H2 DATA − SHUF_STR −2,40°; Red Team V5 v3:
PASS_WITH_LIMITATIONS (SESOI 1° hojne, równoważność łączna ≠ w warstwach, H2 zakłócone skalą sygnału). Eksploracja po V5 v3
(dev 1501–1520): SHUF_STR z własną kalibracją dekodera poprawia się o 1,17°, DATA − SHUF_STR maleje z −2,62° do −1,45°.
Enkoder (`v7_encoder_distance`, deterministyczne rendery, bez wyników zachowania): dla ρ ≥ 0,28 m prąd LC10a (12 mV·g) < ~7 mV
progu przy |az| ≥ 15° → sieć milczy, d = 0 strukturalnie.

## 1. Pytania i hipotezy (d = błąd(pierwszy) − błąd(drugi); d < 0 ⇔ pierwszy lepszy)
- **H1 (główna, per warstwa):** DATA vs SWS (SHUF_WITHIN_SIDE v2) w scenach ρ < 0,28 m, warstwy S1 [0,16; 0,22) i S2 [0,22; 0,28).
  W każdej warstwie dwa pytania: (a) przewaga — test permutacyjny zmiany znaku, Holm na 2 warstwach, α 0,05;
  (b) równoważność — TOST ±SESOI przy α 0,025 na warstwę (Bonferroni na 2) ⇔ CI95 (bootstrap) ⊂ (−0,5°; +0,5°).
  Wynik łączny (S1+S2): opis, bez decyzji.
- **H2 (skala sygnału vs reszta):** H2a DATA − STR_OWN (po wyrównaniu skali kalibracją); H2b STR_SHARED − STR_OWN (efekt samej
  kalibracji dekodera na tej samej instancji SHUF_STR). Holm na {H2a, H2b}, α 0,05; decyzja: p_Holm < 0,05 ∧ CI95 bez 0.
- Opis (bez decyzji): DATA − TOY, DATA − P; warstwy dla H2.
Interpretacja ograniczona z góry: SWS v2 zachowuje lateralizację, warstwy, wejścia DNa02, skład grup i multizbiory wag — różni
się w praktyce wzorcem w bloku LC10a×LC10a (wzajemność, trójkąty, klasteryzacja, asortatywność razem); 57–58 % masy |w| zostaje
na miejscu. SHUF_STR niszczy jednocześnie lateralizację, architekturę warstw i wzorce w blokach; H2a po wyrównaniu skali NIE
rozdziela lateralizacji od architektury warstw. Nic tu nie jest twierdzeniem o mózgu muchy.

## 2. Uzasadnienie ρ < 0,28 m i warstw (ustalone przed nowymi wynikami)
(1) Mechanizm deterministyczny niezależny od zachowania: dla ρ ≥ 0,28 m prąd LC10a jest podprogowy dla |az| ≥ 15° → obie sieci
milczą, d ≡ 0 nie niesie informacji o topologii. (2) Wcześniejsze wyniki (V5 v3, opis warstw) wskazały, że różnice występują
poniżej tej odległości — to motywacja eksploracyjna; dlatego test na NOWYCH ziarnach, a nie reanaliza V5 v3. Granica 0,22 m
dzieli zakres na równe połowy (nie dobrana do wyników). Warstwy przypisane deterministycznie: parzyste ziarno → S1, nieparzyste → S2.

## 3. SESOI = ±0,5°
Rozdzielczość obrazu: 128 kolumn na ~86° poziomego pola → 0,67°/kolumnę; enkoder rozmywa 3×3 px; 0,5° < 1 kolumna — różnica
poniżej rozdzielczości kamery nie jest istotna dla sterowania. 10 % tolerancji sukcesu (5°). Odniesienie: dokładność regulatora P
na tym samym enkoderze ≈ 0,3° (V5 v3) — dolna granica osiągalna dla tego układu. SESOI nie jest kalibrowane do wyników V5 v3
(tam przewidywano 1°; RT wskazał, że 1° było hojne).

## 4. Warunki (6), sceny, dekodery
| Warunek | Definicja | Status |
|---|---|---|
| DATA | `visual_path.network(0.2)` | DATA + MODEL |
| SWS | `shuffle_within_side(spec, layer_side_labels, ziarno + 400 000)`; asercja 17 własności + cel zamian | CONTROL |
| STR_OWN | `shuffle(equal_weight=True)`, ziarno + 200 000; dekoder kalibrowany na tej instancji | CONTROL |
| STR_SHARED | ta sama instancja SHUF_STR; dekoder DATA | CONTROL |
| TOY | `loop_v2.toy_relay`, dekoder własny | MODEL |
| P | regulator P na gL − gR | ENGINEERING |
Sceny: `trial_spec_v4` — az0 ~ U(−30°, 30°), ρ ~ U w warstwie; identyczne dla wszystkich warunków ziarna; Q_POSE, 3 s, takt 10 ms;
ziarno ALIF = ziarno próby (wspólne dla warunków SNN).
**Kalibracja (CONTROL, jednakowa dla DATA, SWS, STR_OWN, TOY):** `v5v4.calibrate` — bodźce syntetyczne spot_clip az −30…30° co 10°
(+ pusty obraz), ziarna ALIF z puli kalibracyjnej 5001–5003, parametry: wyłącznie slope (offset = L−P dla pustego obrazu);
cel: MNK różnicy DNa02 L−P względem azymutu; reguła: liczona raz na instancję przed jej próbą, zamrożona; slope ≤ 2 Hz/rad →
odmowa. Kalibracja nie widzi scen ani wyników pętli zamkniętej (brak przecieku). DATA: slope 492,1 (sprawdzone, deterministyczne),
TOY 306,1. Kalibracja może zmienić interpretację: wyrównuje WZMOCNIENIE małosygnałowe, nie progi ani nieliniowość.

## 5. Ziarna i liczebność
Potwierdzające **4001–4240** (n = 240; S1 120, S2 120), instancje SWS 404 001–404 240, SHUF_STR 204 001–204 240; kalibracyjne
5001–5003; test dymny (dev) 6001–6002. Historia: brak użycia 4001–4200 (+0/100 000/200 000/400 000/500 000), 5001–5010, 6001–6010
oraz 4201–4240 (+ te same offsety) w 57 plikach JSON wyników/manifestów/scratchpadu i w kodzie. Wykluczone
pule (runner odmawia): 0–39, 300–399, 1001–1999, 2001–2005, 2011–2100, 3001–3100.
Moc (symulacja, resampling rozkładów d z V5 v3 w warstwach; SD S1 ≈ 0,64°, S2 ≈ 1,86° — szacunki z n = 15 i 17, S1 prawdopodobnie
zaniżone): n = 120/warstwę → S2: P(równoważność | δ = 0) 0,70, P(przewaga | δ = −0,5°) 0,80, P(przewaga | δ = −1°) ≈ 1,0;
S1: ≈ 1,0 (optymistyczne). H2a/H2b: ≥ 0,94 przy połowie efektu z eksploracji. Wniosek „równoważne” w S2 nie jest zagwarantowany
(30 % szans na brak rozstrzygnięcia przy δ = 0) — taki wynik będzie raportowany jako „nie wykazano ani różnicy, ani równoważności”.

## 6. Metryki, analiza, braki, wykluczenia, przerwanie
- Główna: błąd końcowy = średnie |e| w 2,5–3,0 s (e z prawdy symulatora, tylko ocena). Pomocnicze: sukces (|e| < 5° w 2,5–3,0 s),
  czas do |e| < 5°, przeregulowanie, takty z flagą bezpieczeństwa, nachylenia kalibracji.
- Jednostka analizy: ziarno (scena); porównania sparowane w ziarnie. Test: permutacyjny zmiany znaku średniej d (100 000, ziarno
  4401), CI: bootstrap par percentylowy (10 000, ziarno 4402) 95 % i 90 %; pomocniczo Wilcoxon (Pratt), d_z, liczba zer.
- Kategorie wyniku H1 per warstwa (`h1_category`): „DATA lepsza”, „kontrola lepsza” (z dopiskiem, jeśli CI95 ⊂ ±SESOI),
  „równoważne w granicach ±SESOI”, „nie wykazano ani różnicy, ani równoważności”. p > 0,05 ≠ „brak efektu”.
- Błąd symulatora albo NaN → ziarno wykluczone ze WSZYSTKICH porównań błędu (sparowanie), w sukcesie = porażka; analiza wrażliwości:
  wykluczone wstawione jako d = +max|d| (najgorzej dla DATA). Odmowa kalibracji → błąd = |az0| (brak ruchu), sukces = porażka;
  wrażliwość: analiza bez tych ziaren.
- Przerwanie (STOP, bez analizy potwierdzającej): Stage 1 niezgodny przed/po; naruszenie własności SWS lub SHUF_STR; > 5 błędów
  symulatora w jednym warunku lub > 2 % wszystkich prób; kalibracja DATA lub TOY odrzucona; kod ≠ manifest.
- Wznowienie: surowe rekordy JSONL (1 rekord = 1 ziarno ze wszystkimi warunkami, dopisywany po ukończeniu ziarna); po awarii
  ponowne uruchomienie tym samym poleceniem pomija ziarna z rekordem — bez podwójnego liczenia; rekord częściowy nie powstaje.

## 7. Raportowanie
Wszystkie warunki, warstwy i porównania (także nieistotne); liczby zaplanowane/wykonane/wykluczone/odrzucone; nachylenia kalibracji;
odstępstwa od protokołu; rozdzielenie DATA/MODEL/ENGINEERING/CONTROL; „nie wykryto” ≠ „równoważne” ≠ „przewaga”.
Fixed-drive (stały napęd) — osobne pytanie, poza tym protokołem.
