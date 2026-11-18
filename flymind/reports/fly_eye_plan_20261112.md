# FlyMind — plan „oko muchy” zamiast encodera koloru (tylko na papierze)

Data: 12 XI 2026 · Autor: Claude (Opus 5.5) · Podstawa: decyzja Adama z 12 XI (odpowiedź „Yes, plan fly eye” na pytanie z raportu `bio_vision_20261112.md`).
Status: **plan**. Bez kodu projektu, symulacji, treningu, pobierania, instalacji, nowych seedów i commita. Liczby z MaleCNS pochodzą z jednorazowych zapytań tylko do odczytu na `data/malecns/*-male-cns-v1.0-minconf-0.5.feather`.

**Etykiety:** [LIT] / [FM] / [PROP]; VERIFIED · PARTIALLY VERIFIED · REPORTED · INFERRED · HYPOTHESIS · NOT VERIFIED · NOT IMPLEMENTED.

---

## 0. Streszczenie dla Adama

1. **Decyzja (12 XI):** encoder koloru → ten sam prąd do wszystkich LC10a jednej strony uznajemy za **sztuczne pobudzanie wybranych neuronów** w rozumieniu zasady z 3 XI. Wyniki V5 (38/40 itd.) zostają prawdziwe jako wyniki pętli, ale **nie** jako „mucha widzi cel”. [FM]
2. **Cel planu:** obraz z kamery wchodzi do sieci **tylko na poziomie oka** (fotoreceptory/lamina, wszystkie kolumny jednakowo). Dalej wszystko robią połączenia z MaleCNS: płat wzrokowy → detektory → neurony zstępujące → ramię. [PROP]
3. **Dane na to są:** kolumny siatkówki mają współrzędne w adnotacjach (1767 neuronów L1 z przypisaną kolumną heksagonalną); rdzeń ruchu (28 typów, od R1-R6 do T4/T5) to **47 473 neurony, 1,16 mln połączeń, 7,1 mln synaps**. [FM, VERIFIED odczyt]
4. **Ważne odkrycie z danych:** **LPLC2 (detektor zbliżania)** jest łatwy: 79% jego wejścia pochodzi z płata wzrokowego, głównie z T4/T5. **LC10a (śledzenie celu)** jest trudny: tylko 44% wejścia z płata, rozłożone na 28 typów (w tym drogę barwną R7y → Tm5a), 35% z innych neuronów projekcyjnych, 17% z mózgu centralnego. [FM, VERIFIED odczyt]
5. **Rekomendacja:** pierwsze zachowanie przez oko to **„coś się zbliża → zatrzymaj/cofnij”** (LPLC2/LC4 → włókno olbrzymie DNp01, 4862 i 6362 synapsy). Śledzenie celu przez LC10a — drugi etap. [PROP]
6. **Największe ryzyko naukowe:** konektom nie podaje dynamiki neuronów. Kierunkowość T4/T5 zależy od różnych opóźnień wejść; przy jednakowych parametrach ALIF może się **nie pojawić**. Dlatego pierwszy test (bramka G2) to: czy nasze T4/T5 w ogóle rozróżniają kierunek ruchu, zanim cokolwiek podłączymy do ramienia. [INFERRED / HYPOTHESIS]
7. **Termin:** do demo 1 XII zostało 19 dni. Realnie da się zrobić O0–O3 i test G2. Pełna pętla „oko → ramię” do demo jest mało prawdopodobna. Proponuję: demo pokazuje V5 z uczciwym opisem + „oko w budowie” z wynikiem G2. [INFERRED]

---

## 1. Fakty z danych MaleCNS v1.0 [FM, VERIFIED — odczyt]

