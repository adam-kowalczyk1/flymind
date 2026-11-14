# FlyMind — jak można by zasadniczo zmienić AI dla robotów (tylko research)

Data: 12 XI 2026 · Autor: Claude (Opus 5.5) na prośbę Adama · Status: raport, nic nie uruchomiono, nic nie zacommitowano.
Dodatkowe prośby Adama: film Welch Labs (VLA) oraz „porównaj to z VFA” — rozumiem jako **Vision-Force-Action firmy Eka Robotics** (jeśli chodziło o coś innego, trzeba poprawić pkt 6).

**Etykiety:** [LIT] literatura · [FM] FlyMind · [PROP] moja propozycja. Status: VERIFIED (otworzyłem źródło i tam to jest) · PARTIALLY VERIFIED (źródło otwarte, ale tylko część / streszczenie) · REPORTED (deklaracja firmy lub autorów bez niezależnego sprawdzenia) · INFERRED (mój wniosek) · HYPOTHESIS · NOT VERIFIED · NOT IMPLEMENTED.

---

## 0. Streszczenie dla Adama (prostym językiem)

1. **Dzisiejsze „mózgi robotów” (VLA) dobrze rozumieją polecenia i obraz, ale słabo czują i słabo reagują szybko.** Niezależny test π0 (Penn): średni postęp zadania 42,3%, pełny sukces w kategoriach ok. 19–28%; typowe błędy to zamrożenie w połowie ruchu, kolizje, precyzja i brak dotyku. [LIT, VERIFIED]
2. **Zwierzęta robią to, czego roboty nie umieją, nie dzięki „większemu modelowi”, tylko dzięki budowie:** szybkie odruchy na dole, wolne decyzje na górze; mózg wie z góry, jaki ruch sam wykona (kopia eferentna); ciało i dotyk liczą część pracy; jest stały stan wewnętrzny (np. „kompas” w mózgu muchy); uczenie lokalne, bez ponownego trenowania całości. [LIT, VERIFIED na poziomie abstraktów]
3. **Najbardziej realne do zamknięcia w ciągu kilku lat:** dotyk i siła w szybkiej pętli + wolny model u góry, szybka adaptacja bez ponownego trenowania, tańsze energetycznie pętle odruchowe. **Mało realne w kilka lat:** niezawodność „rok bez awarii”, prawdziwy zdrowy rozsądek fizyczny, uczenie z jednej próby w otwartym świecie. [INFERRED]
4. **VFA (Eka) to dokładnie ruch w stronę „siła zamiast języka”** — ale to deklaracje firmy, bez publikacji. Ma 1500 chwytów/h vs ok. 600 u człowieka i >95% udanych chwytów do 1 kg według firmy. Zewnętrzny ekspert pyta, czy to wytrzyma rok bez awarii i czy wyjdzie poza pick-and-place. [LIT, REPORTED]
5. **Sieci z konektomu są dziś świetnym narzędziem nauki, nie lepszym sterownikiem robota.** Nie znalazłem żadnej pracy, w której sterownik z konektomu bije zwykłe metody w zadaniu robota. [INFERRED z przeglądu; brak dowodu przeciwnego]
6. **Gdzie FlyMind może coś realnie wnieść:** uczciwy, sprawdzalny test „czy połączenia z danych mają znaczenie w zamkniętej pętli” (kontrole tasowania już są: 38/40 vs 3/40), test opóźnienia i kopii eferentnej (dziś 50 ms opóźnienia → 17/40), mały, otwarty benchmark. **Gdzie byłoby udawanie:** „rewolucja”, „mucha lepsza od VLA”, „neuromodulacja”, „uczenie”, ogólna inteligencja — bo w kodzie tego nie ma, a wejście/wyjście to jedna liczba na stronę. [FM + INFERRED]

---

## 1. Metoda i czego nie zrobiłem

