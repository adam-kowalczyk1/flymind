# V1 — klatki czy zdarzenia? Test wejścia kamery na płacie wzrokowym z danych (projekt d2, 2026-11-05)

**Status: PROJEKT d2 (po red teamie r1). Nic nie zostało uruchomione ani zaimplementowane. Wymaga zgody właściciela na decyzje
D1–D5 (§12) i osobnej zgody na każdy etap uruchomień.** Bez sprzętu, bez zakupów, bez SO-101. Tylko symulacja na Macu
(`.venv`, `python -I -B`). Historia: d1 → red team r1 (REDESIGN wycinka i punktu wejścia, reszta APPROVE WITH CHANGES) → d2 (§14).

## 0. Po co ten test (prostymi słowami)

Mamy wybrać kamerę na nadgarstek. Rekomendacja z przeglądu 2026-11-05: kamera klatkowa OV9281, alternatywa: kamera zdarzeniowa
GenX320. Argument za klatkami: dają jasność „jak fotoreceptor”, więc zasilą obwód muchy od laminy w górę, a kamera zdarzeniowa
zastępuje część obwodu sprzętowym progiem. Test sprawdza to w symulacji, zanim wydamy pieniądze:

> Czy wycinek płata wzrokowego z danych MaleCNS (od laminy do T4/T5 i LPLC2) liczy kierunek ruchu i looming tak samo dobrze
> z wejścia klatkowego (120/180 fps) jak z wejścia zdarzeniowego — i jak blisko „idealnego oka” (1000 Hz, bez szumu)?

Dwa uczciwe zastrzeżenia z góry:
1. **Obwód w naszym modelu może w ogóle nie liczyć ruchu** (Lappalainen 2024 potrzebowali dopasowania 734 parametrów). Dlatego
   najpierw bramka wykonalności (Etap 0). Jeśli nie przejdzie, porównania kamer z tego testu nie rozstrzygniemy — to też wynik.
2. **Fotoreceptorów z danych nie da się użyć jako wejścia**: w MaleCNS ich połączenia z laminą są szczątkowe (§1). Test dotyczy
   więc „konektomu od laminy w górę”, a wejście do laminy jest modelowe (jawnie, §5.4).

## 1. Fakty z danych (sprawdzone 2026-11-05; potwierdzone niezależnie przez red team r1)

- Prawe oko (`somaSide == 'R'`): współrzędne kolumn `assignedOlHex1/2` dla L1, L2, L3, L5, Mi1, Mi4, Mi9, Tm1, Tm2, Tm4, Tm9, C3
  (~833–898 komórek na typ). **Lewe oko nie ma hex dla L3 i Tm4** → test na prawym oku.
- **Konwencja heksagonalna (sprawdzona):** odległość d = (|Δq| + |Δr| + |Δq − Δr|)/2; sąsiedzi = (±1, 0), (0, ±1), (+1, +1), (−1, −1).
  Dowód: krawędzie L1 → Mi1 ≥ 5 synaps: (0,0) 887, (1,1) 7, (0,±1) 6+6, (±1,0) 3+2, (−1,−1) 2, (1,−1) 0. Osadzenie w płaszczyźnie:
  x = q + r·cos 120°, y = r·sin 120°. Test jednostkowy w `optic_slice.py` musi to odtwarzać.
- Bez hex (przypisanie z połączeń): R1-R6, L4, Tm3, T4a–d, T5a–d; globalne: LPLC2 (91 R), LC4 (55 R). R1-R6 nie mają strony
  (`somaSide` R tylko dla 9 ciał).
- Przekaźniki (`celltype_predicted_nt`, ufność): R1-R6 histamina 0,97; L1 Glu 0,81; Mi9 Glu 0,75; Mi4 GABA 0,86; C3 GABA 0,86;
  pozostałe typy obwodu ACh ≥ 0,92.
- Szkielet obwodu jest w danych: L1 → Mi1, Tm3, C3, L5; L2 → Tm1, Tm2, Tm4, L5; L3 → Mi9, Tm9, Mi1; Mi1/Tm3/Mi4/Mi9 → T4;
  Tm1/Tm2/Tm4/Tm9 → T5; T4/T5 → LPLC2.