| Co | Wynik |
|---|---|
| Neurony z przypisaną kolumną heksagonalną (`assignedOlHex1/2`) | 23 720; typy: L1 1767, L2 1767, L5 1773, C3 1770, T1 1764, Mi1 1762, Mi4 1758, Mi9 1760, Tm1 1767, Tm2 1758, Tm9 1743, Tm20 1732, L3 892, C2 874, Tm4 833 |
| Zakres współrzędnych kolumn L1 | hex1 1–36, hex2 1–39 |
| Typy **bez** kolumny w adnotacji | R1-R6, R7/R8, T4/T5, LC10a, LPLC2, LC4, LC11 (kolumnę trzeba wyznaczyć z połączeń) |
| Liczba kolumn | ok. 884–892 na stronę (wg L1: 892 P, 884 L) |
| Podsieć A: rdzeń ruchu (R1-R6, L1–L5, C2, C3, T1, Mi1/4/9, Tm1/2/3/4/9/20, CT1, TmY15, T4a–d, T5a–d) | 47 473 neurony; 1 155 853 połączeń; 7 109 349 synaps |
| Podsieć B: A + LC10a, LPLC2, LC4, LC11 | 48 202 neurony; 1 256 270 połączeń; 7 450 730 synaps |
| Wejście LPLC2 wg superklas | ol_intrinsic 78,6%, visual_projection 15,1%, cb_intrinsic 3,4%; 80% wejścia z płata daje 21 typów: Tm5Y, T5d, T5b, T5c, T4c, Tm20, T4b, T5a, T4a, Y3, … |
| Wejście LC10a wg superklas | ol_intrinsic 44,3%, visual_projection 35,4%, cb_intrinsic 17,0%, visual_centrifugal 3,1%; 80% wejścia z płata daje 28 typów: Tm5Y, TmY21, Tm5a, Li22, Tm3, MeLo8, Tm6, Li14, T2a, Y3, … |
| Największe wejścia do LC10a (typy) | LC10a 25 244, TuTuA_2 18 097, AOTU042 14 492, Tm5Y 14 221, LC9 9 661, LC10c-1 8 823 |
| Tm5a — główne wejścia | Dm8a 12 180, Mi4 7 710, LT58 7 078, Cm7 7 032, **R7y 6 507** (droga barwna) |
| Drogi wyjściowe | LPLC2 → DNp01 (GF) 4862; LC4 → DNp01 6362; LC10a → DNa02 0 (pośrednio, jak w V5) |

Nie sprawdzałem znaków (przekaźników) w tych podsieciach ani dróg dłuższych niż 1 krok.

**Wniosek [INFERRED]:** LC10a nie jest „wyjściem oka” — to węzeł, który mocno słucha innych neuronów projekcyjnych i mózgu centralnego (sprzężenie zwrotne). Dlatego wejście „kolor → LC10a” nie tylko omijało oko, ale też upraszczało sam LC10a.

---

## 2. Literatura, na której plan się opiera

| Co | Źródło | Status |
|---|---|---|
| Sieć z konektomu 64 typów płata wzrokowego, parametry dopasowane metodami głębokiego uczenia; przewidywania zgodne z 26 badaniami | Lappalainen et al. 2024, Nature, doi:10.1038/s41586-024-07939-3 (abstrakt) | [LIT] VERIFIED |
| Kod tego modelu: `TuragaLab/flyvis`, PyTorch, licencja MIT, gotowe wytrenowane modele, samouczek „własne bodźce” | GitHub API + README | [LIT] VERIFIED |
| flyvis używa innego konektomu niż MaleCNS i modelu nieimpulsowego | z pamięci | NOT VERIFIED |
| NeuroMechFly v2 / FlyGym: oczy jako ommatidia na siatce heksagonalnej, symulowane wejście na siatkówkę; sieć wzrokowa z konektomu do podążania za muchą | Wang-Chen et al. 2024, Nat Methods (abstrakt) + README FlyGym | [LIT] VERIFIED |
| T4/T5: 4 kierunki, osobne warstwy płytki | Maisak et al. 2013, Nature (abstrakt) | [LIT] VERIFIED |
| LPLC2: ultra-selektywne zbliżanie przez przeciwstawny ruch promieniowy | Klapoetke et al. 2017, Nature (abstrakt) | [LIT] VERIFIED |
| LC10: małe ruchome obiekty, mechanizm centrum–otoczenie; siła zależy od stanu (P1) | Ribeiro et al. 2018, Cell (abstrakt) | [LIT] VERIFIED |
| GF: czas impulsu decyduje o rodzaju ucieczki | von Reyn et al. 2014, Nat Neurosci (abstrakt) | [LIT] VERIFIED |
| Fotoreceptory muchy najlepiej kodują szybkie, kontrastowe zmiany | Juusola et al. 2017, eLife (abstrakt) | [LIT] VERIFIED |
| Większość neuronów laminy i rdzenia płata wzrokowego działa potencjałami stopniowanymi, nie impulsami | z pamięci | NOT VERIFIED — do sprawdzenia przed O2 |