- Wyszukiwanie w sieci; otwarte strony arXiv (abstrakty, w 2 przypadkach część pełnego tekstu HTML), abstrakty z Europe PMC dla prac z Nature/Science/Cell (strony wydawców wymagały logowania), strona projektu Penn (całość), artykuły prasowe o Eka (całość), metadane i lista rozdziałów filmu Welch Labs (transkrypcja niedostępna dla mnie).
- Pełne teksty prac z Nature **nie** zostały przeczytane — tylko abstrakty. Liczby spoza abstraktów nie są używane, a gdzie są, mają etykietę.
- Brak kodu, symulacji, treningu, pobrań, nowych ziaren. Nie ruszałem wcześniejszych raportów ani robota.

---

## 2. Pytanie 1 — największe nierozwiązane problemy AI robotów

| # | Problem | Dowód | Status |
|---|---|---|---|
| P1 | **Brak siły i dotyku w pętli.** Modele bazowe robotów opierają się głównie na obrazie i sterowaniu pozycją; imitacja „nie jest na poziomie dynamiki, gdzie siła naprawdę się liczy”. | Xie & Correll 2025 (arXiv 2504.11827), abstrakt | [LIT] VERIFIED |
| P2 | **Zawodność w otwartym świecie.** π0 w teście Penn: ponad 300 prób, średni postęp 42,3%, sukces np. Pick-and-Place 24%, Fabric 19,4%, Coffee Machine 8% postępu; zamrażanie, kolizje, literówki w poleceniu psują wynik; zasłonięta kamera nadgarstka → „Frozen — no recovery”. Autorzy sami nazywają to „vibe-check”, nie rygorystycznym benchmarkiem. | penn-pal-lab.github.io/Pi0-Experiment-in-the-Wild (cała strona) | [LIT] VERIFIED |
| P3 | **Długie zadania.** Gemini Robotics 1.5: postęp ok. 44% w zadaniach długich; zręczność „na poziomie poprzedniej generacji”. | arXiv 2510.03342 — z modelowego streszczenia dalszych sekcji, nie dosłownie | [LIT] PARTIALLY VERIFIED |
| P4 | **Ocena.** Ponad 90% epizodów ewaluacyjnych przy rozwoju Gemini Robotics 1.5 było w symulacji; laby używają różnych robotów i kryteriów, więc wyniki trudno porównać. | arXiv 2510.03342 (dosłownie); przegląd preprints.org (tylko wynik wyszukiwania) | [LIT] VERIFIED / NOT VERIFIED (drugie) |
| P5 | **Głód danych.** Open X-Embodiment: 22 roboty, 21 instytucji, 527 umiejętności. π0.5: ok. 400 h danych z robota mobilnego w ok. 100 domach, a 97,6% przykładów w 1. fazie pochodzi z innych źródeł. Dane robotów są rzadkie i drogie. | arXiv 2310.08864, 2504.16054 | [LIT] VERIFIED |
| P6 | **Brak szybkiej adaptacji „w locie”** w manipulacji. W lokomocji jest rozwiązanie (RMA: adaptacja „w ułamkach sekundy”, trenowane tylko w symulacji), w manipulacji z kontaktem — nie znalazłem odpowiednika o porównywalnej sile dowodu. | arXiv 2107.04034 (abstrakt) | [LIT] VERIFIED / INFERRED |
| P7 | **Opóźnienie i hierarchia.** Duże modele myślą wolno; dlatego π0 ma osobny „action expert”, a Gemini rozdziela rozumowanie i działanie. To proteza tego, co zwierzęta mają w odruchach. | rozdziały filmu Welch Labs (Action Expert), Gemini 1.5 abstrakt | [LIT] PARTIALLY VERIFIED + INFERRED |

**Klasyczne sterowanie** (MPC, impedancja) jest precyzyjne i niezawodne w znanym świecie, ale wymaga ręcznego modelu i źle znosi nowe obiekty — to wiedza ogólna, NOT VERIFIED w tym raporcie (nie otwierałem źródła).

**Hype:** hasło „ChatGPT moment dla robotyki” — dane z P2–P5 go nie wspierają. [INFERRED]

---

## 3. Pytanie 2 — co zwierzęta umieją, a roboty nie, i jak to jest zbudowane

