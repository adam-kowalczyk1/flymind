# FlyMind F1 — Active sensing, etap 0 (pętla otwarta): raport końcowy

Data: 2026-11-01. Protokół: `PROTOCOL.md` r3.2 (historia: r1 odrzucony przez red team, r2 PASS_WITH_FIXES, r3 poprawki, r3.1 budżet,
r3.2 poprawki kodu). Wszystko dotyczy MODELU (sieć ALIF na okablowaniu z konektomu MaleCNS + inżynierski enkoder obrazu), nie muszki.
Brak commitów, brak sprzętu SO-101, brak zmian w plikach chronionych.

Etykiety twierdzeń (w nawiasach kwadratowych):
**[KOD]** = VERIFIED IN SOURCE CODE · **[LIT]** = SUPPORTED BY LITERATURE · **[ZAŁ]** = EXPERIMENTAL ASSUMPTION · **[HIP]** = HYPOTHESIS ·
**[WYNIK]** = OBSERVED RESULT · **[NZW]** = UNVERIFIED.

## 1. Streszczenie
- **Pytanie:** czy sterowany oscylacyjny ruch kamery poprawia wykrywanie słabych, nieruchomych celów przez SNN z konektomu
  (LC10a → pośrednie → DNa02, ALIF) i czy korzyść zależy od okablowania i od samej sieci impulsowej.
- **Odpowiedź [WYNIK]:** tak, ale nieswoiście.
  - Obrót kamery 4° z częstotliwością 0,5 Hz podnosi BSC sieci DATA z 0,325 do 0,4275: Δ +0,10 [0,07; 0,14], n = 200 świeżych
    jednostek, czyli próg odległości przesuwa się o ≈ 1,4 cm. H1 jest POTWIERDZONA.
  - Efekt utrzymuje się we wszystkich 4 wariantach odporności.
  - Sieci z przetasowanym okablowaniem (B1, SWS) zyskują tyle samo (S3, S4: równoważne).
  - Próg z filtrem dolnoprzepustowym, bez SNN, zyskuje tyle samo (S6: równoważny).
  - Gładki ruch losowy daje tyle samo co sinus (S2: równoważny).
  - Klasyczny odczyt P nie zyskuje (S5: równoważny).
  - Korzyść rośnie z amplitudą, a od częstotliwości prawie nie zależy, więc nie ma „rezonansu”.
- **Mechanizm [WYNIK diagnostyki post hoc + HIP]:** średni sygnał z enkodera się nie zmienia. Ruch okresowo przesuwa cel w stronę
  większej ekscentryczności, gdzie wagi azymutu enkodera dają większy napęd, a ostry próg impulsowy zamienia te szczyty w impulsy.
  Sieć działa jak próg na wolnym integratorze (~40–80 ms).
- **Warunki niepowodzenia:** F-b, F-c i F-d zachodzą (brak specyficzności sinusa, SNN i okablowania). F-a, F-e, F-f, F-g i F-h nie zachodzą.
- **Rekomendacja:** formalna reguła protokołu pozwala rozważyć etap 1, ale tylko jako test korzyści z wypukłości progu (inżynieria),
  nie hipotezy biologicznej. Szczegóły w §18. Zatrzymałem się zgodnie z fazą 9.
- **Integralność [WYNIK]:** Stage 1 28/28, 377 plików chronionych i 2402 pliki snapshotu bez zmian, 0 błędów runnera, testy
  35/35 i 19/19. Niezależny red team odtworzył wszystkie estymaty (PASS_WITH_ISSUES; uwagi włączone do tekstu).

## 2. Zweryfikowana architektura obecnego systemu FlyMind

```
scena MuJoCo (stół-szachownica, piłeczka r 2,5 cm, ramię w pozie loop.Q_POSE)          so101.build_mjcf, loop.place_ball
   │  kamera „eye” przymocowana do chwytaka (so101.py:143), fovy 70°, 96×128, MSAA 4
   ▼
POZA KAMERY ◄── F1: wirtualny obrót kamery wokół pionu przez środek optyczny (cam_quat modelu w pamięci; stimulus.Scene.pose)
   │  renderer.update_scene(d, camera="eye") (so101.py:221)
   ▼
obraz RGB uint8 ◄── F1: + szum pikseli σ 10 (wspólny dla wszystkich systemów; systems.pixel_noise)
   ▼
enkoder TargetEncoder (encoder.py:50–69): rozmycie 3×3, kontrast chromatyczny c = (G − (R+B)/2)/jasność (l. 62),
   próg c > c_min 0,15 (l. 63), wagi azymutu S_L = σ(az/10°), S_R = 1 − S_L, E = S·Σc (l. 65), g = 1 − exp(−E/60) (l. 66)
   ▼  g_L, g_R ∈ [0, 1) — jedna para liczb na klatkę (bez pamięci między klatkami)
prąd 12·g_s mV do KAŻDEGO LC10a strony s (encoder.currents, l. 71–76), trzymany 10 ms (loop.py:141: net.run(I, 10))
   ▼
LC10a: 135 L + 140 R (visual_path.select, typ 'LC10a', strona = somaSide)
   ▼  krawędzie z danych MaleCNS v1.0, J0 0,2, Dale z neuroprzekaźnika
147 neuronów pośrednich (≥ 5 synaps od LC10a i ≥ 5 do DNa02; visual_path.py:50)
   ▼
DNa02 L (523769), DNa02 R (10360) (visual_path.py:34)
   ▼  ALIF (alif.py): τ_m 20 ms, τ_syn 5 ms, próg −45 / spoczynek −52 mV, refrakcja 2,2 ms (3 kroki), adaptacja b_a 0,5 mV, τ_a 300 ms,
   ▼  szum prądu σ 2 mV losowany bezwarunkowo w każdym kroku (alif.py:74), dt 1 ms
ODCZYT F1 (eksperymentalny, osobny od dekodera ruchu): D = #DNa02_L − #DNa02_R w oknie 1–3 s
   ▼
DECYZJA: „lewo” jeśli D > c, „prawo” jeśli D < −c, inaczej „brak” (c z prób bez celu, FA ≤ 0,05)
(istniejący decoder.SteerDecoder — różnica częstości L−R, filtr, kalibracja kąta, decoder.py:97–99 — NIE jest używany ani zmieniany)
```

