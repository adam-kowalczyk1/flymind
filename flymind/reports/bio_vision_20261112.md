# FlyMind — czy biologia może zmienić widzenie robotów? (tylko badanie)

Data: 12 XI 2026 · Autor: Claude (Opus 5.5) na prośbę Adama · Status: raport. Bez kodu projektu, symulacji, treningu, pobierania danych i commita.

**Etykiety:** [LIT] literatura · [FM] FlyMind · [PROP] moja propozycja. Status: VERIFIED (otworzyłem źródło i tam to jest) · PARTIALLY VERIFIED · REPORTED · INFERRED (mój wniosek) · HYPOTHESIS · NOT VERIFIED · NOT IMPLEMENTED.

**Uwaga o metodzie:** liczby z MaleCNS w pkt 2 pochodzą z **odczytu** lokalnych plików `data/malecns/*.feather` (adnotacje i wagi, v1.0, minconf 0,5) jednorazowymi zapytaniami w terminalu. Nie dodałem kodu do repo, niczego nie zapisałem ani nie uruchomiłem symulacji. Jeśli według Adama takie zapytanie łamie zasadę „bez kodu”, liczby z pkt 2 trzeba traktować jako niezatwierdzone.

---

## 0. Streszczenie dla Adama (prostym językiem)

1. **Najważniejsza rzecz spoza listy:** dziś FlyMind **nie widzi przez oczy muchy**. `encoder.py` szuka kolorowej plamy i podaje **ten sam prąd wszystkim LC10a jednej strony**. Pomija fotoreceptory i cały płat wzrokowy (ok. 89 tys. neuronów płata w danych). Według `FLYMIND_MASTER_CONTEXT.md` to „heurystyka ENGINEERING, nie siatkówka”. Zasada z 3 XI mówi „bez sztucznego pobudzania wybranych neuronów” — **obecne wejście jest na granicy tej zasady**. Mówię to wprost, bo to podstawa wszystkiego poniżej. [FM, VERIFIED]
2. **Widzenie zmian (kamery zdarzeniowe):** działa naprawdę, ale głównie jako **dodatek** do zwykłej kamery. W Nature 2024 kamera 20 kl./s + zdarzeniowa dała opóźnienie jak kamera 5000 kl./s przy przepustowości kamery 45 kl./s. Same zdarzenia zwykle przegrywały dokładnością. [LIT, VERIFIED]
3. **Patrzenie aktywne:** sensowne. AV-ALOHA: ruchoma kamera wyraźnie lepsza od stałych w zadaniach z zasłoniętym widokiem. [LIT, VERIFIED]
4. **Widzenie przez ruch (przepływ optyczny):** sprawdzone w latających robotach od lat. Dla **ramienia z jedną kamerą** daje „czas do zderzenia” i proporcje, ale nie bezwzględną odległość bez dodatkowej wiedzy. Ramię ma już dokładną wiedzę o własnym ruchu, więc korzyść jest mniejsza niż u drona. [LIT + INFERRED]
5. **Wrodzone detektory:** mucha ma gotowe detektory „coś się zbliża” (LPLC2, LC4), „mały ruchomy cel” (LC11, LC10). **Wszystkie są w MaleCNS** i mają silne połączenia, np. LC4→włókno olbrzymie (DNp01) 6362 synapsy, LPLC2→DNp01 4862. Jako **uzupełnienie** dużych modeli (DINO) — sensowne. Jako **zastępstwo** — przereklamowane: detektor zbliżania nie rozpozna kubka. [LIT VERIFIED + FM VERIFIED (odczyt) + INFERRED]
6. **Odejmowanie własnego ruchu (kopia eferentna):** u muchy dobrze udokumentowane. Robot zna własne komendy i kinematykę **dokładnie**, więc klasyczne sterowanie wzrokowe od dawna to wykorzystuje. Biologia daje tu ważną lekcję o tym, **kiedy** tłumić widzenie: przy zmianie kursu tak, przy stabilizacji nie (Fenk 2021). Nie daje „nowego rozwiązania” problemu kamery na ramieniu. [LIT VERIFIED + INFERRED]
7. **Na Explory, jeśli ma być o biologii, najmocniejszy i najuczciwszy temat to:** zastąpić heurystykę koloru prawdziwą drogą wzrokową muchy (fotoreceptory → T4/T5 → LC/LPLC), i pokazać, co się wtedy dzieje, z kontrolami. To duży krok i wymaga Twojej zgody. [PROP]