- **Geometria T4 z danych (red team r1, skrypt `redteam/c.py`):** dla każdego T4 środki ciężkości wejść Mi4 i Mi9 leżą po
  przeciwnych stronach Mi1, przesunięte o ~0,7–0,9 kolumny, bardzo spójnie (długość średniego wektora 0,90–0,96); podtypy a/b
  i c/d są antyrównoległe, osie a/b i c/d ~97° od siebie. **T5 jest słabiej i niesymetrycznie zbudowany** (Tm4 i Tm9 bywają
  po tej samej stronie, np. T5c). Przewidywanie: T4 może dać DS, T5 może legalnie zawieść.
- **Fotoreceptory → lamina są szczątkowe:** na całym prawym oku tylko 509 z 892 L1 ma jakiekolwiek wejście R1-R6 (mediana 36
  synaps); w wycinku 33/217 L1 (red team r1). R1-R6 to ~11 % wejścia L1 i 2 % wejścia L3 (L3: 59 % od Dm12). 1982 z 3377 ciał
  R1-R6 ma status „Out of scope”.
- **Wycinek S-core (reguła jak w skrypcie sesji `slice.py`, zapisana tu dokładnie):** rdzeń = komórki 12 typów z hex w krążku
  d ≤ 8 wokół (mediana hex1, mediana hex2) kolumn L1 → 217 kolumn, 2604 komórki. Typ bez hex (Tm3, L4, T4, T5, LPLC2, LC4) wchodzi,
  jeśli **≥ 50 % jego synaps wejściowych OD KOMÓREK TYPÓW Z HEX pochodzi z rdzenia** (mianownik: tylko wejścia od typów z hex,
  jedno przejście, bez iteracji); R1-R6 wchodzi, jeśli ≥ 50 % jego synaps wyjściowych DO typów z hex trafia do rdzenia.
  Wynik: 5120 neuronów, 124 134 krawędzie, 799 229 synaps; LPLC2 33, LC4 17. Inne reguły dają inne liczby (red team r1:
  „≥ 50 % wszystkich wejść z wycinka” → 3416 neuronów i 2 T4; wersja iteracyjna → 4377). Reguła powyżej jest zamrożona;
  `optic_slice.py` musi odtworzyć 5120 co do neuronu, inaczej STOP.
- Udział wejścia z wnętrza wycinka (wszystkie źródła): T4 0,62–0,65; T5 0,57–0,62; Mi1 0,41; L3 0,05; LPLC2 0,30. Brakuje
  m.in. Dm, Pm, C2, CT1, Mi13, Tm5Y.
- **LPLC2 jest obcięty brzegiem wycinka** (żaden LPLC2 nie ma ≥ 50 % wszystkich wejść z wycinka; maks. 0,37) → looming tylko jako
  miara wtórna, z kontrolą pokrycia pola recepcyjnego (§7).

## 2. Literatura, która wymusza kształt testu