Weryfikacja twierdzeń z raportów projektu (wszystkie sprawdzone w źródle w fazie 1):
1. Wszystkie LC10a jednej strony dostają ten sam prąd — **[KOD]** encoder.py:74–75.
2. Prąd trzymany ~10 ms — **[KOD]** jedna klatka na takt 10 ms, `net.run(I, 10)` (loop.py:141).
3. Silnie wspólne wejście populacji — **[KOD]** wynika z 1.; jedynym źródłem różnic między neuronami jednej strony jest szum σ 2 mV i rekurencja.
4. Adaptacja może tłumić stałe wejście — **[KOD]** mechanizm istnieje (alif.py:81); jego wielkość w F1 — patrz wyniki neuronowe.
5. Filtrowanie czasowe — **[KOD]** enkoder nie ma pamięci; błona τ_m 20 ms i synapsa τ_syn 5 ms; dekoder ruchu ma τ_rate 50 ms + τ 0,1 s (w F1 nieużywany).
6. Martwa strefa dla słabych celów — **[WYNIK]** sonda fazy 1: piłka 0,26 m, az 8° → I_ipsi 6,02 mV → DNa02 11,5 Hz; 0,30 m → 5,05 mV → 0 Hz.
   Próg jest ostry, bo szum prądu σ 2 mV daje tylko ~0,3 mV fluktuacji napięcia (filtr błony) **[KOD + rachunek]**.
7. P lepszy od SNN — **[NZW w tej sesji]** wynik wcześniejszych etapów (V5–V7), nie powtarzany w F1 dla pętli zamkniętej.
8. Dekoder nie jest pełnym obwodem ruchowym — **[KOD]** docstring decoder.py: stałe modelu z bio2, kalibracja liniowa.
Dodatkowe fakty: scena nie jest lustrzanie symetryczna (przechył kamery ≈ 2,3°, światło kierunkowe, szachownica) — ipsilateralne g dla celu
±10° różni się o 5–7 % **[WYNIK, test T2]**; kamera jest pochylona ~34° w dół, więc obrót wokół osi „góra obrazu” przesuwa namiar
o θ/cos(34°) — dlatego F1 obraca wokół pionu świata, co daje dokładnie namiar = az0 − θ (błąd 3,6e-16 rad, test T6) **[WYNIK]**.

**Gdzie wchodzi active sensing:** wyłącznie w pozie kamery przed renderem (implementacja A, wirtualna kamera). Robot, piłeczka i stół
są statyczne (fizyka nie jest krokowana; test T6: pozycja piłeczki stała). Wszystko za renderem jest niezmienione.

## 3. Podstawy naukowe
- Rezonans stochastyczny: słaby sygnał podprogowy może być lepiej przenoszony przez układ progowy z dodanym szumem; zależność od natężenia
  szumu jest niemonotoniczna **[LIT: Gammaitoni i in. 1998, Rev. Mod. Phys. 70:223]**. W F1 ruch jest deterministyczny (sinus), a enkoder
  jest bez pamięci z twardym progiem — to raczej *dithering* niż SR w ścisłym sensie; etykiety „SR” używam tylko jako analogii
  **[LIT: McDonnell i Abbott 2009, PLoS Comput Biol — przestroga przed nadużywaniem terminu]**.
- Nadprogowy SR (populacja niezależnych progów + szum) **[LIT: Stocks 2000, PRL 84:2310]** — w F1 populacja LC10a dostaje IDENTYCZNY prąd
  na stronę, więc mechanizm Stocksa (niezależne szumy) działa tylko przez mały szum σ 2 mV; analogia słaba.
- Active sensing: ruchy czuciowe regulujące „poślizg” bodźca u Eigenmannia (pętla zamknięta) **[LIT: Biswas i in. 2018, Curr Biol 28:4029]**;
  oscylacje ciała ryb przy słabym bodźcu **[LIT: Stamper i in. 2012, J Exp Biol 215:1567]**; aktywne próbkowanie w chemotaksji larw
  **[LIT: Gomez-Marin i in. 2011, Nat Commun 2:441 — węch, nie wzrok; słaba analogia]**.
- Mikroruchy oka: stabilizacja obrazu siatkówkowego pogarsza rozróżnianie wysokich częstości przestrzennych **[LIT: Rucci i in. 2007,
  Nature 447]**; ruchy fiksacyjne przeciwdziałają adaptacji i zanikowi percepcji **[LIT: Martinez-Conde i in. 2004, 2013, Nat Rev Neurosci]**;
  mikrosakady fotoreceptorów Drosophila i hiperostrość **[LIT: Juusola i in. 2017 eLife; Kemppainen i in. 2022 PNAS — wyniki autorów,
  nie replikowane niezależnie, wg weryfikacji]**; mięśnie ruszające siatkówkę u muszki **[LIT: Fenk i in. 2022 Nature, tylko tytuł zweryfikowany]**.