| # | Zdolność | Jak to jest zbudowane | Źródło | Status |
|---|---|---|---|---|
| Z1 | **Ucieczka w kilka uderzeń skrzydeł.** Mucha robi przechylony zwrot „w ciągu kilku uderzeń skrzydeł”, szybciej niż zwykłe skręty. | Krótka droga wzrok→mięśnie, osobny tryb ucieczki | Muijres et al. 2014, Science (abstrakt; liczby czasu nie są w abstrakcie) | [LIT] VERIFIED (bez liczb) |
| Z2 | **Nie myli własnego ruchu z ruchem świata.** Neurony wzrokowe muchy dostają sygnał motoryczny przy własnym skręcie; potencjały zaczynają się przed ruchem skrzydeł (−39 ms / −25 ms dla skrętów w lewo/prawo, komórki HSN). | **Kopia eferentna** — mózg odejmuje skutek własnego ruchu | Kim, Fitzgerald, Maimon 2015, Nat Neurosci (część pełnego tekstu, PMC) | [LIT] VERIFIED |
| Z3 | **Stały wewnętrzny „kompas”.** Populacja neuronów koduje kierunek, trzyma go w ciemności dzięki ruchowi własnemu; proponowany atraktor pierścieniowy. | Kompleks centralny, aktywność trwała | Seelig & Jayaraman 2015, Nature (abstrakt) | [LIT] VERIFIED |
| Z4 | **Powrót do domu bez GPS** (pszczoła). Kompas z polaryzacji + licznik przepływu optycznego zbiegają się w kompleksie centralnym; model obwodu testowany na robocie. | Ten sam kompleks centralny co Z3 | Stone et al. 2017, Curr Biol (abstrakt; „na robocie” z prasy) | [LIT] VERIFIED / REPORTED (robot) |
| Z5 | **Uczenie z małej liczby prób, lokalnie.** Różne typy neuronów dopaminowych zapisują lub osłabiają pamięć według własnych reguł, zależnie od czasu względem zapachu. | Ciało grzybkowate, reguły lokalne | Aso & Rubin 2016, eLife (abstrakt; słowa „one-trial” brak) | [LIT] VERIFIED |
| Z6 | **Ciało liczy za mózg.** Podatne ciało może realizować nieliniowe operacje; uczenie sterowania staje się prostsze. | Obliczenia morfologiczne | Hauser et al. 2011, Biol Cybern (abstrakt) | [LIT] VERIFIED |
| Z7 | **Chwyt sterowany dotykiem.** Sygnały z opuszków kodują zdarzenia kontaktu i służą do bieżącej korekty. | Mechanoreceptory + szybkie pętle | Johansson & Flanagan 2009, Nat Rev Neurosci (abstrakt; brak liczb) | [LIT] VERIFIED (bez liczb) |
| Z8 | **Hierarchia ruchu.** Te same elementy hierarchii powtarzają się w ssakach i dobrych systemach sztucznych. | Rdzeń/pień — szybko, kora — wolno | Merel, Botvinick, Wayne 2019, Nat Commun (abstrakt) | [LIT] VERIFIED |
| Z9 | **Mały budżet.** Mózg muchy: 139 255 neuronów, ok. 5×10⁷ synaps. | — | Dorkenwald et al. 2024, Nature (abstrakt) | [LIT] VERIFIED |

Zużycia energii mózgu muchy w watach **nie znalazłem** w recenzowanej pracy 2024–2026 — nie podaję liczby. [NOT VERIFIED]

**Wniosek [INFERRED]:** wspólny wzór Z1–Z8 to nie „lepszy algorytm”, tylko **architektura wielu pętli o różnych szybkościach, z czuciem i przewidywaniem skutków własnego ruchu, ze stałym stanem wewnętrznym i lokalnym uczeniem**. VLA ma z tego głównie hierarchię (P7), resztę słabo albo wcale.

---

## 4. Pytanie 3 — które luki da się zamknąć w kilka lat i czym