| Źródło | Co wspiera | Wpływ na projekt |
|---|---|---|
| Lappalainen i in., Nature 634:1132–1140, 2024, DOI 10.1038/s41586-024-07939-3 (preprint 10.1101/2023.03.11.532232) | Neurony **nieimpulsowe**, 721 kolumn, znaki z przekaźników (His, GABA, Glu hamujące), **734 dopasowane parametry** (potencjały spoczynkowe, stałe czasowe, skale synaps), zadanie przepływu optycznego, wejście = klatki szare 24 Hz, krok 20 ms; modele z losowymi parametrami gorsze | bramka Etapu 0; wariant nieimpulsowy; przewidywanie, że 120 fps wystarczy (H) |
| Gengs i in. 2002; Pantazis i in. 2008 (rekordy z wyszukiwania) | Histamina z R1–R6 otwiera kanały Cl⁻ (ort/HCLA) na LMC → hiperpolaryzacja L1/L2 przy świetle | znak wejścia do laminy −1 (§5.4) |
| Molina-Obando i in., eLife 8:e49373, 2019 | Selektywność ON wielosynaptyczna, hamowanie Glu (GluClα) i GABA; L1 Glu, Mi1/Tm3 przeciwny znak | Glu −1 w wariancie głównym |
| Groschner i in., Nature 603:119–123, 2022, DOI 10.1038/s41586-022-04428-3 (rekord) | Mi9 (Glu) hamuje T4 przez GluClα | jw. |
| Maisak i in., Nature 500:212–216, 2013, DOI 10.1038/nature12320 | T4 = ON, T5 = OFF, 4 podtypy na 4 kierunki | G1, G3 |
| Behnia i in., Nature 512:427–430, 2014, DOI 10.1038/nature13427 | Mi1/Tm3 ON, Tm1/Tm2 OFF; korelator z ich dynamiką ma szczyt ~1 Hz; Δφ = 5,1° | bodźce, siatka |
| Haag, Mishra, Borst, eLife 6:e29044, 2017 | Kąt akceptacji ~5°; Tm9 dolnoprzepustowy, Tm1/2/4 pasmowoprzepustowe | optyka |
| Nature Communications 2021, s41467-021-24986-w (red team r1, streszczenie) | Tm9, Tm2 i CT1 niosą też sygnał ON do T5 | Tm2/Tm9 wyłączone z G1 |
| Klapoetke i in., Nature, 2017, DOI 10.1038/nature24626 | LPLC2 i oponencja ruchu radialnego | H3 |
| Ketkar i in., Curr Biol 30:657–669, 2020, DOI 10.1016/j.cub.2019.12.038 | Luminancja (L3) potrzebna do kontrastu przy szybkich zmianach | H2 |
| Juusola & Hardie, J Gen Physiol 117:3–25, 2001, DOI 10.1085/jgp.117.1.3 | Adaptacja fotoreceptora w 4 rzędach jasności | model fotoreceptora |
| OmniVision, strona produktu OV9281 (ovt.com, dostęp 2026-11-05) | 1280×800 przy 120 fps, VGA przy 180 fps, 2-tor MIPI, 156 mW | F120, F180 |

## 3. Hipotezy (rejestrowane przed uruchomieniem)

- **H0 (bramka):** w wariancie GŁÓWNYM (§4.4) przy wejściu F-IDEAL spełnione G1 ∧ G2 ∧ G3 (§8) dla T4. T5 raportowany, nie wymagany.
  Przewidywanie autora: niepewne (raczej porażka bez dopasowania parametrów).
- **H1 (główna):** F120 ≡ EV-R (±SESOI) i F120 ≡ F-IDEAL dla miary P1 (§9).
- **H2 (wtórna):** po nagłym przyciemnieniu (S4) EV-R daje większy błąd odpowiedzi Mi9/Tm9 niż F120 (Ketkar 2020).
- **H3 (wtórna):** LPLC2 o pokryciu ≥ 70 % pola w wycinku: zbliżanie > max(oddalanie, przesuw) w F120 i w EV-R.
- **H4 (wtórna, nowa w d2):** przy migotaniu oświetlenia 100 Hz (S6) F120 daje fałszywy ruch/aliasing 20 Hz, EV-R nie (lub
  odwrotnie) — to realny wyróżnik kamer, którego wolne bodźce nie pokażą.

## 4. Sieć

### 4.1 Wycinki
- **S-core (główny):** §1, zamrożony.
- **S-ext (wrażliwość):** S-core + komórki typów pośrednich (Dm*, Pm*, C2, Mi13, CT1, Tm5Y, Y*) według tej samej reguły co typy
  bez hex. Rozmiar policzyć przed Etapem 0.

### 4.2 Wagi i znaki
- `sign_map = {ACh: +1, GABA: −1, Glu: −1, histamine: −1}`; wrażliwość: Glu = +1. Neurony bez NT → znak 0 (raport liczby).
- **Normalizacja (zarejestrowana, główna):** W[post, pre] = znak(pre) · g · N[post, pre] / Σ_pre N[post, pre] (udział synaps
  w wejściu z wycinka) — każdy neuron dostaje sumę bezwzględnych wag g niezależnie od tego, ile wejść wycięto. Jedno globalne g,
  ustalane wyłącznie na bodźcu S0 (ziarna kalibracyjne, przed testami DS). Wrażliwość: liniowe J0 · N z J0 = 0,275 mV (Shiu 2024),
  bez normalizacji (ryzyko nasycenia: krawędzie do 193 synaps ≈ 53 mV na impuls).