---

## 1. Co FlyMind dziś „widzi” [FM]

| Fakt | Źródło | Status |
|---|---|---|
| `encoder.py`: kolorowa plama → ten sam prąd do wszystkich LC10a jednej strony | `FLYMIND_MASTER_CONTEXT.md`, l. 71 | VERIFIED |
| Właściciel odrzucił sztuczne pobudzanie neuronów; wejścia tylko z naturalnych zmysłów | tamże, l. 26 | VERIFIED |
| Sieć: 135 + 140 LC10a → 147 pośrednich → 2 DNa02; 0 bezpośrednich synaps LC10a→DNa02 | tamże, l. 72, 80; potwierdzone dziś odczytem (LC10a→DNa02 = 0) | VERIFIED |
| Wejście i wyjście: jedna liczba na stronę; bez obrazu 0/40 | prompt Adama | REPORTED |

**Napięcie [INFERRED]:** LC10a w biologii odpowiada na **małe ruchome obiekty** (mechanizm centrum–otoczenie oparty na ruchu, Ribeiro 2018), a encoder podaje **kolor**. To nie jest zmysł muchy. Wynik 38/40 jest prawdziwy jako wynik pętli, ale nie jako „mucha widzi cel”.

---

## 2. Obwody wzrokowe w MaleCNS v1.0 (odczyt danych) [FM, VERIFIED — odczyt, bez symulacji]

| Poziom | Typy (liczba neuronów, L/P) |
|---|---|
| Fotoreceptory | R1-R6 3377; R7/R8 różne podtypy (R7y 482, R8y 481, R7p 332, R8p 330 …) |
| Lamina / rdzeń | L1 1776, L2 1779, L3 1772; Mi1 1773, Mi4 1772, Mi9 1775; Tm1 1777, Tm2 1766, Tm3 2054, Tm4 1670, Tm9 1771 |
| Detektory kierunku ruchu | T4a–d 1684 / 1690 / 1778 / 1709; T5a–d 1664 / 1715 / 1720 / 1620 |
| Neurony szerokiego pola | HSN, HSE, HSS po 1 na stronę; H2 1/1; typy VS: `VS`, `VST1`, `VST2`, `VSm` (nazwa `VS1` nie występuje) |
| Detektory cech (LC/LPLC) | LPLC1 134, LPLC2 185, LC4 126, LC6 124, LC9 219, LC10a 275, LC10b 95, LC11 143, LC12 498, LC15 126, LC16 182, LC17 353, LC18 208, LC21 153, LC22 73, LC31a 32 |
| Neurony zstępujące | DNp01 (synonim „GF” — włókno olbrzymie), DNp02, DNp03, DNp06, DNp09, DNp11, DNa01, DNa02 — po 1 na stronę |
| Superklasy | ol_intrinsic 89 403; visual_projection 9 201; visual_centrifugal 563; ol_sensory 6 098 |

Wybrane połączenia (suma wag synaps między typami):

| Droga | Synapsy | Komentarz |
|---|---|---|
| LC4 → DNp01 (GF) | 6362 | droga ucieczki przed zbliżaniem |
| LPLC2 → DNp01 (GF) | 4862 | j.w. |
| T4a → HSN | 12 770 | ruch poziomy → neuron szerokiego pola |
| LC9 → DNp09 | 1977 | zgodne z audytem D1 |
| LC10a → DNa02 / DNa01 | 0 / 0 | brak bezpośrednich (zgodne z wcześniejszym audytem) |
| LC11 → DNp01 | 0 | — |
| Wejścia HSN / HSE / HSS / VS z neuronów zstępujących | 11 / 15 / 23 / 31 | **mało**; czy niosą kopię eferentną — nieznane (HYPOTHESIS) |