- Adaptacja jako filtr górnoprzepustowy **[LIT: Benda i in. 2005 J Neurosci]**; dla τ_a 300 ms róg pierwszego rzędu ≈ 0,5 Hz — rachunek
  własny, nie z literatury **[HIP]**.
- Teoria detekcji sygnałów: d', ROC, kryterium **[LIT: Green i Swets 1966; Macmillan i Creelman]**.
- Refrakcja / czas martwy a statystyka wyładowań **[LIT: Teich, Matin i Cantor 1978, JOSA 68:386 — najbardziej prawdopodobna pozycja
  „Teich 1978”; treść abstraktu NZW]**.
- LC10 reagują na małe RUCHOME obiekty, ich aktywacja wywołuje orientację **[LIT: Ribeiro i in. 2018 Cell 174:607]**; wzmocnienie LC10a
  zależne od pobudzenia seksualnego **[LIT: Hindmarsh Sten i in. 2021 Nature 595:549]**. W modelu F1 LC10a NIE ma selektywności ruchu
  (enkoder kolorowy bez pamięci) **[KOD]** — biologiczny argument „LC10 wolą ruch” NIE przenosi się na ten model.

## 4. Przegląd literatury i stanu wiedzy (szczegóły: `literature/f1_literature_verification.md`)
Weryfikacja bibliograficzna: subagent sprawdził metadane w Crossref i abstrakty w PubMed; ja sprawdziłem wyrywkowo Viollet 2014 i Stocks
2000 w Crossref (zgodne). Najważniejsze poprawki listy wyjściowej:
| Pozycja | Stan | Co wspiera | Czego NIE wspiera |
|---|---|---|---|
| Biswas i in. 2018 | poprawna | ruchy czuciowe regulowane w pętli | otwartej pętli F1 (analogia) |
| Gomez-Marin i in. 2011 | poprawna | aktywne próbkowanie przy decyzji | wzroku (to węch larw) |
| Gammaitoni i in. 1998 | poprawna | ramy SR | deterministycznego ditheru (to nie SR) |
| Krstić i Wang 2000 | poprawna bibliogr., treść z drugiej ręki | perturbacja + demodulacja (extremum seeking) | czegokolwiek neuronalnego (analogia z teorii sterowania) |
| Viollet 2014 | **jeden autor** („et al.” błędne) | wibrujące czujniki hiperostre | wykrywania słabego celu przez SNN |
| He i in. 2024 | **niejednoznaczne**; najbardziej prawdopodobne Sci Robot 9:eadj8124 (kamera zdarzeniowa z wirującym pryzmatem) | sterowany ruch czujnika | sensorów klatkowych i SNN z konektomu |
| Stocks 2000 | poprawna | SR nadprogowy w populacji | identycznego wejścia populacji (F1) |
| Teich 1978 | **niejednoznaczne**; najpewniej Teich, Matin, Cantor (JOSA 68:386) | refrakcja w wyładowaniach | — (abstrakt NZW) |
| Maimon i in. 2010 | poprawna | wzmocnienie zależne od stanu (lot) | F1 (nie dotyczy ruchu czujnika) |
Przeszukanie stanu wiedzy (szczegóły w pliku): fly-inspired micro-scanning (VODKA, Juston 2014, Colonnier 2015), kamery zdarzeniowe
z ruchami fiksacyjnymi (Testa i in. 2023 Sci Rep; He i in. 2024), sakady w N-MNIST (Orchard 2015), modele konektomowe (Shiu i in. 2024,
Lappalainen i in. 2024). Nie znaleziono pracy łączącej sterowany ruch czujnika, SNN z konektomu i kontrolę z tasowaniem sieci — to NIE
jest twierdzenie o nowości (przeszukanie nie było wyczerpujące) **[NZW]**. Literatura nie łączy LC10a z DNa02 — ta ścieżka pochodzi
z naszej analizy danych konektomu **[KOD: visual_path.select]**.

## 5. Hipotezy centralne
- **H1 [HIP]** Sterowany sinusoidalny obrót kamery (f*, A*) zwiększa BSC sieci DATA względem kamery stacjonarnej o ≥ 0,07 (= 1 cm
  przesunięcia progu odległości).
- **S1/S2 [HIP]** Korzyść jest specyficzna dla sinusa: większa niż dla J_shuf (te same wartości θ, losowa kolejność) i J_vel (dopasowane
  RMS przemieszczenia i prędkości).
- **S3/S4 [HIP]** Korzyść zależy od okablowania: Δ(DATA) ≠ Δ(B1), Δ(DATA) ≠ Δ(SWS).
- **S5 [HIP]** Klasyczny odczyt P na własnym zakresie (kontrast) NIE zyskuje na ruchu.
- **S6 [HIP]** Korzyść SNN różni się od korzyści dopasowanego progu z filtrem dolnoprzepustowym (TH_LP) — tj. nie wynika z samej
  wypukłości progu.
- Przewidywanie mechanistyczne z wcześniejszego programu: DATA desynchronizuje LC10a względem B1 → interakcja z refrakcją → DATA może
  korzystać inaczej **[HIP]**.

## 6. Dokładny protokół etapu 0 (skrót; pełny tekst `PROTOCOL.md` r3.2)
- Próba: 3 s, 300 klatek po 10 ms, 10 kroków SNN (1 ms) na klatkę; okno analizy 1–3 s (całkowite liczby okresów dla każdego f).
- Jednostka u (próbka statystyczna): losuje ρ_u ~ U[0,22; 0,36] m, |az|_u ~ U[8°; 12°], k_u ~ U[0,04; 0,24], fazę φ_u ~ U[0, 2π);
  ten sam bodziec we wszystkich warunkach (parowanie); cel lewy (+az), prawy (−az), brak celu.