### 4.3 Model neuronu (decyzja D1, D2)
- **M-G (główny):** nieimpulsowy jak u Lappalainen: τ dV/dt = −(V − V_rest) + Σ W f(V_pre) + I; f(V) = max(V, 0).
  Parametry jednolite, niedopasowane: τ = 50 ms (ich inicjalizacja), **V_rest = +1 (jednostka umowna) dla wszystkich typów**,
  dt = 1 ms. Dodatnie V_rest oznacza toniczne wydzielanie w spoczynku, bez którego hiperpolaryzacja L1 przy świetle nie może
  odhamować Mi1/Tm3 (tor ON nie istniałby z konstrukcji). To założenie modelu, równe dla wszystkich typów, niezależne od bodźca.
  Nowy plik `graded.py` (alif.py bez zmian — przypięty sha256).
- **M-A (kontrola negatywna):** `SparseALIF` bez zmian, bez prądu spoczynkowego. Przewidywanie: brak toru ON. Służy do pokazania,
  że wynik zależy od modelu neuronu, nie tylko od danych. Jeśli właściciel zgodzi się na D2(b) — stały prąd per typ dający
  spoczynkową częstość 20 Hz — M-A+ jest wariantem wrażliwości.
- **M-L (opcjonalny, D5):** M-G z opublikowanymi parametrami per typ z Lappalainen 2024, jeśli dostępne i licencja pozwala.

### 4.4 Wariant GŁÓWNY (decyduje; reszta = wrażliwość, raportowana, bez prawa zmiany decyzji)
M-G · S-core · normalizacja udziałowa · Glu −1 · wejście E2 · tło jasne.
Wrażliwość: M-A (kontrola), M-A+ (jeśli D2), M-L (jeśli D5), S-ext, J0 liniowe, Glu +1, tło ciemne, E1 (kontrola negatywna).

## 5. Wejście: od sceny do prądu w neuronach

### 5.1 Scena i optyka
- Bodźce analityczne w kątach (az, el), zegar świata 1 kHz. Bez MuJoCo w Etapach 0–1.
- Kierunki kolumn: siatka heksagonalna z §1 (konwencja dq − dr, osie 120°), odstęp 5,1° (Behnia 2014); oś kamery w środku krążka.
  Mapa oka z danych nie jest dostępna — uproszczenie jawne.
- Piksele: odstęp 0,334° (GenX320 przy HFOV 86°) dla wszystkich kamer (równy koszt). Uwaga: przy tym uśrednieniu ~700 pikseli na
  ommatidium różnice szumu per piksel między kamerami tracą znaczenie — wyniki szumowe nie są wnioskiem o sensorach.
- Ommatidium = ważona Gaussem (FWHM 5°, Haag 2017) suma, ucięta przy ±5°, zapisana jako macierz rzadka 217 × N_pix (inaczej
  ~1,2·10¹⁰ mnożeń na próbę).

### 5.2 Emulatory kamer
| Kod | Co | Parametry (założenia; wrażliwość) |
|---|---|---|
| F-IDEAL | 1 kHz, float, bez szumu | górna granica |
| F180 | 180 fps (VGA OV9281), **10 bit**, autoekspozycja: średnia sceny = 50 % zakresu, ekspozycja ≤ okres klatki, szum fotonowy + odczytu | szumy OV9281 NIEZWERYFIKOWANE → poziom niski / wysoki |
| F120 | 120 fps, jw. | jw. |
| F40 | 40 fps (DAVIS346 APS), jw. | kontrola dolna |
| EV-R | zdarzenia z log-jasności 1 kHz na piksel, próg Δln I = 0,25 (GenX320 nominalnie 25 %), rozrzut progu σ 3 %, refrakcja piksela 1 ms, pasmo piksela: filtr 1. rzędu z opóźnieniem zależnym od jasności (0,15 ms przy 1000 lx, 1 ms przy 5 lx — CLAIM producenta), szum tła 0,1 Hz/piksel; zdarzenia całkowane z przeciekiem (τ 100 ms) do estymaty log-jasności → ten sam model fotoreceptora | rozrzut 0/3/10 %, szum 0/0,1/1 Hz, próg 0,15 |
| EV-L | zdarzenia ON/OFF wprost jako impulsy prądu do L1–L3 (pomija fotoreceptor; ON → −, OFF → +) | tylko wrażliwość |
**EV-R jest jedynym ramieniem zdarzeniowym w decyzji** (ustalone teraz, bez wyboru na pilocie — unika „klątwy zwycięzcy”).
Klatka dostępna po ekspozycji + odczycie (8,3 ms F120, 5,6 ms F180 — założenie odczyt ≈ okres); między klatkami wartość trzymana.