Nie sprawdzałem znaków (przekaźników) ani dróg wieloetapowych. Liczby to sumy wag przy minconf 0,5.

---

## 3. Temat 1 — widzenie zmian zamiast pełnych klatek

**(a) Biologia [LIT]**
- T4 i T5 muchy są dostrojone do jednego z 4 kierunków ruchu (przód–tył, tył–przód, góra, dół) i kończą się w osobnych warstwach płytki zrazikowej. Maisak et al. 2013, Nature (abstrakt). VERIFIED.
- Fotoreceptory R1-R6 muchy najlepiej kodują szybkie, kontrastowe zmiany, jakie występują przy sakadach; mikroruchy fotoreceptorów wyostrzają obraz ponad ograniczenie optyczne. Juusola et al. 2017, eLife (abstrakt). VERIFIED. To jest ciekawy kontrargument: owad nie „ignoruje” tego, co się nie zmienia — on **sam wywołuje zmiany** ruchem.

**(b) Roboty [LIT]**
- Kamery zdarzeniowe: rozdzielczość czasowa rzędu mikrosekund, zakres dynamiki 140 dB vs 60 dB, mała moc; **wymagają nowych metod przetwarzania**. Gallego et al., arXiv 1904.08405 (abstrakt). VERIFIED.
- Gehrig & Scaramuzza 2024, Nature: algorytmy tylko na zdarzeniach albo są wydajne, ale mniej dokładne, albo tracą rzadkość; **hybryda** 20 kl./s RGB + zdarzenia = opóźnienie kamery 5000 kl./s przy przepustowości 45 kl./s, bez utraty dokładności (abstrakt). VERIFIED.
- Dron w pełni neuromorficzny (Loihi, 200 Hz, 7–12 mW sieci) — patrz raport `robot_ai_revolution_20261112.md`. VERIFIED.

**(c) FlyMind** — droga R1-R6 → L1/L2 → T4/T5 jest w danych w pełnej skali (pkt 2). Kamera zdarzeniowa GenX320 była już alternatywą w wyborze kamery z 5 XI (pamięć projektu; NOT VERIFIED dziś). Symulacja zdarzeń z MuJoCo jest możliwa jako różnica klatek [INFERRED, NOT IMPLEMENTED].

**(d) Błąd / udawanie [INFERRED]**
- „Kamera zdarzeniowa = oko muchy” — nie. Oko muchy ma ok. 890 kolumn na stronę (liczba L1 w danych: 892 P, 884 L; liczba R1-R6 = 3377 wygląda na niepełną adnotację — nie sprawdzałem), a fotoreceptory kodują analogowo z adaptacją, nie binarnymi zdarzeniami (to ostatnie: NOT VERIFIED w tym raporcie).
- „Zdarzenia zawsze lepsze” — Gehrig 2024 pokazuje, że **same** zdarzenia zwykle przegrywają; zysk daje połączenie.
- Nieruchoma scena nie generuje zdarzeń — dla ramienia stojącego nad nieruchomym obiektem to wada, chyba że robot sam się porusza (zgodne z Juusola).

---

## 4. Temat 2 — patrzenie aktywne

**(a) Biologia [LIT]**
- Prawie wszystkie zwierzęta z dobrym wzrokiem mają wzorzec „stabilne fiksacje + szybkie sakady”; wzrok trzyma się nieruchomo, bo fotoreceptory są wolne i obraz się rozmywa; tłumienie obrotów chroni przepływ translacyjny, z którego zwierzę ocenia kierunek i odległości. Land 1999, J Comp Physiol A (abstrakt). VERIFIED.
- Mucha w locie wykonuje ruchy głowy i musi wtedy wyciszać odruchy stabilizacji wzroku wokół osi skrętu. Kim et al. 2017, Cell (abstrakt). VERIFIED.