---

## 3. Architektura (etapy O0–O6) [PROP — wszystko NOT IMPLEMENTED]

```
kamera MuJoCo ──► O1 optyka: próbkowanie na kolumny heks. (L i P)
                    │   (jednakowo dla wszystkich kolumn; bez wyboru neuronów)
                    ▼
               O2 fotoreceptor: adaptacja (górnoprzepustowo w czasie) → prąd do R1-R6 (albo L1–L3)
                    ▼
               O3 rdzeń ruchu z MaleCNS (podsieć A, 47 473 neuronów)  ──► G2: czy T4/T5 rozróżniają kierunek?
                    ▼
               O4 detektory: LPLC2, LC4 (etap 1); LC10a + 28 typów płata (etap 2) ──► G3: czy LPLC2 odróżnia zbliżanie?
                    ▼
               O5 wyjście: DNp01 (GF) → „stop / cofnij” (etap 1); DNa02 → obrót (etap 2)
                    ▼
               O6 ramię SO-101 w MuJoCo + warstwa bezpieczeństwa (classical, oznaczona)
```

| Etap | Co | Decyzje / problemy | Z danych czy inżynierskie |
|---|---|---|---|
| **O0** Mapa kolumn | Tabela: kolumna (hex1, hex2, strona) → neurony L1–Tm; R1-R6, T4/T5, LPLC2 przypisane przez połączenia | Tylko analiza danych | z danych |
| **O1** Optyka | Obraz renderu → jasność w każdej kolumnie (np. średnia ważona w polu akceptacji) | **Pole widzenia:** oko muchy obejmuje prawie całą sferę, kamera SO-101 ok. 70°. Opcje: (a) ścisnąć wszystkie kolumny w 70° (zniekształca kąty), (b) użyć tylko kolumn przednich, (c) dwie kamery w symulacji. **Barwy:** kamera RGB ≠ UV/zieleń muchy — na start tylko jasność | inżynierskie (jawnie oznaczone) |
| **O2** Fotoreceptor | Prosty model adaptacji → prąd wejściowy dla wszystkich R1-R6 (lub L1–L3, jeśli R pominięte) | Neurony graded vs ALIF impulsowy (NOT VERIFIED, pkt 2) | inżynierskie |
| **O3** Rdzeń ruchu | Podsieć A z wagami i znakami z MaleCNS, silnik `alif_sparse.py` | **Parametry neuronów:** jednakowe (jak dziś) vs dopasowane (wymaga zgody jak P1–P7). **Koszt:** 1,16 mln niezerowych wag; prędkość nieznana — `bench_loop.py` istnieje, ale nie był uruchamiany | wagi z danych, dynamika inżynierska |
| **O4** Detektory | Etap 1: LPLC2, LC4 (+ ich wejścia Tm5Y, Tm20, Y3, TmY5a, Tm37, TmY18…). Etap 2: LC10a + 28 typów płata + inne VPN | Granica podsieci = decyzja; raportować, ile wejścia zostaje poza nią | z danych |
| **O5** Wyjście | DNp01 → komenda „stop/cofnij”; DNa02 → obrót (jak V5) | Mapowanie DN → staw ramienia jest inżynierskie | inżynierskie |
| **O6** Ramię | Istniejąca pętla + warstwa bezpieczeństwa | bez zmian we wspólnych modułach | — |

**Zgodność z zasadą z 3 XI:** obraz wchodzi tylko przez O1–O2, do **wszystkich** kolumn tą samą regułą. Żaden neuron poza okiem nie dostaje prądu z zewnątrz. [PROP]

---

## 4. Bramki i kryteria (ustalone przed uruchomieniem) [PROP]