### 5.3 Model fotoreceptora (jedyny etap nie z danych — MODEL)
log-jasność → adaptacja dzieląca (τ_ad = 1 s) → filtr dolnoprzepustowy 2. rzędu, czas do szczytu ~12 ms (9–16 ms wg wyszukiwania
prac grupy Juusoli — CZĘŚCIOWO ZWERYFIKOWANE) → u_R(t).
**Kalibracja równa dla wszystkich ramion:** dla każdego ramienia (F-IDEAL, F180, F120, F40, EV-R, EV-L) jeden współczynnik k_arm
dobrany tak, by szczytowa zmiana prądu wejścia do L1 na S0 (pełne pole, kontrast 50 %) była taka sama jak w F-IDEAL. Kalibracja na
ziarnach 15 504 001–010, przed jakimkolwiek bodźcem ruchowym; współczynniki zapisane w manifeście.

### 5.4 Punkt wejścia (decyzja D3)
- **E2 (główny, MODEL):** I = −k_arm · u_R do L1, L2, L3 każdej kolumny przez `ModelEdge` (uzasadnienie: szczątkowe zakończenia R
  w MaleCNS, §1); znak −1 (histamina → Cl⁻); jednakowa „równoważna liczba synaps” per kolumna = mediana sumy synaps R1-R6 → L1
  (osobno L2, L3) po kolumnach, które mają jakiekolwiek wejście R na całym prawym oku.
- **E1 (kontrola negatywna):** u_R do ciał R1-R6 z wycinka, dalej synapsy z danych. Przewidywanie: ~85 % kolumn bez bodźca, brak DS.

## 6. Bodźce
| Kod | Bodziec | Parametry |
|---|---|---|
| S0 | błysk pełnego pola ON/OFF, kontrast 50 % | kalibracja, G1 |
| S1 | krawędź ON i OFF, 6 kierunków siatki | 15, 30, 60, 120, 240, 500, 1000 °/s (obrót własny ramienia do ~103 °/s wg bio2/vision.py; szybkie dla różnicowania kamer) |
| S2 | siatka sinusowa λ = 30° | TF 0,5–8 Hz (opisowo) |
| S3 | ciemny krążek: zbliżanie l/v = 10, 40, 80 ms (piłeczka 5 cm przy 0,5 m/s → 50 ms); oddalanie; przesuw tego samego rozmiaru | H3 |
| S4 | tekstura stała + nagłe przyciemnienie ×0,1 przy stałym kontraście Webera | H2 |
| S5 | tekstura stała + drgania kamery (sinus 5–20 Hz, 0,5°) + powolny obrót | fałszywy ruch/looming (opisowo) |
| S6 | oświetlenie modulowane sinusem 100 Hz (sieć 50 Hz), także 50–300 Hz, głębokość 10–50 %, scena stała i S1 60 °/s | H4 |
Tła: jasne (główne) i ciemne ×0,01 (wrażliwość — test zakresu dynamiki, osobny od testu czasowego).

## 7. Miary
- Odpowiedź: M-G średnie f(V) w oknie bodźca minus spoczynek; M-A częstość [Hz]. Komórka „reagująca”: odpowiedź > 3σ spoczynku
  w ≥ 1 kierunku; raport odsetka reagujących. DSI dla R_pref + R_null < ε = brak (nie 0) — raport liczby.
- **DSI** = (R_pref − R_null)/(R_pref + R_null), kierunek preferowany z połowy powtórzeń, DSI z drugiej połowy.
- **Oś anatomiczna T4 (G3):** dla każdego T4 wektor od środka wejść Mi9 do środka wejść Mi4 (z danych, w osadzeniu §1).
  Znak kierunku preferowanego względem tej osi NIEZWERYFIKOWANY w literaturze → G3 sprawdza tylko oś (±30°), znak raportowany.