| Luka | Szansa na kilka lat | Potrzebna zasada | Status |
|---|---|---|---|
| Siła/dotyk w pętli (P1, Z7) | **Wysoka** — trwa wiele prób (VFA, ForceVLA, TaF-VLA w wynikach wyszukiwania) | Szybka pętla siły pod wolnym modelem wizualnym | INFERRED |
| Szybka adaptacja (P6) | **Średnio-wysoka** — RMA działa w lokomocji | Moduł szacujący „ukryte warunki” z historii czucia, polityka bazowa bez zmian | INFERRED |
| Opóźnienie / odruchy (P7, Z1, Z2) | **Średnia** | Odruchy na dole + kopia eferentna (przewidywanie skutku własnego ruchu) | HYPOTHESIS |
| Energia małych pętli | **Średnia, niszowa** — dron na Loihi: 200 Hz, 7–12 mW ponad 0,94 W spoczynku | Sieci impulsowe + kamery zdarzeniowe | [LIT] VERIFIED / INFERRED |
| Model świata do planowania | **Średnia** — V-JEPA 2-AC: <62 h nieopisanych filmów robota, zero-shot pick-and-place na Franka w 2 labach | Przewidywanie w przestrzeni ukrytej | [LIT] VERIFIED (abstrakt) |
| Niezawodność „rok bez awarii”, zdrowy rozsądek, uczenie z 1 próby w otwartym świecie | **Niska** w kilka lat | nieznana | INFERRED |

**Architektura, która z tego wynika [PROP, HYPOTHESIS]:** „zwierzę z dobudowaną korą” — wolny model (VLA/model świata) wybiera cel; pod nim szybka warstwa z siłą, dotykiem, kopią eferentną i stałym stanem; ciało podatne tam, gdzie się da. To jest zbieżne z W3 z raportu `vla_with_fly_design_20261112.md` — nie nadpisuję go, tylko zauważam zgodność.

---

## 5. Pytanie 4 — istniejące prace w tym kierunku i co naprawdę pokazały

| Praca | Co pokazała | Czego **nie** pokazała | Status |
|---|---|---|---|
| Shiu et al. 2024, Nature — model LIF całego mózgu muchy | Sama łączność + przekaźnik trafnie przewiduje neurony smaku i karmienia; przewidywania potwierdzone optogenetyką; obwód czyszczenia czułków | Sterowania ciałem / robotem | [LIT] VERIFIED |
| Lappalainen et al. 2024, Nature — sieć wzrokowa z konektomu (64 typy komórek) | Przewidywania zgodne z pomiarami z 26 badań; działa lepiej przy rzadkich połączeniach | Że to lepszy detektor ruchu dla robota | [LIT] VERIFIED |
| NeuroMechFly v2, Nat Methods 2024 | Ciało muchy w symulacji ze wzrokiem, węchem, czuciem; sieć wzrokowa z konektomu do podążania za inną muchą | Prawdziwego robota | [LIT] VERIFIED |
| Vaxenburg et al. 2025, Nature — ciało muchy w MuJoCo | Realistyczny chód i lot, sterownik uczony RL; hierarchia (wysoki poziom używa wytrenowanego niskiego) | Sterownik nie jest z konektomu | [LIT] VERIFIED |
| Lechner et al. 2020, Nat Mach Intell — NCP | Mały sterownik (19 neuronów kontrolnych wg opisu) inspirowany C. elegans prowadzi samochód | Inspiracja, nie konektom; liczby z wyszukiwania, nie z pracy | [LIT] PARTIALLY VERIFIED (DOI/tytuł przez Crossref) |
| Paredes-Vallés et al. 2024, Sci Robot — dron neuromorficzny | Pełna pętla wzrok→sterowanie na Loihi, sim-to-real, zawis i lądowanie, 7–12 mW sieci | Złożonych zadań; sieć nie z biologii | [LIT] VERIFIED |
| Stone et al. 2017 — obwód pszczoły | Pełny biologicznie ograniczony model nawigacji | Skali, odporności w terenie (robot opisany w prasie) | [LIT] VERIFIED / REPORTED |
| RMA 2021 | Adaptacja w ułamkach sekundy, trening tylko w symulacji | Manipulacji | [LIT] VERIFIED |
| Zador et al. 2023 — „ucieleśniony test Turinga” | Program badań: celować w umiejętności wspólne zwierzętom, nie w język | Żadnego wyniku eksperymentalnego (to perspektywa) | [LIT] VERIFIED |