| Bramka | Test | Zaliczone gdy | Jeśli nie |
|---|---|---|---|
| **G1** Mapa | ≥95% L1 i R1-R6 przypisanych do kolumn; obie strony | liczby w tabeli | poprawić O0 albo zawęzić do kolumn z mapą |
| **G2** Kierunek | Pasy/krawędzie w 4 kierunkach, otwarta pętla, bez ramienia. Indeks kierunkowości T4a–d / T5a–d zgodny z ich preferowanym kierunkiem (Maisak 2013) | próg ustalony przed testem; kontrola: wagi przetasowane w obrębie typu | **STOP** — przy jednakowych parametrach oko nie liczy ruchu; decyzja Adama: dopasowanie parametrów albo zmiana planu |
| **G3** Zbliżanie | Rosnący dysk vs malejący vs ruch całego pola (jak Klapoetke 2017) | LPLC2/LC4 silniej na zbliżanie niż na oba kontrolne; kontrole przetasowania | wynik ujemny opisany wprost |
| **G4** Pętla | Obiekt zbliża się do kamery na ramieniu → ramię się zatrzymuje/cofa przez DNp01 | ustalone przed testem; kontrole: przetasowana sieć, zamienione strony, bez obrazu, „oko wyłączone” + porównanie z odruchem klasycznym | raport bez upiększania |
| **G5** Cel (etap 2) | Śledzenie celu przez LC10a → DNa02 z prawdziwym okiem | porównanie z V5 (encoder) i klasyką, te same kontrole | — |

---

## 5. Ryzyka [INFERRED]

| Ryzyko | Skutek | Co robimy |
|---|---|---|
| Brak kierunkowości przy jednakowych parametrach | G2 nie przechodzi | to jest **wynik naukowy** („sam konektom bez dynamiki nie wystarcza”); dopiero wtedy decyzja o dopasowaniu parametrów |
| Neurony graded modelowane jako impulsowe | zła dynamika rdzenia | sprawdzić literaturę przed O2; opisać jako ograniczenie |
| Koszt obliczeń 47–48 tys. neuronów | pętla wolniejsza niż czas rzeczywisty | zmierzyć (B2-podobny pomiar) przed decyzją; symulacja nie musi być w czasie rzeczywistym |
| Pole widzenia i barwy kamery ≠ oko | zniekształcone wejście | jawnie oznaczyć jako inżynierskie |
| LC10a zależy od sprzężeń centralnych (17%) i innych VPN (35%) | etap 2 może wymagać dużej części mózgu | najpierw etap 1 (LPLC2) |
| 19 dni do demo | pełna pętla nie zdąży | demo = V5 z uczciwym opisem + wynik G2/G3 |
| Pokusa „dostrojenia” wag, by przeszło | udawanie | wagi i znaki z danych bez zmian; parametry wspólne dla typu, ustalone przed testem |

---

## 6. Co powiedzieć na plakacie 16 XI (propozycja) [PROP]
„Wejście wzrokowe w obecnej wersji to heurystyka koloru podawana do neuronów LC10a — nie oko muchy. Budujemy prawdziwą drogę wzrokową z danych MaleCNS (ok. 47 tys. neuronów od fotoreceptorów do detektorów ruchu). Pierwszy test: czy sama mapa połączeń wystarcza, żeby neurony rozróżniały kierunek ruchu.”

---

## 7. Decyzje dla Adama — **niczego nie zaczynam**
1. Zatwierdzenie kolejności: etap 1 = LPLC2/LC4 → DNp01 (zbliżanie → stop), etap 2 = LC10a.
2. O1: która opcja pola widzenia (a / b / c)?
3. Czy dopuszczasz **dopasowanie parametrów** neuronów (uczenie), jeśli G2 nie przejdzie? Jeśli nie — wynik ujemny kończy ten kierunek.
4. Zgoda na O0 (tylko analiza danych, bez symulacji) jako pierwszy krok.
5. Zgoda na pomiar kosztu (`bench_loop.py` lub podobny) — wymaga uruchomienia kodu i przydziału seedów.
6. Zakres demo 1 XII: V5 z uczciwym opisem + ewentualnie G2/G3.

---

## 8. Źródła sprawdzone przy tym planie
- Dane: `data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather`, `connectome-weights-male-cns-v1.0-minconf-0.5.feather` — odczyt.
- Kod (przeczytane nagłówki): `flymind/encoder.py`, `flymind/alif_sparse.py`, `flymind/bench_loop.py`; `flymind/FLYMIND_MASTER_CONTEXT.md` l. 26, 71–80.
- https://github.com/TuragaLab/flyvis — README + metadane repo (MIT).
- https://github.com/NeLy-EPFL/flygym — README.
- Prace: patrz tabela w pkt 2 i `bio_vision_20261112.md` (abstrakty).

---

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