- **Indeks polaryzacji** na S0: (R_ON − R_OFF)/(R_ON + R_OFF). Tabela oczekiwań G1 (7 typów): L1, L2 — OFF (w obu modelach
  wyjście rośnie przy ściemnieniu); Mi1, Tm3, T4 — ON; Tm1, T5 — OFF (Behnia 2014, Maisak 2013, Gengs 2002). Wyłączone: Mi4, Mi9
  (polaryzacja NIEZWERYFIKOWANA), Tm2, Tm9 (niosą też ON — Nat Commun 2021), Tm4.
- **LI LPLC2** = (R_zbliż − max(R_oddal, R_przesuw)) / (R_zbliż + max(…)), tylko dla LPLC2, których ≥ 70 % wejść od T4/T5 pochodzi
  z wycinka (liczba komórek raportowana; jeśli < 5 — H3 nie oceniane).
- **Opóźnienie modelowe:** czas od przejścia krawędzi przez środek kolumny do przekroczenia 3σ przez T4 tej kolumny.
- **H2:** błąd względny odpowiedzi Mi9/Tm9 po przyciemnieniu względem stanu sprzed przy tym samym kontraście.
- **H4:** moc widma odpowiedzi T4/T5 w paśmie aliasu (|f_mig − k·fps|) i fałszywe DSI na scenie stałej.

## 8. Kontrole i bramka Etapu 0
Kontrole: **(C1) tasowanie z zachowaniem par typów:** zamiany końców krawędzi tylko w obrębie tego samego bloku (typ pre → typ post),
zachowane stopnie, znaki i skład typów wejść; niszczy, KTÓRE komórki (kolumny) są połączone; ≥ 40 instancji (nowa funkcja,
`visual_path.shuffle` nie nadaje się — miesza typy w całej sieci). (C1b) jak C1 + obrót osi Mi9/Mi4: Mi4 i Mi9 każdego T4 zamienione
miejscami (przewidywanie: odwrócenie kierunku preferowanego). (C2) Glu +1. (C3) brak bodźca / scena stała. (C4) losowa permutacja
kolumna → kierunek w polu widzenia. (C5) S-ext.

**Bramka (wariant główny, wejście F-IDEAL), T4:**
- **G1:** polaryzacja zgodna dla ≥ 6 z 7 typów z §7.
- **G2:** dla ≥ 3/4 podtypów T4: mediana DSI ≥ 0,20 (próg bezwzględny) **i** > 95. percentyl z C1 (≥ 40 instancji).
- **G3:** dla ≥ 3/4 podtypów T4: mediana różnicy kątowej między kierunkiem preferowanym a osią Mi9–Mi4 (bez znaku) ≤ 30°.
- T5: te same miary raportowane opisowo (budowa T5 w danych jest niesymetryczna, §1).
- **Bramka nie przeszła → STOP.** Raport: „wycinek z danych w modelu M-G bez dopasowania nie liczy kierunku ruchu”. Decyzja o kamerze
  zostaje przy argumentach z przeglądu; następny krok = osobny projekt (dopasowanie parametrów lub M-L).

## 9. Etap 1 — porównanie kamer i reguły decyzji
- **P1 (jedyna miara główna):** średnia z median DSI czterech podtypów T4 na S1 przy 60, 120 i 240 °/s (tło jasne).
  Wtórne: P1 dla 500–1000 °/s, T5, LI LPLC2 (H3), H2, H4.
- **SESOI = 25 % różnicy (DATA − C1) z bramki** dla P1 (F-IDEAL, wariant główny) — wyznaczone w Etapie 0, zapisane przed
  uruchomieniem Etapu 1. Uzasadnienie: zmiana kamery uzasadniona, jeśli dotyczy co najmniej ćwierci sygnału kierunkowego, którego
  model w ogóle dostarcza (decyzja projektowa D4, nie wartość biologiczna).
- Analiza parami (ta sama jednostka = ta sama tekstura i szum sieci we wszystkich kamerach); n z pilota (ziarna 15 504 011–040):
  moc 80 % dla TOST, α = 0,05 na stronę; maks. 200 jednostek.