**Wniosek [INFERRED]:** prace z konektomem dowodzą, że **połączenia niosą informację o funkcji** (dobra nauka). Prace inżynierskie dowodzą, że **zasady biologiczne** (hierarchia, adaptacja, zdarzenia, niska moc) działają w robotach. **Nikt nie pokazał, że skopiowany konektom jest lepszym sterownikiem robota niż sieć uczona.** To otwarte — i sporne.

---

## 6. Porównanie: VLA vs VFA vs zwierzę vs FlyMind (prośba Adama)

### 6.1 Film Welch Labs (Adam podał link)
„Inside the World's Smartest Robot Brain [VLA]”, Welch Labs, opublikowany 4 IV 2026, ok. 35 min. Przeczytałem **metadane i opis z rozdziałami**, transkrypcji nie udało się pobrać. Rozdziały: SayCan → RT-1 → PaLM-E → RT-2 → π0 (PaliGemma + „action expert”) → „Just a Demo?” → modele świata i LeCun. W opisie autorzy sami zaznaczają, że w pokazanym odcinku zdejmowania skuwki **π0 nie steruje robotem, tylko działa offline na nagranych danych**. [LIT, VERIFIED — opis; treść filmu NOT VERIFIED]
Ten film to dobra lekcja, jak działa VLA, a nie dowód, że działa niezawodnie. Pytanie „Just a Demo?” to dokładnie P2 z pkt 2. [INFERRED]

### 6.2 Tabela

| Cecha | VLA (π0/π0.5, Gemini Robotics) | VFA (Eka) | Mucha (biologia) | FlyMind V5 [FM] |
|---|---|---|---|---|
| Główny sygnał | obraz + język | obraz + **siła** | wzrok, dotyk, propriocepcja, zapach, stan wewnętrzny | 1 liczba na stronę (obraz → lewo/prawo) |
| Skąd wiedza | imitacja, dużo danych (π0.5: ~400 h + 97,6% innych źródeł) | RL w symulacji fizyki (wg prasy) | ewolucja + uczenie lokalne | połączenia z MaleCNS, bez uczenia |
| Język / ogólność zadań | **tak** | nie wiadomo; pytanie, czy wyjdzie poza pick-and-place | nie | nie |
| Szybka pętla / odruch | osobny „action expert” | deklarowana szybkość 1500 chwytów/h | tak, wiele pętli (Z1, Z2) | sieć ALIF; z opóźnieniem 50 ms spada do 17/40 |
| Dotyk / siła | słabo (P1) | **tak, rdzeń** | tak | dotyk tylko w osobnym etapie chwytu (vision-in-loop), bez korzyści integracji |
| Stan wewnętrzny, plastyczność | kontekst modelu | nieznane | tak (Z3, Z5) | **brak**; neuromodulatory bez efektu w kodzie |
| Dowód | papiery + niezależny test Penn (42,3% postępu) | **tylko deklaracje firmy**, brak publikacji | dziesiątki lat nauki | 38/40 vs tasowanie 3/40; chwyt 90/135 (4. z 11; klasyczny 93) |
| Status | [LIT] VERIFIED / PARTIALLY | [LIT] REPORTED | [LIT] VERIFIED | [FM] REPORTED (liczby z promptu Adama) |

**Czy VFA to „rewolucja”? [INFERRED]** To trafny kierunek (P1 to największa luka), i zgodny z biologią (Z6, Z7). Ale: brak artykułu, brak niezależnego testu, liczby z labu, sceptycyzm zewnętrznego eksperta (K. Hauser, UIUC: czy rok bez awarii; czy poza pick-and-place). Wycena 1,45 mld USD to nie dowód. Etykieta: **obiecujące, niesprawdzone**.

**Lekcja z VFA dla FlyMind [INFERRED]:** VFA rezygnuje z języka i stawia na siłę — czyli robi to, co FlyMind mógłby robić naturalnie (odruchy, dotyk). Ale VFA uczy się na ogromnej liczbie symulacji, a FlyMind nie uczy się wcale. To główna różnica, nie konektom.