**(b) Roboty [LIT]**
- „Active perception” jako program badań: Bajcsy 1988, Proc. IEEE — **tylko metadane** (Crossref). PARTIALLY VERIFIED.
- AV-ALOHA: dodatkowe ramię z kamerą sterowane głową operatora w VR; uczenie przez imitację z aktywnym widzeniem daje „znaczną poprawę” względem stałych kamer w zadaniach z ograniczoną widocznością. Chuang et al. 2024, arXiv 2409.17435 (abstrakt; brak liczb w abstrakcie). VERIFIED.

**(c) FlyMind** — Etap F1 „aktywne czucie” z 1–2 XI był zamknięty: „zysk realny, ale ogólny dla progu” (pamięć projektu; NOT VERIFIED dziś). Kamera na nadgarstku SO-101 sama jest formą aktywnego widzenia [INFERRED].

**(d) Błąd [INFERRED]** — nazywanie każdego ruchu kamery „sakadą muchy”. U muchy sakada to szybki obrót całego ciała lub głowy z wyciszeniem części widzenia; w FlyMind nie ma osobnego sterowania wzrokiem ani wyciszenia.

---

## 5. Temat 3 — widzenie przez ruch (przepływ optyczny)

**(a) Biologia [LIT]**
- „Licznik drogi” pszczoły jest wzrokowy: zależy od tego, ile obraz przesunął się na oku. Srinivasan et al. 2000, Science (abstrakt). VERIFIED.
- Ruch własny bez obrotów jest potrzebny, by przepływ mówił o odległości (Land 1999). VERIFIED.

**(b) Roboty [LIT]**
- Mikrohelikopter z „regulatorem przepływu optycznego” startuje, leci i ląduje bez pomiaru wysokości ani prędkości; model wyjaśnia m.in. tonięcie pszczół nad gładką wodą. Franceschini, Ruffier, Serres 2007, Curr Biol (abstrakt). VERIFIED.
- Postawę lotu da się wyznaczyć z przepływu + modelu ruchu, bez akcelerometru; w zawisie postawa jest nieobserwowalna, ale sterowanie pozostaje stabilne, „lekko oscylacyjne”. de Croon et al. 2022, Nature (abstrakt). VERIFIED.
- Uczenie wskazówek wyglądu poprawia sterowanie oparte na przepływie: de Croon, De Wagter, Seidl 2021, Nat Mach Intell — **tylko metadane**. PARTIALLY VERIFIED.

**(c) FlyMind** — T4/T5 → HS (T4a→HSN 12 770 synaps) to w danych gotowa droga przepływu poziomego [FM, VERIFIED odczyt]. Kamera na ramieniu porusza się znanym ruchem, więc przepływ mógłby dać **czas do kontaktu** przy podchodzeniu do obiektu [INFERRED, NOT IMPLEMENTED].

**(d) Błąd [INFERRED]** — „jedna kamera + przepływ = pełna mapa głębi”. Przepływ daje odległość **w proporcji do prędkości**; bez znanej prędkości tylko skalę względną. Ramię zna swoją prędkość, więc to rozwiązywalne, ale wtedy zwykła geometria (stereo z ruchu) robi to samo bez biologii. Przewaga owadów jest głównie w **małym koszcie obliczeń**, ważnym dla drona, mniej dla ramienia z laptopem.

---

## 6. Temat 4 — wrodzone detektory a duże modele (DINO)