- **Pseudoreplikacja (jawnie):** jednostki to powtórzenia bodźca i szumu na JEDNYM wycinku jednego oka jednego osobnika. p-wartości
  dotyczą tego wycinka, nie „muchy”. Uogólnienie (inne krążki tego samego oka: 3 przesunięte środki) — wrażliwość, opisowo.

| Wynik (wariant główny, P1) | Decyzja |
|---|---|
| F120 ≡ EV-R i F120 ≡ F-IDEAL (TOST ±SESOI) | **OV9281 potwierdzona** |
| EV-R > F120 o > SESOI (jednostronnie, α = 0,05) | **zmiana na GenX320** |
| F120 < F-IDEAL o > SESOI, F180 ≡ F-IDEAL, EV-R nie lepsze od F180 o > SESOI | OV9281 w trybie VGA 180 fps |
| F120 i F180 < F-IDEAL o > SESOI, EV-R ≡ F-IDEAL | zmiana na GenX320 |
| każdy inny układ | niekonkluzywne — rekomendacja bez zmian, raport z przedziałami |
Wyniki wrażliwości i miar wtórnych są raportowane; nie zmieniają decyzji. Wyjątek zgłaszany wprost: jeśli H4 pokaże silny alias
migotania w F120 przy realnym oświetleniu, raport zaleca test oświetlenia przed zakupem (bez zmiany decyzji z P1).

## 10. Ziarna (pula zarejestrowana 2026-11-05, przed jakimkolwiek uruchomieniem)
Sprawdzenie kolizji: `grep -rElI '\b15[ _]?5[0-9]{2}[ _]?[0-9]{3}\b' flymind bio2 sim reports research_notes` → 0 plików
(przed utworzeniem tego pliku); kontrola dodatnia: wzorzec dopasowuje `15501001`.
| Pula | Użycie |
|---|---|
| 15 501 001 – 15 501 099 | testy dymne / jednostkowe (nigdy nie analizowane) |
| 15 502 001 – 15 502 040 | Etap 0: jednostki |
| 15 503 001 – 15 503 050 | Etap 0: instancje tasowania C1 / C1b |
| 15 504 001 – 15 504 010 | kalibracja g i k_arm |
| 15 504 011 – 15 504 040 | pilot Etapu 1 (SD do mocy) |
| 15 505 001 – 15 505 200 | Etap 1 potwierdzenie: jednostki (pierwsze n) |
| 15 506 001 – 15 506 050 | Etap 1: instancje tasowania |
| 15 507 001 – 15 507 003 | RNG analizy (bramka, pilot, potwierdzenie) |
| 15 509 001 – 15 509 999 | red team (ponowne symulacje) |
Na jednostkę u: szum sieci `default_rng([u, 0])`, tekstura/bodziec `[u, 1]`, szum kamery `[u, 2, crc32(kamera)]`.
Runner odmawia ziarna spoza puli danego etapu i zakresów 0–39, 300–399.

## 11. Zasoby i plan implementacji
- Sieć: ~124 tys. niezerowych wag → krok rzadki rzędu 0,1–0,2 ms (szacunek red teamu, DO POMIARU). `snn_interface.build` alokuje
  macierze gęste (4 × 5120² × 8 B ≈ 0,8 GB) — dla wycinka użyć nowego, rzadkiego buildera w `optic_slice.py` (ten sam kontrakt znaków,
  test równoważności z `build` na małej sieci); nie uruchamiać więcej niż 2 procesów naraz.
- Rzutowanie bodźca: macierz rzadka (§5.1) — warunek konieczny przed jakimkolwiek przebiegiem.
- Liczba prób bramki: 7 prędkości × 6 kierunków × 2 polaryzacje × 40 jednostek ≈ 3,4 tys. (wariant główny) + kontrole; czas
  zmierzyć w teście dymnym, przed zgodą na Etap 0.