---

## 7. Pytanie 5 — FlyMind: gdzie realny wkład, a gdzie udawanie

### 7.1 Gdzie realny, sprawdzalny wkład [PROP, HYPOTHESIS — wszystko NOT IMPLEMENTED]

| # | Pomysł | Dlaczego realne | Jak sprawdzić |
|---|---|---|---|
| R1 | **„Czy połączenia z danych mają znaczenie w zamkniętej pętli robota?”** jako główne pytanie naukowe | Literatura (pkt 5) pyta o to w modelach mózgu, rzadko w pętli z ciałem robota; FlyMind już ma kontrole (tasowanie 3/40, zamiana stron 0/40, brak obrazu 0/40) | Te same kontrole na kolejnych zadaniach; dopasowane sieci losowe o tych samych statystykach |
| R2 | **Test opóźnienia i kopii eferentnej** | 50 ms → 17/40 to mierzalna słabość; Z2 to biologiczne rozwiązanie właśnie tego | Czy dodanie kopii własnej komendy do wejścia wzrokowego przywraca wynik — tylko jeśli odpowiednie połączenia są w MaleCNS (NOT VERIFIED) |
| R3 | **Mały, otwarty benchmark** (scena + kontrole + baza klasyczna + odruch) | P4 mówi, że ocena to wąskie gardło; niewiele osób robi uczciwe kontrole | Opublikować protokół z wynikami ujemnymi |
| R4 | **Uczciwy raport „czego konektom nie daje”** | Wyniki ujemne są rzadkie i cenne | Chwyt: klasyczny 93 > sieć 90 > odruch 80 — to już jest wynik |

### 7.2 Gdzie byłoby udawanie [INFERRED]
- „FlyMind rewolucjonizuje AI robotów” — brak dowodu na przewagę nad klasyką (90 vs 93), nie mówiąc o VLA.
- „Mucha jest mądrzejsza od VLA” — porównanie nieuczciwe: inne zadania, 1 liczba wejścia/wyjścia.
- „Neuromodulacja / uczenie / pamięć w FlyMind” — w kodzie nie ma plastyczności, stanu ani działających neuromodulatorów.
- „Konektom muchy steruje ramieniem jak mucha nogą” — mapowanie noga→szczęka/ramię jest inżynierskie.
- „Sprawdzone na prawdziwym robocie” — tylko symulacja.
- Każde „rewolucja”, „pierwszy na świecie” bez przeszukania literatury pod tym kątem.

### 7.3 Zgodność z zasadą z 3 XI („mucha ma sterować”)
R1–R4 zostawiają sterowanie sieci muchy; klasyka tylko jako baza i bezpieczeństwo. R2 dodaje sygnał do sieci, nie zastępuje jej. E1–E3, P1–P7, S1–S7, U1–U5 nadal niezatwierdzone i ich nie uruchamiam. [FM]

---

## 8. Co jest sporne lub nieznane — wprost
- Czy konektom daje przewagę **inżynierską** (a nie tylko naukową) — **nieznane**, brak dowodu.
- Czy VLA „skalują się” do niezawodności — **sporne**; laby mówią tak, testy niezależne pokazują ok. 42% postępu.
- Liczby Eka — **niesprawdzone**, deklaracje firmy.
- Liczby Gemini 1.5 z dalszych sekcji — tylko ze streszczenia.
- Film Welch Labs — znam tylko opis i rozdziały.
- Wszystkie prace z Nature/Science — tylko abstrakty.

---

## 9. Proponowane następne kroki — **żadnego nie zaczynam**
1. Decyzja Adama: czy główne pytanie FlyMind zmienić na R1 („czy połączenia mają znaczenie w pętli”).
2. Tylko analiza danych (bez symulacji): czy w MaleCNS są połączenia pasujące do kopii eferentnej dla obwodu LC10a→DNa02 (warunek R2).
3. Plakat 16 XI: dodać jedną uczciwą tabelę jak w 6.2 (FlyMind obok VLA i VFA, z etykietami).
4. Jeśli chodziło o inne „VFA” — wskazać, uzupełnię pkt 6.