**(a) Biologia [LIT]**
- 22 typy LC opisane anatomicznie; aktywacja kilku wywołuje konkretne zachowania; dwa reagują na zbliżanie, inny na mały ruchomy obiekt; jednostronna aktywacja daje skręt do lub od. Wu et al. 2016, eLife (abstrakt). VERIFIED.
- LPLC2: „ultra-selektywny” detektor zbliżania dzięki przeciwstawnemu ruchowi promieniowemu; ramiona dendrytów leżą w warstwach T4/T5 dla 4 kierunków. Klapoetke et al. 2017, Nature (abstrakt). VERIFIED.
- LC11: reaguje na mały ciemny obiekt (np. 2,2°), słabo na migotanie, pionowe paski i panoramy. Keleś & Frye 2017, Curr Biol (abstrakt). VERIFIED.
- LC10: niezbędne do orientacji samca na samicę; reaguje na małe ruchome obiekty; siłę działania wzmacnia stan pobudzenia (neurony P1). Ribeiro et al. 2018, Cell (abstrakt). VERIFIED.
- Włókno olbrzymie (GF): moment jego impulsu względem równoległych dróg decyduje o wyborze szybkiej vs stabilnej ucieczki. von Reyn et al. 2014, Nat Neurosci (abstrakt). VERIFIED.

**(b) Roboty [LIT]**
- Model neuronu LGMD szarańczy jako **jedyny** zmysł robota: niezawodne omijanie zderzeń w złożonym tle. Yue & Rind 2006, IEEE TNN (abstrakt). VERIFIED.
- DINOv2: cechy ogólnego zastosowania bez dostrajania, kosztem dużych danych i modelu. Oquab et al. 2023, arXiv 2304.07193 (abstrakt). VERIFIED.

**(c) FlyMind** — LPLC2, LC4, LC10a, LC11 i inne są w MaleCNS; LC4/LPLC2→GF to silne, krótkie drogi (pkt 2). Zgodnie z Ribeiro 2018 LC10 to biologicznie sensowne wejście do śledzenia celu — **ale jako detektor ruchomego małego obiektu, nie koloru** [INFERRED].

**(d) Uzupełnienie czy alternatywa? [INFERRED]**
- **Uzupełnienie — tak:** tani, szybki odruch („coś leci na kamerę → stop”) obok wolnego, ogólnego modelu. Pasuje do architektury „szybkie odruchy pod wolnym modelem” z poprzedniego raportu.
- **Alternatywa — nie:** detektory muchy wykrywają **cechy ważne dla muchy** (zbliżanie, mały cel, samica), nie kategorie przedmiotów. Twierdzenie, że „zestaw detektorów muchy zastąpi DINO”, byłoby przereklamowane.
- **Zasada z 3 XI:** podawanie musze **wyniku DINO** (np. „tu jest kubek” jako prąd do LC10a) to dokładnie zewnętrzny wynik zamiast zmysłu — **narusza zasadę**. Dziś podobnie działa encoder koloru (pkt 1).

---

## 7. Temat 5 — odejmowanie własnego ruchu (kopia eferentna)

**(a) Biologia [LIT]**
- Neurony wzrokowe muchy dostają sygnał motoryczny przy własnych sakadach (Kim, Fitzgerald, Maimon 2015 — szczegóły w raporcie `robot_ai_revolution_20261112.md`). VERIFIED.
- Sygnał motoryczny ilościowo wycisza przewidywaną odpowiedź na obrót wokół osi skrętu, a zachowuje czułość wokół innych osi. Kim et al. 2017, Cell (abstrakt). VERIFIED.
- **Wyciszenie jest wybiórcze:** silne przy skrętach zmieniających kurs (ucieczka, spontaniczne), słabe lub brak przy skrętach stabilizujących (optomotorycznych). Fenk, Kim, Maimon 2021, Curr Biol (abstrakt). VERIFIED.

**(b) Roboty [LIT + INFERRED]**
- Klasyczne sterowanie wzrokowe (visual servoing) zakłada znaną kinematykę kamery: Chaumette & Hutchinson 2006, IEEE RAM — **tylko metadane**. PARTIALLY VERIFIED.
- Robot **zna** swoje komendy i stan stawów, więc „kopia eferentna” jest u niego darmowa [INFERRED]. Problem kamery na ramieniu to głównie **opóźnienie, rozmycie i kalibracja**, nie brak wiedzy o własnym ruchu.