- Ruch: θ(t) = A·sin(2πft + φ_u), obrót wokół pionu przez środek optyczny; θ > 0 = kamera w lewo; namiar = az0 − θ **[KOD, test T6]**.
- Szum: piksele σ 10 (wspólny), ALIF σ 2 mV (ziarno u, identyczny ciąg szumu dla wszystkich sieci — **[KOD, test CRN]**).
- Odczyt i decyzja: §2 powyżej; BSC = ½[P(lewo|lewy) + P(prawo|prawy)], „brak” = błąd. Przy równomiernym ρ BSC jest estymatorem
  Spearmana–Kärbera położenia progu (ΔBSC × 0,14 m = przesunięcie progu), o ile spełnione są warunki brzegowe i monotoniczności (§5).

## 7. Macierz eksperymentu
| Etap | Jednostki | Sieci | Warunki ruchu | Zakresy |
|---|---|---|---|---|
| 0A pilotaż cz. 1 | 9 101 001–060 | DATA, 5 B1, 5 SWS | stat + 16 sinusów (f 0,5/1/2/4 × A 0,5/1/2/4°) | D, C |
| 0A pilotaż cz. 2 | te same | j.w. | J_shuf(A*), J_rms(A*), J_vel(f*, A*) | D, C |
| 0B/0C potwierdzenie | 9 102 001–200 | DATA; 10 B1, 10 SWS (świeże) | DATA: stat, 16 sin, J_shuf, J_rms, J_vel, MT; B1/SWS: stat, sin*, J_shuf, J_rms, J_vel | D (+C dla warunków kluczowych) |
| 0D odporność | 9 103 001–200 | DATA, B1, SWS | stat, sin*, J_shuf | D; 4 warianty |
Z pilotażu (reguły mechaniczne): f* = 0,5 Hz, A* = 4°, n = 200, θ_TH = 6,00 mV, θ_TH_LP = 5,93 mV, zakresy bez zmian.

## 8. Kontrole
| Kontrola | Co rozstrzyga | Etykieta |
|---|---|---|
| kamera stacjonarna | punkt odniesienia | — |
| J_shuf: sinus z przetasowanymi klatkami | struktura czasowa vs sam rozkład amplitud (te same szczyty) | [ZAŁ] |
| J_rms: biały jitter, dopasowane RMS (okno) | wymagana przez zlecenie; szczyty ~2A — niesprawiedliwy przy progu | [ZAŁ] |
| J_vel: jitter dolnoprzepustowy, dopasowane RMS przemieszczenia i prędkości | periodyczność vs ruch aperiodyczny | [ZAŁ] |
| MT: ruchomy cel, kamera stoi | czy ruch tła/chwytaka coś wnosi | [ZAŁ] |
| P (filtr klasycznego regulatora z loop.py) | czy odczyt liniowy zyskuje | [KOD] |
| TH: próg bez pamięci, TH_LP: próg po filtrze τ 20 ms (progi dopasowane w pilotażu) | czy SNN ≠ sama nieliniowość progu | [ZAŁ] |
| LIN: liniowy kontrast bez progu c_min | odniesienie zerowe | [ZAŁ] |
| B1 (tasowanie bloku LC10a×LC10a), SWS v2 | zależność od okablowania | [KOD: block_shuffle, side_shuffle] |
Nie wykonano: pojedynczego neuronu LIF z adaptacją jako zastępnika (sugestia red teamu) — ograniczenie.

## 9. Plan statystyczny
Bootstrap sparowany po jednostkach (10 000), kryteria szacowane w każdej replikacji; dla B1/SWS bootstrap hierarchiczny (instancje, potem
jednostki). Klasyfikacja (pierwsza pasująca reguła): SUPPORTED → HARMFUL → EQUIVALENT (CI90 w ±0,07, ramiona mierzalne i ważne SK) →
DETECTABLE-BELOW-SESOI → UNMEASURABLE → INCONCLUSIVE. H1 jeden test α 0,05; S1–S6 rodzina Holma (6). Wielkość próby z pilotażu: wymagane
n ≤ 177 dla wszystkich testów → minimum protokołu 200; przewidywana moc ≥ 0,93. Brak spojrzeń pośrednich, brak wykluczeń odstających.

## 10. Integralność i odtwarzalność
- Manifesty (`manifest_pilot.json`, `manifest_pilot2.json`, `manifest_confirm.json`, …): sha256 protokołu, kodu F1, zamrożonych zależności
  FlyMind i plików danych, HEAD gita, wersje oprogramowania; runner odmawia startu przy niezgodności; hash manifestu zapisany w każdym
  pliku jednostki (od pilot2).
- `integrity_v5v41.py --compare` (Stage 1 28/28, manifesty v5v3/v5v4, 377 plików chronionych) i `integrity_f1.py` (2402 pliki flymind/
  poza experiments/, bio2/, data/, assets/ względem snapshotu sprzed F1) — przed i po każdym etapie.
- `python -I -B` wszędzie (także procesy robocze), brak importu bio2 (test), pliki wyników w trybie „x”, rejestr ziaren `SEED_REGISTRY.md`.