---

## 10. Źródła i co z nich przeczytałem

| Źródło | ID / URL | Co przeczytałem |
|---|---|---|
| Shao et al. 2025, przegląd VLA | arXiv 2508.13073 | abstrakt |
| Kawaharazuka et al. 2025, przegląd VLA | arXiv 2510.07077 | abstrakt |
| Physical Intelligence, π0.5 | arXiv 2504.16054 | abstrakt + ok. 1/3 tekstu HTML |
| Gemini Robotics Team, GR 1.5 | arXiv 2510.03342 | abstrakt + ok. 1/5 tekstu HTML, reszta ze streszczenia |
| Wang et al. (Penn), π0 in the Wild | https://penn-pal-lab.github.io/Pi0-Experiment-in-the-Wild/ | cała strona |
| Xie & Correll 2025 | arXiv 2504.11827 | abstrakt |
| Open X-Embodiment | arXiv 2310.08864 | abstrakt |
| Assran et al. 2025, V-JEPA 2 | arXiv 2506.09985 | abstrakt |
| Kumar et al. 2021, RMA | arXiv 2107.04034 | abstrakt |
| Paredes-Vallés et al. 2024 | doi:10.1126/scirobotics.adi0591; arXiv 2303.08778 | abstrakty (Europe PMC + arXiv) |
| Shiu et al. 2024 | doi:10.1038/s41586-024-07763-9 | abstrakt (Europe PMC) |
| Lappalainen et al. 2024 | doi:10.1038/s41586-024-07939-3 | abstrakt (Europe PMC) |
| Wang-Chen et al. 2024, NeuroMechFly v2 | doi:10.1038/s41592-024-02497-y | abstrakt (Europe PMC) |
| Vaxenburg et al. 2025 | doi:10.1038/s41586-025-09029-4 | abstrakt (Europe PMC) |
| Zador et al. 2023 | doi:10.1038/s41467-023-37180-x | abstrakt (Europe PMC) |
| Lechner et al. 2020 | doi:10.1038/s42256-020-00237-3 | tylko metadane (Crossref); treść z wyników wyszukiwania |
| Stone et al. 2017 | doi:10.1016/j.cub.2017.08.052 | abstrakt (Europe PMC) |
| Kim, Fitzgerald, Maimon 2015 | doi:10.1038/nn.4083; PMC6327952 | abstrakt + ok. 40% pełnego tekstu |
| Muijres et al. 2014 | doi:10.1126/science.1248955 | abstrakt (Europe PMC) |
| Seelig & Jayaraman 2015 | doi:10.1038/nature14446 | abstrakt (Europe PMC) |
| Merel, Botvinick, Wayne 2019 | doi:10.1038/s41467-019-13239-6 | abstrakt (Europe PMC) |
| Aso & Rubin 2016 | doi:10.7554/eLife.16135 | abstrakt (Europe PMC) |
| Hauser et al. 2011 | doi:10.1007/s00422-012-0471-0 | abstrakt (Europe PMC) |
| Johansson & Flanagan 2009 | doi:10.1038/nrn2621 | abstrakt (Europe PMC) |
| Dorkenwald et al. 2024, FlyWire | doi:10.1038/s41586-024-07558-y | abstrakt (Europe PMC) |
| SiliconANGLE o Eka (20 X 2026) | https://siliconangle.com/2026/10/20/eka-robotics-nets-150m-at-a-1-45b-valuation-for-robot-hands-that-sense-force/ | cały artykuł |
| The AI Insider o Eka (20 X 2026) | https://theaiinsider.tech/2026/10/20/eka-robotics-raises-150m-series-a-to-scale-vision-force-action-model-for-dexterous-robots/ | początek artykułu (trening: symulacja + RL) |
| Welch Labs, film VLA | https://www.youtube.com/watch?v=2mrGMMmrVNE | metadane, opis, rozdziały; bez transkrypcji |

Nieudane / nieużyte: blog Physical Intelligence „olympics” (blokada bota) — nie cytuję; indiatechreport.in (błąd DNS) — nie cytuję.

---

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