**(c) FlyMind** — u nas: opóźnienie 50 ms → 17/40 (pkt 1). HS/VS mają w danych niewielkie wejścia z neuronów zstępujących (11–31 synaps) [FM, VERIFIED odczyt]; czy to droga kopii eferentnej — **nieznane** [HYPOTHESIS]. Kim 2015/2017 nie identyfikuje w abstraktach źródła tego sygnału.

**(d) Błąd [INFERRED]** — „kopia eferentna rozwiąże problemy kamery na ramieniu”. Część z nich (znajomość własnego ruchu) robot już ma. Wartość biologii: **przewidywanie** (kompensacja opóźnienia) i **wybiórczość** (Fenk 2021: nie tłumić tego, co stabilizuje).

---

## 8. Spoza listy — co może być ważniejsze [INFERRED / PROP]

1. **Prawdziwa droga wzrokowa zamiast heurystyki (najważniejsze).** Lappalainen 2024 (poprzedni raport) pokazał, że sieć z konektomu płata wzrokowego po dopasowaniu parametrów przewiduje aktywność z 26 badań; NeuroMechFly v2 użył sieci wzrokowej z konektomu do podążania za inną muchą. Dla FlyMind: obraz z kamery w MuJoCo → wejście do R1-R6 → … → LC10a. **Ale:** to wymaga dopasowania parametrów (uczenia), czyli P1–P7-podobnej zgody, i ogromnej sieci (ok. 89 tys. neuronów płata). HYPOTHESIS, NOT IMPLEMENTED.
2. **Niska rozdzielczość jako cecha, nie wada.** Owad widzi grubo, ale szybko i równolegle (Juusola 2017). Dla robota oznacza to: mała kamera + szybka pętla do odruchów, duża kamera do rozpoznawania. INFERRED.
3. **Stan zmienia widzenie.** LC10 działa silniej w stanie pobudzenia (Ribeiro 2018). FlyMind nie ma stanu. INFERRED.

---

## 9. Ocena tematów wprost

| Temat | Siła dowodu w robotach | Dla ramienia SO-101 | Dla FlyMind / Explory | Przereklamowane? |
|---|---|---|---|---|
| 1. Zmiany zamiast klatek | silna (Nature 2024, Sci Robot 2024) | umiarkowana | droga T4/T5 w danych | „zdarzenia zastąpią kamery” — tak |
| 2. Patrzenie aktywne | umiarkowana (AV-ALOHA) | dobra | słaba, brak sterowania wzrokiem | nie |
| 3. Przepływ optyczny | silna dla dronów | umiarkowana (czas do kontaktu) | droga T4→HS w danych | „głębia z jednej kamery” — tak |
| 4. Wrodzone detektory | umiarkowana (LGMD) | dobra jako odruch | **najmocniejsza**: LC/LPLC/GF w danych | „zastąpią DINO” — tak |
| 5. Kopia eferentna | słaba jako nowość | mała (robot już zna ruch) | test opóźnienia; źródło w danych nieznane | „rozwiąże kamerę na ramieniu” — tak |

---

## 10. Zasada z 3 XI — co ją narusza [FM / INFERRED]
- **Narusza:** wynik DINO lub innego modelu podawany jako prąd do wybranych neuronów; **obecny encoder koloru → LC10a** jest tego samego rodzaju (wybrane neurony, wynik heurystyki).
- **Zgodne:** obraz kamery → fotoreceptory → płat wzrokowy z danych → LC/LPLC → DN. Także osobny, klasyczny odruch bezpieczeństwa poza muchą, jeśli jest oznaczony jako `classical`.
- E1–E3, P1–P7, S1–S7, U1–U5: nadal niezatwierdzone; nic tu nie uruchamiam.

---