## 11. Opis implementacji (`flymind/experiments/f1_active_sensing/`)
`stimulus.py` (ruch, wirtualna kamera, MT, cache renderów) · `systems.py` (szum pikseli, enkoder, SNN + miary neuronowe, P/TH/TH_LP/LIN) ·
`runner.py` (zadanie = jednostka; zapis atomowy; wznawialny) · `analysis_core.py`, `analysis.py` (reguły pilotażu, testy, klasyfikacja) ·
`figures.py` (wykresy i odtworzenie z zapisanych danych) · `manifest.py`, `integrity_f1.py` · `tests/test_f1.py`, `tests/test_analysis.py`.
Żaden plik poza tym katalogiem nie został zmieniony **[WYNIK: integrity_f1 OK]**.

## 12. Wyniki testów
- `tests/test_f1.py` **35/35 PASS** (T1–T12, MT, cache A1, maska B1, integralność, CRN, TH_LP, P, brak importu bio2) **[WYNIK]**.
- `tests/test_analysis.py` **19/19 PASS** (kryterium, BSC, AUC/d', MI, Holm, klasyfikacja, SK, bootstrap hierarchiczny) **[WYNIK]**. Po etapie 0D jeden test
(wyrównanie jednostek smoke) padł, bo jego filtr `unit >= 9108030` obejmował nowsze jednostki smoke 9108040–041; zawęziłem filtr do
030–033 (zmiana tylko w teście, kod analizy bez zmian) → 19/19.
- Jedna niewyjaśniona porażka testu cache renderów (A1) w trakcie walidacji: przy kolejnych 3 uruchomieniach i teście obciążeniowym
  (8700 klatek) 0 niezgodności. Przyczyny nie ustalono **[NZW]**. Zabezpieczenie: runner w każdej jednostce porównuje 10 klatek z cache
  z renderem od zera (`render_checks` w npz). W potwierdzeniu i odporności wszystkie kontrole zgodne **[WYNIK: 0 błędów runnera]**.
- Smoke (9 108 001–099) przed każdym etapem: OK. Integralność przed i po każdym etapie: Stage 1 28/28, 377 plików chronionych bez zmian,
  2402 pliki snapshotu sprzed F1 bez zmian **[WYNIK]**.

## 13. Rzeczywiste wyniki (potwierdzenie, n = 200 świeżych jednostek; `results/analysis_confirm.json`)
Wszystko poniżej to wynik modelu, nie muszki. CI = 95 % bootstrap sparowany (10 000).

**H1 — POTWIERDZONA [WYNIK].** BSC sieci DATA: kamera stacjonarna 0,325 → sinus (0,5 Hz, 4°) 0,4275; Δ = **+0,103 [0,068; 0,140]**,
p = 0,0001; przesunięcie progu odległości ≈ **+1,4 cm** (ρ₅₀ dalej o 1,4 cm, ≈ 5 % progu). Oba ramiona mierzalne, warunki SK spełnione.
Klasa SUPPORTED wymaga (§8) CI95 > 0 i estymaty ≥ 0,07 — spełnione; dolna granica CI95 (0,0675) leży jednak tuż PONIŻEJ SESOI, więc
wykluczenia efektu mniejszego niż 1 cm nie ma. Niezależny red team (`redteam/results_redteam.md`) odtworzył własnym kodem wszystkie
estymaty H1 i S1–S6 co do cyfry **[WYNIK]**.

**Ale korzyść nie jest specyficzna — prawie wszystkie testy specyficzności dają równoważność [WYNIK]:**
| Test | Δ (CI95) | Holm p | Klasa | Wniosek |
|---|---|---|---|---|
| S1 sinus − J_shuf | +0,065 [0,043; 0,090] | 0,0006 | DETECTABLE-BELOW-SESOI | dodatni; estymata tuż pod SESOI, SESOI nie wykluczone — wolna struktura czasowa częściowo ma znaczenie |
| S2 sinus − J_vel | 0,000 [−0,018; 0,018] | 1 | EQUIVALENT | periodyczność nie ma znaczenia; liczy się gładki ruch |
| S3 ΔDATA − ΔB1 | −0,020 [−0,060; 0,015] | 1 | EQUIVALENT | brak zależności od okablowania LC10a×LC10a |
| S4 ΔDATA − ΔSWS | −0,020 [−0,058; 0,013] | 1 | EQUIVALENT | brak zależności od stron |
| S5 ΔP (zakres C) | +0,010 [−0,018; 0,035] | 1 | EQUIVALENT | odczyt liniowy P nie zyskuje |
| S6 ΔDATA − ΔTH_LP | −0,003 [−0,025; 0,018] | 1 | EQUIVALENT | **próg z filtrem 20 ms zyskuje tyle samo co SNN** (dla wolnego sinusa; dla jitteru TH_LP zyskuje więcej — patrz mechanizm) |
Kontrole ważności: kamera vs ruchomy cel (MT) −0,010 [−0,025; 0,005] — równoważne (efekt to ruch obrazu celu, nie ruch tła/chwytaka);
P sinus − J_shuf (C) i TH sinus − J_shuf (D) — równoważne (oczekiwane dla układów bez pamięci) **[WYNIK]**.

Warunki niepowodzenia (§9 protokołu): F-a (H1 nie potwierdzona) — nie; **F-b brak specyficzności sinusa — TAK (przez S2: brak
specyficzności periodyczności; S1 wskazuje częściową zależność od wolnej struktury czasowej); F-c nie specyficzne dla
SNN — TAK; F-d brak specyficzności okablowania — TAK**; F-e wąski efekt — nie (11/16 komórek siatki > 0 po Holmie); F-f wyładowania
bez informacji — nie; F-h porażka jednej strony — nie **[WYNIK]**.

**Odpowiedź częstotliwościowa (siatka 4 × 4, DATA) [WYNIK]:** korzyść rośnie z amplitudą (A 0,5° ≈ 0; 1° ≈ +0,02; 2° ≈ +0,04;
4° ≈ +0,08–0,10) i prawie nie zależy od częstotliwości (A 4°: 0,5 Hz +0,103, 1 Hz +0,103, 2 Hz +0,095, 4 Hz +0,080). Tylko 4 komórki
z A = 4° przekraczają SESOI (SUPPORTED); komórki A 1–2° są wykrywalnie > 0, ale w ±SESOI (klasyfikowane EQUIVALENT zgodnie z kolejnością
reguł protokołu). Brak maksimum wewnętrznego (nie ma krzywej „rezonansowej”) — f* = 0,5 Hz jest słabo zidentyfikowane.

**Detekcja sygnałów (DATA, zakres D) [WYNIK]:** kryterium c = 0 (FA = 0 w próbach bez celu we wszystkich warunkach; patrz ograniczenia);
trafienia L/P 0,35/0,30 → 0,455/0,40; d'(L vs P, z AUC) 1,06 → 1,39; informacja wzajemna bodziec–odpowiedź 0,33 → 0,43 bit; udział
odpowiedzi „brak” 0,675 → 0,573. Błędów strony praktycznie nie ma — DNa02 kontralateralny milczy (0 impulsów) we wszystkich warunkach;
porażki to wyłącznie „brak” odpowiedzi. FA = 0 dla DATA we WSZYSTKICH warunkach (D = 0 w każdej z 200 prób bez celu na warunek;
sprawdzone niezależnie) — ruch nie podnosi fałszywych alarmów w tej scenie, ale dopasowanie FA jest puste (górna granica 95 % ≈ 1,5 %).
Wrażliwość na kryterium (opisowa): Δ = +0,10 dla c ≤ 5, +0,07 dla c = 10, +0,04 dla c = 20 impulsów — przy ostrzejszej decyzji
korzyść maleje, bo ruch dodaje głównie krótkie paczki impulsów. Próg ρ₅₀ (Spearman–Kärber, 0,22 m + BSC × 0,14 m): stacjonarnie ≈ 26,6 cm, z ruchem ≈ 28,0 cm.

**Miary neuronowe (opisowe, DATA, średnia po próbach z celem) [WYNIK]:** LC10a ipsi 381 → 421 impulsów/2 s (+40 [30; 51]);
pośrednie +23 [16; 31]; DNa02 ipsi +1,9 [1,2; 2,7]; synchronia LC10a 0,050 → 0,067; latencja decyzji 205 → 432 ms (+99 [46; 158]) —
wyładowania pojawiają się w paczkach w fazie, gdy cel jest najbardziej ekscentryczny (patrz odtworzenie); amplituda składowej f* DNa02
≈ 10,7 Hz. DATA ma niższą synchronię LC10a niż B1/SWS (0,05 vs 0,14 stacjonarnie) i więcej impulsów DNa02 (20,5 vs 15,5) — zgodnie
z wcześniejszym programem — ale ta różnica NIE przekłada się na różną korzyść z ruchu (S3/S4) **[WYNIK]**.

**Instancje kontrolne [WYNIK]:** Δ DATA (+0,103) jest na 12. miejscu z 21 sieci (10 B1 + 10 SWS + DATA) — w środku rozkładu.
Δ poszczególnych instancji (po 20 jednostek) 0,025–0,275, ale ta sama rozpiętość występuje dla DATA na tych samych jednostkach —
zmienność pochodzi z bodźców, nie z sieci.

**Mechanizm (diagnostyka eksploracyjna post hoc, NIE część zamrożonego protokołu; moja i red teamu) [WYNIK + HIP]:**
- Średni napęd enkodera g_ipsi w oknie praktycznie się nie zmienia (stat 0,458; sinus 0,457 ≈ 5,50 → 5,48 mV), rośnie średnie maksimum
  (0,473 → 0,508; ≈ 5,68 → 6,10 mV). Napęd ipsi koreluje z θ (r ≈ −0,98, red team): gdy kamera skręca w prawo, cel jest bardziej
  ekscentryczny i rampa wag σ(az/10°) daje większe g. Napęd szczytowy ≥ ~5,9 mV rozdziela trafienia od chybień (AUC 0,999, red team)
  **[WYNIK]**.
- Interpretacja **[HIP, zgodna z danymi]**: korzyść = rampa ekscentryczności enkodera × ostry efektywny próg sieci (~5,9 mV; szum błony
  ~0,3 mV). Ruch nie dodaje sygnału; okresowo przesuwa cel tam, gdzie wzmocnienie enkodera jest większe, i szczyty przekraczają próg.
  Odtworzenie (jednostka 9 102 003) to pokazuje: paczki LC10a pojawiają się tylko przy maksymalnym namiarze.
- To NIE jest próg bez pamięci: TH bez pamięci daje sinus − J_shuf = +0,005, a DATA +0,065 (S1). DATA ma też tę samą BSC dla J_shuf i J_rms
  (0,3625), choć szczyty J_rms są ~2× wyższe — liczy się czas przebywania przy szczycie, nie jego wysokość. TH_LP z τ 20 ms przecenia
  odpowiedź DATA na jitter (J_shuf 0,4075, J_rms 0,420 vs 0,3625); według red teamu τ 40–80 ms pasuje lepiej. Sieć zachowuje się więc
  jak próg na WOLNIEJSZYM integratorze. Równoważność S6 dotyczy wolnego sinusa i progu θ_LP dopasowanego do BSC DATA w spoczynku.
- Efekt zależy od punktu pracy: dla TH Δ ≈ 0,005–0,01 przy progach 4 i 8 mV (sufit/podłoga) wobec 0,10–0,18 przy 5–7 mV (red team).
  Liniowy odczyt P ma BSC = 1,0 na całym zakresie D — korzyść z ruchu odzyskuje część straty, którą wprowadza sam próg impulsowy
  **[WYNIK]**.
- Δ trafień wg tercyli |az| jest płaska (0,104 / 0,114 / 0,090; red team) **[WYNIK]**.
- Erratum do PROTOCOL.md §8 (plik zamrożony, nie zmieniam): „prędkość J_shuf 3–12× większa od sinusa” — dla f* = 0,5 Hz zmierzony
  stosunek RMS prędkości to 21–24× (sprawdzone na 50 jednostkach) **[WYNIK]**.

**Odporność 0D (n = 200 świeżych jednostek na wariant, 9 103 001–200; `results/analysis_robust.json`) [WYNIK]:**
| Wariant | DATA stat → sin | Δ DATA (CI95) | Δ B1 | Δ SWS | Δ TH_LP | Δ DATA J_shuf |
|---|---|---|---|---|---|---|
| |az| 4–8° | 0,235 → 0,360 | +0,125 [0,088; 0,168] | +0,158 | +0,153 | +0,155 | +0,060 |
| |az| 12–16° | 0,503 → 0,623 | +0,120 [0,090; 0,153] | +0,118 | +0,125 | +0,135 | +0,043 |
| piłka 0,72 r | 0,138 → 0,280 | +0,143 [0,100; 0,188] | +0,173 | +0,165 | +0,155 | +0,073 |
| szum pikseli σ 20 | 0,400 → 0,485 | +0,085 [0,058; 0,115] | +0,103 | +0,098 | +0,105 | +0,030 |
Korzyść DATA z sinusa ma CI95 > 0 i klasę SUPPORTED we wszystkich 4 wariantach → **F-g nie zachodzi**. W każdym wariancie sieci
tasowane i TH_LP zyskują tyle samo lub więcej (opisowo; 0D nie ma testów różnic), a J_shuf daje DATA mniej niż sinus — ten sam obraz
co w potwierdzeniu. FA DATA = 0 także przy σ 20. P i LIN są na suficie zakresu D (UNMEASURABLE). Efekt nie jest więc artefaktem
jednego zakresu azymutu, rozmiaru celu czy poziomu szumu.

## 14. Demonstracja wizualna (`figures/confirm/`; wszystko z zapisanych danych potwierdzenia)
- `frequency_response.png` — ΔBSC DATA vs f dla 4 amplitud z CI95 i pasmem ±SESOI.
- `detection_performance.png` — krzywe psychometryczne (trafienia vs ρ lub k) dla DATA, B1, SWS, P (zakres C), TH_LP; warunki stat,
  sinus*, J_shuf, J_rms, J_vel, MT.
- `effects_forest.png` — wszystkie testy prerejestrowane z CI95 i klasą.
- `neural_measures.png` — impulsy, synchronia, latencja wg warunku i sieci (opisowe).
- `replay_stationary_vs_sinusoid.mp4` (10 s, 300 klatek) + `replay_frame_000/150/299.png` — jednostka 9 102 003 (reguła wyboru z góry:
  najniższy numer jednostki z błędem stacjonarnie i trafieniem z sinusem, cel lewy). Obrazy wejściowe, θ i namiar, raster LC10a/pośrednich,
  skumulowane DNa02 L/R, bieżące D i decyzja. Odtworzenie jest ponowną symulacją; skrypt sprawdza bit w bit g i D względem zapisanych
  wyników i przerywa przy niezgodności **[WYNIK: zgodne]**. Ta jednostka jest **wybrana jako przykład korzyści** — nie jest typowa
  (większość jednostek ma ten sam wynik w obu warunkach). Uwaga: obrót 4° przesuwa piłkę o ok. 5 px z 128 — ruch na filmie jest subtelny.

## 15. Wyniki negatywne i niejednoznaczne
- **Brak specyficzności okablowania (S3, S4 równoważne):** tasowane sieci zyskują tyle samo. Hipoteza „DATA desynchronizuje LC10a →
  inna korzyść” — obalona dla tego zadania **[WYNIK]**.
- **Brak specyficzności SNN (S6 równoważny):** próg z filtrem 20 ms odtwarza efekt. SNN nie jest potrzebny do wyjaśnienia korzyści **[WYNIK]**.
- **Brak specyficzności sinusa (S2 równoważny; S1 < SESOI):** dowolny gładki ruch o tym samym zakresie działa tak samo **[WYNIK]**.
- **Brak rezonansu:** brak optimum częstotliwości; zależność monotoniczna od amplitudy. Termin „rezonans stochastyczny” nie pasuje —
  to deterministyczne przekraczanie progu przez szczyty modulacji **[WYNIK + HIP]**.
- P na zakresie C nie zyskuje (równoważne) — odczyt liniowy z całkowaniem nie korzysta z modulacji o zerowej średniej **[WYNIK]**.
- Pilotaż sugerował, że B1/SWS zyskują więcej niż DATA (+0,21/+0,19 vs +0,14); potwierdzenie tego nie powtórzyło (−0,02, równoważne) —
  pilotaż (n = 60) był szumem **[WYNIK]**.

## 16. Ograniczenia
- **Model, nie muszka:** enkoder jest inżynierski (kolor, bez pamięci, bez selektywności ruchu); prawdziwe LC10 reagują na ruch, więc
  wynik nie mówi nic o biologii aktywnego widzenia **[KOD]**.
- **FA = 0:** scena bez dystraktorów i bez fałszywych celów; kryterium c = 0. W scenie z dystraktorami ruch mógłby podnieść FA **[ZAŁ]**.
- **Jedna sieć DATA:** wnioski o okablowaniu odnoszą się do jednej realizacji z J0 0,2; porównanie z 20 kontrolami **[ZAŁ]**.
- **Mechanizm zależy od geometrii:** zysk pochodzi z przejść celu przez korzystniejszy azymut i z ostrego progu; inne |az|, ρ, rozmiar
  — patrz odporność 0D. Odpowiedź może zniknąć przy innym kształcie wag azymutu **[HIP]**.
- **f* słabo zidentyfikowane:** płaska odpowiedź częstotliwościowa; wybór 0,5 Hz przez regułę argmax nie oznacza optimum.
- **Tylko pętla otwarta, wirtualna kamera:** brak bezwładności, rozmycia ruchu, opóźnień serw, sprzężenia z ruchem ramienia.
- **Brak zastępnika LIF z adaptacją** (sugestia red teamu) — S6 używa TH_LP; nie sprawdzono, czy pojedynczy neuron ALIF wystarcza.
- **Jedna niewyjaśniona porażka testu cache (A1)** — kontrolowana w trakcie biegu, przyczyna nieznana.
- **Zakres testu:** pojedynczy poziom szumu pikseli (σ 10; σ 20 w 0D), jeden kolor celu, statyczna scena, okno 2 s.
- **Latencja:** ruch wydłuża czas do pierwszej decyzji (+99 ms) — w pętli zamkniętej to koszt.

## 17. Propozycja etapu 1 (TYLKO projekt; nic nie zostało zaimplementowane ani uruchomione)
Uzasadnienie: efekt istnieje w modelu (+1,4 cm progu), ale jest progowy i nieswoisty, więc etap 1 ma sens tylko jako test inżynierski
„czy mały ruch czujnika pomaga sterowaniu”, nie jako test hipotezy biologicznej **[HIP]**.
1. **Generacja ruchu:** gładki ruch odchylenia kamery (ostatni przegub nadgarstka lub wirtualny offset w sterowaniu), amplituda 2–4°,
   0,5–1 Hz; jako kontrola — gładki ruch losowy o tym samym widmie (J_vel), skoro S2 nie wykazał różnicy.
2. **Interakcja z regulatorem:** ruch czuciowy dodawany do polecenia po dekoderze ruchu, nigdy do jego wejścia; dekoder dostaje namiar
   skorygowany o znaną fazę ruchu (efference copy: bearing_obs + θ_cmd), żeby oscylacja nie była interpretowana jako błąd celu.
3. **Unikanie oscylacji pętli:** pasmo regulatora ≤ 1/3 f ruchu albo filtr notch przy f; ograniczenie wzmocnienia; test stabilności
   w symulacji (margines fazy) przed sprzętem.
4. **Rozdzielenie pętli:** pętla czuciowa (stała, sterowana w otwartej pętli, znana θ_cmd) oddzielona od pętli ruchowej (namiar →
   skręt); ruch czuciowy włączany tylko gdy D = 0 (brak decyzji) i wyłączany po detekcji — „szukaj, potem śledź”.
5. **Ruch użyteczny vs niekontrolowany:** porównanie z (a) kamerą statyczną, (b) J_vel, (c) zarejestrowanym ruchem niezamierzonym
   (drgania serw) odtworzonym jako ruch czuciowy; miara: próg wykrycia, czas do decyzji, błąd końcowy chwytu.
6. Wszystko najpierw w symulacji MuJoCo z nowymi ziarnami; sprzęt SO-101 dopiero po osobnej zgodzie.

## 18. Rekomendacja
- **Reguła zamrożona (PROTOCOL §9):** „rozważyć etap 1” ⇔ H1 SUPPORTED i nie F-g i nie F-h. Spełnione (H1 SUPPORTED, F-g nie, F-h nie)
  **[WYNIK]**. Ponieważ zaszło F-c, protokół wymaga sformułowania: etap 1 testowałby **korzyść z wypukłości progu**, nie korzyść
  specyficzną dla SNN ani dla konektomu.
- **Co etap 0 pokazał [WYNIK]:** sterowany ruch kamery (4°, 0,5 Hz) przesuwa próg wykrycia o ≈ 1,4 cm (BSC +0,10 [0,07; 0,14], FA = 0,
  scena bez dystraktorów), odpornie na 4 warianty. Ten sam zysk dają sieci tasowane, próg z filtrem dolnoprzepustowym i gładki ruch
  losowy. To efekt „wzmocnienie enkodera zależne od ekscentryczności × próg impulsowy”, nie aktywne widzenie z konektomu i nie rezonans.
- **Moja rekomendacja [HIP/ocena]:** NIE prowadzić etapu 1 jako testu hipotezy biologicznej ani specyficzności konektomu — etap 0 ją
  obalił dla tego modelu. Etap 1 (wg §17, w symulacji) ma sens tylko jako pytanie inżynierskie: czy mały ruch czujnika w trybie
  „szukaj” pomaga robotowi wykrywać słabe cele, przy koszcie ~100 ms latencji. Wtedy kontrolą obowiązkową jest TH_LP (τ 40–80 ms),
  bo daje ten sam zysk prościej.
- Bardziej wartościowa alternatywa: enkoder z selektywnością ruchu (jak prawdziwe LC10) — wymaga nowego protokołu.
- **Zatrzymuję się tutaj (faza 9).** Bez etapu 1, bez zmian w plikach chronionych, bez sprzętu, bez commitów — czekam na decyzję.