- Nowe pliki (nic istniejącego nie zmieniane): `optic_slice.py`, `optics.py`, `cameras.py`, `photoreceptor.py`, `graded.py`,
  `shuffle_typed.py`, `runner.py` (zapis „x”, manifest sha256), `analysis.py` + po jednym `test_*.py` z samosprawdzeniem, m.in.:
  (a) hex: histogram przesunięć L1 → Mi1 = §1; (b) wycinek = 5120 neuronów; (c) emulator EV: skok jasności ×2 przy C = 0,25 daje
  floor(ln 2 / 0,25) = 2 zdarzenia ON i 0 OFF; (d) C1 zachowuje bloki typów i stopnie; (e) DSI ruchu bez sieci (wejście = kolumny)
  = 0 ± szum.
- Wyniki: `flymind/results/v1_camera/`; `.venv/bin/python -I -B`, bez importu bio2.

## 12. Decyzje właściciela przed implementacją
- **D1:** model główny nieimpulsowy M-G (odejście od ALIF w płacie wzrokowym; zgodne z biologią laminy i Lappalainen 2024)?
- **D2:** dodatnie V_rest w M-G (konieczne dla toru ON) — akceptacja? Opcjonalnie M-A+ (stały prąd 20 Hz per typ w ALIF)?
- **D3:** wejście do laminy przez krawędzie modelowe (E2), bo fotoreceptory z danych są szczątkowe — akceptacja?
- **D4:** SESOI = 25 % różnicy DATA − tasowanie z bramki — akceptacja lub inna wartość?
- **D5:** pobranie opublikowanych parametrów Lappalainen 2024 (M-L) — tak/nie?

## 13. Czego ten test NIE rozstrzyga
Prawdziwych szumów, opóźnień USB/MIPI i oświetlenia (pomiar po zakupie); mapy oka (siatka 5,1° to uproszczenie); wpływu 35–60 %
wejść spoza wycinka; zgodności z innymi osobnikami (MaleCNS = jeden samiec; pseudoreplikacja §9); siły synaps (liczba ≠ siła);
poprawności modelu fotoreceptora i wejścia E2; zachowania ramienia (test kończy się na T4/T5/LPLC2, nie na DN i serwach).

## 14. Odpowiedź na red team r1 (2026-11-05)
| # | Zarzut | Weryfikacja | Zmiana w d2 |
|---|---|---|---|
| 1 | Konwencja hex to dq − dr | potwierdzone (L1 → Mi1: (1,1) 7, (1,−1) 0) | §1, §5.1, test (a) |
| 2 | Liczby wycinka nieodtwarzalne z opisu | słuszne: opis d1 nie zgadzał się z regułą w skrypcie (mianownik = wejścia od typów z hex) | reguła zapisana dokładnie, test (b); LPLC2 obcięty → miara wtórna z kontrolą pokrycia |
| 3 | E1 prawie puste | potwierdzone (509/892 L1 z wejściem R na całym oku) | E1 = kontrola negatywna, E2 = główne |
| 4 | Bramka obalana przez konfundy (skala wag, cisza M-A) | słuszne | normalizacja udziałowa, V_rest > 0, M-A = kontrola |
| 5 | Tasowanie C1 za łatwe | potwierdzone w kodzie (`visual_path.shuffle` miesza typy) | tasowanie w blokach typów, ≥ 40 instancji, próg bezwzględny 0,20, C1b |
| 6 | G3 za słabe | słuszne | G3 = oś anatomiczna Mi9–Mi4 ±30°; T5 opisowo |
| 7 | Nierówne porównanie | słuszne co do kalibracji, wyboru EV*, 8 bit; **błędne co do VGA 180 fps** (strona OmniVision to podaje) | k_arm na S0 dla każdego ramienia, EV-R ustalone z góry, 10 bit + AE, model pasma piksela EV |
| 8 | Równoważność gwarantowana konstrukcją | słuszne | bodźce do 1000 °/s, migotanie S6 (H4), SESOI względne |
| 9 | Pseudoreplikacja, rozwidlenia, brak reguł konfliktu | słuszne | jeden wariant główny, P1 jedyna główna, pełna tabela decyzji, pseudoreplikacja jawnie |
| 10–11 | DSI 0/0, higiena ziaren | słuszne | §7, §10 |
| — | wykonalność: gęsty build 0,8 GB, rzutowanie 10¹⁰ | słuszne | rzadki builder i rzutowanie, test dymny przed Etapem 0 |