## 11. Proponowane następne kroki — **żadnego nie zaczynam**
1. **Decyzja Adama:** czy obecny encoder koloru → LC10a uznać za zgodny z zasadą z 3 XI, czy za „sztuczne pobudzanie”. Od tego zależy, co wolno pokazać na Explory.
2. Plan na papierze „oko muchy w MuJoCo”: obraz → R1-R6 → T4/T5 → LC10a/LPLC2, z kontrolami (przetasowanie, brak obrazu, zamiana stron). Ocena kosztu obliczeń na laptopie — przed jakimkolwiek kodem.
3. Mały wariant do rozważenia: odruch „zbliżanie → stop” przez LPLC2/LC4 → GF jako drugie zachowanie z danych.
4. Plakat 16 XI: jedno zdanie wprost — „wejście wzrokowe to dziś heurystyka koloru, nie oko muchy”.

---

## 12. Źródła i co z nich przeczytałem

| Źródło | ID | Co przeczytałem |
|---|---|---|
| Gallego et al., Event-based Vision: A Survey | arXiv 1904.08405 | abstrakt |
| Gehrig & Scaramuzza 2024 | doi:10.1038/s41586-024-07409-w | abstrakt (Europe PMC) |
| Maisak et al. 2013 | doi:10.1038/nature12320 | abstrakt |
| Juusola et al. 2017 | doi:10.7554/eLife.26117 | abstrakt |
| Land 1999 | doi:10.1007/s003590050393 | abstrakt |
| Kim, Fenk, Lyu, Maimon 2017 | doi:10.1016/j.cell.2016.12.005 | abstrakt |
| Fenk, Kim, Maimon 2021 | doi:10.1016/j.cub.2021.09.068 | abstrakt |
| Kim, Fitzgerald, Maimon 2015 | doi:10.1038/nn.4083 | (poprzedni raport) abstrakt + ok. 40% tekstu |
| Bajcsy 1988 | doi:10.1109/5.5968 | tylko metadane (Crossref) |
| Chuang et al. 2024, AV-ALOHA | arXiv 2409.17435 | abstrakt |
| Srinivasan et al. 2000 | doi:10.1126/science.287.5454.851 | abstrakt |
| Franceschini, Ruffier, Serres 2007 | doi:10.1016/j.cub.2006.12.032 | abstrakt |
| de Croon et al. 2022 | doi:10.1038/s41586-022-05182-2 | abstrakt |
| de Croon, De Wagter, Seidl 2021 | doi:10.1038/s42256-020-00279-7 | tylko metadane (Crossref) |
| Wu et al. 2016 | doi:10.7554/eLife.21022 | abstrakt |
| Klapoetke et al. 2017 | doi:10.1038/nature24626 | abstrakt |
| Keleş & Frye 2017 | doi:10.1016/j.cub.2017.01.012 | abstrakt |
| Ribeiro et al. 2018 | doi:10.1016/j.cell.2018.06.020 | abstrakt |
| von Reyn et al. 2014 | doi:10.1038/nn.3741 | abstrakt |
| Yue & Rind 2006 | doi:10.1109/TNN.2006.873286 | abstrakt (Europe PMC) |
| Oquab et al. 2023, DINOv2 | arXiv 2304.07193 | abstrakt |
| Lappalainen 2024; NeuroMechFly v2 2024; Paredes-Vallés 2024 | patrz `robot_ai_revolution_20261112.md` | abstrakty |
| Dane MaleCNS v1.0 | `data/malecns/*-male-cns-v1.0-minconf-0.5.feather` | odczyt adnotacji i sum wag (tylko odczyt) |
| Kontekst FlyMind | `flymind/FLYMIND_MASTER_CONTEXT.md` l. 26, 71–80 | przeczytane |

Wcześniejsze raporty (10, 11, 12 XI, `robot_ai_revolution_20261112.md`, `motion_vector_db_20261112.md`) nie zostały zmienione.

---

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
