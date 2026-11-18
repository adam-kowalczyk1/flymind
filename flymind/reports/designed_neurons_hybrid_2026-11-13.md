# Projektowane neurony mogą tłumaczyć, ale nie decydować

**Jak czytać.** Dla Adama: „Najkrócej”, Słowniczek, pkt 5, pkt 6 i „Decyzje” (ok. 10 min; **pilne do 16 XI: DH6, plakat**). Dla weryfikatora: pkt 2, 4.2 i 7–11.

**Data:** 2026-11-13
**Autor:** Claude (Opus 5.5), na prośbę Adama; to nie jest niezależna recenzja
**Nic nie zbudowano i nic nie uruchomiono poza zapytaniami tylko do odczytu do lokalnych danych MaleCNS.** Skrypty (scratchpad, katalog `/private/tmp/claude-501/-Users-admin--claude-spares-spare-72aeAc/18088efc-118a-40f7-a6fd-25f3036bed30/scratchpad/`):
- `malecns_queries/q1_annotations.py`, `q2_legmn.py`, `q3_jointgroups.py`, `q4_scan.py`, `q4_report.py`, `q5_dn_types.py`, `q6_scan_thr.py`, `q6_report.py`, `q7_hops_nt_an.py`, `q8_nonleg_search.py`, `q9_synonyms.py` (wyniki w plikach `*.out` obok);
- niezależne powtórzenie przez weryfikatora: `malecns_verify/v1.py`, `v2.py`, `v3.py`.

Scratchpad może zostać wyczyszczony; dosłowne kopie skryptów `q*` są w `research_notes/Projektowane neurony i hybryda z muchą/malecns_local_queries.md` (sekcja „Script sources”). Poza tym wykonano tylko zapytania HTTP do baz bibliograficznych (Crossref, Europe PMC, arXiv, bioRxiv API, Semantic Scholar, DOAJ, YouTube oEmbed, Lacuna). Zapisane pliki: ten raport oraz nowy folder `research_notes/Projektowane neurony i hybryda z muchą/` (14 plików: 7 notatek + 7 weryfikacji `__weryfikacja.md`); skrypty i wyniki zapytań są tylko w scratchpadzie. Niczego istniejącego nie nadpisano; kodu ani wyników FlyMind nie zmieniono. Nie podłączano robota, nic nie commitowano.

**Skąd są dane w raporcie.** Raport łączy 7 notatek badawczych i 7 plików weryfikacji (`*__weryfikacja.md`) z folderu `/Users/admin/so101_fly_project/research_notes/Projektowane neurony i hybryda z muchą/`. Gdzie weryfikacja poprawiła notatkę, używam wersji poprawionej. Twierdzeń obalonych albo nie do sprawdzenia nie używam jako dowodu. Sam dodatkowo przeczytałem (tylko odczyt):
- `flymind/FLYMIND_MASTER_CONTEXT.md` (zasada nr 1, tabela stawów, wyniki, plan plakatu);
- `flymind/VALIDATION_PLAN.md`, wiersze ok. 175–250 (red team V5, V5 v2);
- `flymind/reports/bio_advantage_research_20261110.md`, wiersze 86–99;
- `flymind/experiments/fj2_fly_arm/DESIGN.md` i `PILOT_NOTES.md`;
- `flymind/results/audit_shared_decoder_20261029.txt`;
- `research_notes/Hybrydowe mózgi z konektomów/laczenie_modyfikacje.md`, fragmenty (Spaun, NRP, Dhiman, Therianos, taksonomia 5 klas; pkt 3.5);
- pliki `*.out` ze skryptów MaleCNS.

Policzyłem też przedziały Wilsona jedną linijką arytmetyki (komenda w pkt 7).

---

## Najkrócej

1. Sztuczne neurony impulsowe do robotów powstają na dwa sposoby. Albo ktoś ręcznie projektuje połączenia (lub „kompiluje” je z wzoru, jak w metodzie NEF), albo wagi uczy się w symulatorze. Wśród przeczytanych prac jedyne liczbowe wyniki dla ramienia wielostawowego ze SNN uczoną od początku do końca pochodzą z uczenia w symulacji. Projektowane kontrolery wielostawowe istnieją (np. Zaidel 2021, DeWolf 2016/2020), ale mają wyniki opisowe. Rzadko kto porównuje je z prostym klasycznym regulatorem (INFERRED, ok. 10 prac, głównie abstrakty).
2. Nie znalazłem opublikowanej pracy z takim schematem jak na filmie Founders, Inc. (para neuronów „plus/minus” nazwanych od stawu SO-101; INFERRED z braku trafień). Według transkrypcji od Adama film nie podaje metody, liczby prób ani kontroli, a „98%” dotyczy symulowanego robota z czujnikami zbliżeniowymi, nie ramienia (REPORTED); dlatego „98%” to NOT VERIFIED. Mrówka to w filmie tylko plan.
3. Do sieci z konektomu dołącza się ręcznie dobrane odczyty i uczone kontrolery ciała (Eon Systems, NeuroMechFly v2; REPORTED). W przeczytanych źródłach (dla NeuroMechFly v2 tylko abstrakt) nie znalazłem testu, że to mucha, a nie część dołączona, decyduje (INFERRED, argument z braku). FlyGM i (przy słabszym tasowaniu) Shiu 2024 pokazują, że okablowanie z danych ma znaczenie, ale nie rozstrzygają, kto decyduje (REPORTED). Preprint „digital sphinx” pokazuje, że wyuczony łącznik potrafi „poruszyć” ciało muchy nawet mózgiem robaka (REPORTED, abstrakt).
4. Biologia opisuje podział ról: mózg wybiera ruch przez ok. 1300 neuronów zstępujących (DN), a zwój brzuszny (VNC) zamienia to na pracę mięśni nóg (REPORTED: Cheong 2026, Stürner 2025, Braun 2024). W naszych danych MaleCNS 84–88% wejścia do neuronów ruchowych lewej środkowej nogi (T2L) pochodzi z interneuronów VNC, a tylko 6–7% wprost z DN (VERIFIED, własne zapytania). Anatomia naszych danych jest z tym zgodna, ale to liczby synaps, nie dowód funkcji (INFERRED).
5. Z zasadą z 3 XI zaprojektowana warstwa zgadza się tylko jako „tłumacz”: stała, ustalona przed testem, bez wyboru, bez pamięci i bez bramkowania. Jeśli cokolwiek wybiera, to ona decyduje, nie mucha (INFERRED; kryteria KT1–KT9 i KW1–KW3 w pkt 5 to HYPOTHESIS).
6. Z pięciu wariantów (HA–HE) z zasadą najlepiej zgadza się HE. W nim VNC z danych to część muchy (też decyduje lokalnie: rytm, odruchy), a jedynym zaprojektowanym tłumaczem jest stała, ręcznie ustalona mapa pul neuronów ruchowych → stawy. To rozwinięcie istniejącego projektu FJ2 (INFERRED).
7. **Odpowiedź na pytanie o 6 stawów:** uczciwie najwyżej 4 stawy sterowane przez muchę (podstawa, bark, łokieć, chwytak), a 2 stawy nadgarstka stałe. Pełne 6 stawów oznaczałoby, że brakujące decyzje dopisuje część zaprojektowana (wariant HB/HD) (INFERRED). Dziś w głównych przebiegach mucha steruje tylko podstawą i siłą chwytu.
8. Główne ryzyko: dla barku, łokcia i nadgarstka nie ma rozpoznanego sygnału muchy, a obrót nadgarstka nie ma u muchy żadnego odpowiednika. „Pełna” hybryda na 6 stawów kusi więc, żeby brakujące decyzje dopisała część zaprojektowana (INFERRED). Do tego nasz obecny wynik wzroku mierzy lateralizację (podział na lewo/prawo), nie konkretne połączenia (REPORTED, red team V5).
9. **Pilne do 16 XI: DH6 (plakat).** Rekomendacja: (a), najwyżej (b). **Druga decyzja: DH1.** Czy przyjmujesz KT1–KT9 (pkt 5) jako obowiązującą regułę granicy tłumacz/decyzja, także dla obecnego dekodera DNa02? Niezależnie od odpowiedzi rekomendowany następny krok to DH3: mapa pul neuronów ruchowych → stawy SO-101, zrobiona tylko na danych, bez żadnej symulacji (HYPOTHESIS, plan).

---

## Legenda etykiet

| Etykieta | Znaczenie w tym raporcie |
|---|---|
| **VERIFIED** | Sprawdzone przez nas: policzone z lokalnych danych lub kodu podaną komendą albo istnienie i metadane publikacji (DOI/arXiv rozwiązuje się, tytuł, autorzy i rok się zgadzają). Wynik naukowy z cudzej pracy nigdy nie jest VERIFIED. |
| **PARTIALLY VERIFIED** | Część sprawdzona, część nie. |
| **REPORTED** | Wynik podany przez autorów, firmę, film, prasę albo nasz wcześniejszy plik, którego teraz nie odtwarzaliśmy. W nawiasie: co faktycznie przeczytano („read: abstract / full text / secondary”). |
| **INFERRED** | Nasz wniosek z faktów VERIFIED lub REPORTED. |
| **HYPOTHESIS** | Propozycja albo pomysł niesprawdzony. |
| **NOT VERIFIED** | Nie udało się otworzyć ani potwierdzić źródła. |
| **FAILED** | Próbowano i nie zadziałało albo wynik zaprzeczył twierdzeniu. |
| **NOT IMPLEMENTED** | Nie istnieje w kodzie FlyMind. |

W projekcie obowiązują też metki DATA (z konektomu), MODEL (nasze parametry dynamiki) i ENGINEERING (kamera, enkoder, dekoder, serwa, bezpieczeństwo) z `FLYMIND_MASTER_CONTEXT.md`. Używam ich tam, gdzie pomagają.

### Słowniczek

| Termin | Po ludzku |
|---|---|
| SNN, LIF, ALIF | sieć neuronów impulsowych; LIF to najprostszy model neuronu („zbiera prąd, przecieka, strzela”); ALIF dodaje próg, który rośnie po każdym impulsie |
| DN, AN, MN, VNC | neurony zstępujące (mózg → ciało), wstępujące (ciało → mózg), ruchowe (do mięśni); VNC to zwój brzuszny, „rdzeń kręgowy” muchy |
| IK | kinematyka odwrotna: wzór, który z położenia celu liczy kąty stawów |
| tik | jeden krok sterowania (jedno polecenie dla stawów) |
| ziarno | numer losowania; te same ziarna = te same sceny i ten sam szum |
| tasowanie (blokowe, z zachowaniem siły) | losowe przemieszanie połączeń sieci jako kontrola; „z zachowaniem siły” zostawia każdemu neuronowi tę samą sumę wejścia i wyjścia; „blokowe” miesza tylko w obrębie tej samej klasy, strony i warstwy |
| przekaźnik | najprostszy obwód: lewe oko → lewy DNa02, bez reszty sieci |
| przedział Wilsona | zakres, w którym z 95% pewnością leży prawdziwy wskaźnik sukcesu przy danej liczbie prób |
| McNemar | test porównujący dwa warianty na tych samych scenach (pary prób) |
| poprawka Bonferroniego | ostrzejszy próg istotności, gdy robi się wiele porównań naraz |
| pp | punkty procentowe |
| argmax | wybór największej wartości (czyli wybór jednej opcji) |
| zatrzask | zapamiętany stan, który zmienia dalsze zachowanie (np. „chwyt trwa”) |
| BPTT, gradient zastępczy, e-prop | sposoby uczenia wag SNN „wstecz” od błędu |
| STDP, R-STDP, PES | reguły uczenia w trakcie pracy: „razem zapalone, razem wzmocnione”, wersja z nagrodą, reguła NEF poprawiająca dekoder |
| DDPG, TD3, SAC, PPO | popularne algorytmy uczenia przez nagrodę (RL) |
| FJ1, FJ2 | eksperymenty z 3 XI: FJ1 = chwytak sterowany obwodem dotyku nogi; FJ2 = pilot z kilkoma stawami ramienia sterowanymi pulami MN nogi |
| J0 | siła jednej synapsy w modelu (mV na synapsę) |
| G2 | bramka z planu oka (12 XI): test, czy symulowane neurony ruchu T4/T5 rozróżniają kierunek |
| H3/H4 | kontrole z red teamu V5, które z budowy nie mogły rozróżnić sieci (pkt 8) |
| P | prosty regulator proporcjonalny (klasyczny punkt odniesienia) |

---

## 1. Film Founders, Inc.: dużo widać, mało wiadomo

| Co | Etykieta | Źródło / uwaga |
|---|---|---|
| Tytuł filmu to „he invented an “artificial brain””, kanał Founders, Inc. (@fdotinc). | VERIFIED | YouTube oEmbed, sprawdzone 13 XI 2026: `curl 'https://www.youtube.com/oembed?url=https://youtu.be/NIMEbZJHQBM&format=json'` ([oEmbed](https://www.youtube.com/oembed?url=https://youtu.be/NIMEbZJHQBM&format=json)) |
| Data publikacji, opis i linki w opisie | NOT VERIFIED | Strona filmu nie zwróciła opisu ([film](https://youtu.be/NIMEbZJHQBM)) |
| Kim jest Alexander, czy jest repozytorium, artykuł albo produkt | NOT VERIFIED | Dwa wyszukiwania nie znalazły nic o tym filmie. To znaczy tylko tyle, że my nic nie znaleźliśmy. |
| Na ekranie: interfejs „SO101 Full Cortical Body Motion v1.15”; neurony `shoulder_pan_pos_theta1`, `shoulder_pan_neg_theta2`, `elbow_flex_pos_beta`; raster impulsów; wykres napięcia błony; kod w stylu `synapse(pre, post, weight)`; zakładki „Training” i „Connect to Robot” | REPORTED | Obserwacja Adama z obrazu. Claude filmu nie oglądał. To obserwacje obrazu, nie fakty o metodzie. |
| Napis „98% kolizji ominiętych bez treningu” | **NOT VERIFIED** | Nakładka z montażu. Brak liczby prób, definicji kolizji, opisu scen i kontroli. |
| Dane o mózgu mrówki | brak | Mrówka to w filmie tylko **cel na przyszłość** („zaczynamy od mózgu mrówki”, „kolejny kamień milowy”). Danych, konektomu ani modelu mrówki film nie pokazuje (REPORTED, transkrypcja od Adama). |

**Uzupełnienie 13 XI: transkrypcja filmu od Adama.** Adam wkleił streszczenie i pełną transkrypcję (EN + PL). Nie porównałem jej z nagraniem, więc wszystko poniżej to REPORTED (źródło: transkrypcja od Adama).

| Co mówi film | Etykieta | Uwaga |
|---|---|---|
| Alexander jest founderem w inkubatorze Founders, Inc. (wcześniej pracował na University of British Columbia, w SF od V 2025). | REPORTED | Brak nazwiska, firmy, repozytorium i publikacji. |
| Metoda: „zbadaliśmy, jak działają neurony, i zamieniliśmy to w algorytm”; najpierw symulacja jednego neuronu, potem „matematyka”. | REPORTED | Brak modelu neuronu, liczby neuronów i sposobu łączenia. Nic nie wskazuje na dane z konektomu. |
| Neurony „w czasie rzeczywistym” na jego komputerze **bezpośrednio poruszały prawdziwym ramieniem**. | REPORTED | Pokazano tylko ruch. Zadanie, cel, dokładność i liczba prób nie padają. Narrator pyta wprost: „czy potrafi nim ruszać w użyteczny sposób?”. |
| **„98% kolizji ominiętych”** dotyczy **symulowanego robota z czujnikami zbliżeniowymi**, a nie ramienia SO-101. Eksperyment „powtarzał raz za razem”. | REPORTED; liczba nadal **NOT VERIFIED** | Brak liczby prób, scen, definicji kolizji i punktu odniesienia. To dokładnie przypadek z pkt 2.6: odruch czujnik → skręt (typ Braitenberga) z natury omija przeszkody bez treningu (INFERRED). |
| „Żadnego trenowania, żadnego RL — sama neurodynamika”. | REPORTED | Na ekranie jest zakładka „Training”. Bez treningu wag nie znaczy bez ręcznego strojenia (pkt 2.6, INFERRED). |
| Uzasadnienie: obecne AI potrzebuje milionów filmów i GPU, mózg zużywa ok. 20 W. | REPORTED | Ogólny argument energetyczny (pkt 2.7). Nic nie zmierzono dla jego układu. |

**Co to zmienia (INFERRED).** Wynik „98%” nie dotyczy ramienia ani muchy, tylko innego, symulowanego robota. Film nie twierdzi, że ramię wykonuje jakieś zadanie. Wniosek z pkt 6 zostaje: to wariant HD (projektowany, bez danych z konektomu), a dla FlyMind co najwyżej ramię porównawcze. Nasz projekt różni się tym, że ma dane MaleCNS i jawne kontrole; to jest jego mocna strona, nie słabość.

**Uzupełnienie 13 XI (2): artykuł i strona od Adama.**

Źródła:
- [arXiv 2611.13840](https://arxiv.org/abs/2611.13840): Alexander A. Wolf, „Oscillatory Processing Units as a computing substrate for biomimetic intelligence”, v1 z 10 XI 2026, cs.NE/cs.ET/cs.RO, 39 stron. Metadane sprawdzone przez arXiv API (VERIFIED). Treść przeczytana ze źródeł TeX (`main.tex`) i plików `anc/` (read: full text).
- Strona [artificialbrains.ai](https://artificialbrains.ai): odczytałem tylko tytuł „Artificial Brains | Synthetic Neurons for Robots”, bo reszta ładuje się skryptem (VERIFIED, tylko tytuł).
- Że to ten sam Alexander co w filmie, wnioskuję z imienia, nazwy „Artificial Brains” (README artykułu) i tematu (INFERRED).

| Co mówi artykuł | Etykieta | Uwaga dla nas |
|---|---|---|
| Model neuronu jest **zastrzeżony** („proprietary”). Opisano go tylko słownie: kumulacja wejścia, zanik, własny rytm modulujący odpowiedź. Surowe impulsy i konfiguracje obwodów nie są udostępnione. | REPORTED (full text) | Nie da się tego odtworzyć ani sprawdzić. |
| OPU to grupa neuronów o wspólnym rytmie (gamma, beta, alfa, theta, delta). Obwody są „skonfigurowane” ręcznie, a wagi stałe: bez nagrody i bez uczenia wstecz. | REPORTED (full text) | To wariant HD: całość zaprojektowana, **zero danych z konektomu**. |
| **Omijanie przeszkód** (wirtualny robot, ok. 1400 neuronów): prawe ryzyko → skręt w lewo, lewe ryzyko → skręt w prawo, plus wzajemne hamowanie dwóch pul ruchowych. Badanie miało 120 przebiegów: 8 nowych sieci × 3 odłożone światy × 5 warunków. Pełny obwód miał kolizję w 0,0083% tików, a pozorny obwód (sham, przekierowane połączenia) w 96,9%. Przebiegi bez kolizji: 23 z 24. | REPORTED (full text, ryc. 7, `avoidance_pooled_behavior.csv`) | Liczba „98%” z filmu **w artykule nie występuje**. |
| Kontrole: sham z tą samą liczbą połączeń; **odwrócone strony** (czyste otoczenie 8,2% zamiast 92,6%); usunięta konkurencja (stop 42% zamiast 0,06%). Test znaku na 8 sieciach (P = 0,0078; po Holmie 0,016). Druga, z góry zapowiedziana prognoza **nie wyszła** (korelacja −0,213 przy oczekiwanej dodatniej). | REPORTED (full text) | Uczciwie podany wynik negatywny. Kontrole są podobne do naszych (zamiana stron, wyciszenie). |
| **Brak trywialnego punktu odniesienia**, np. „jeśli czujnik po prawej, skręć w lewo” bez neuronów. | INFERRED (brak w tekście) | Ta sama luka co u nas przed red teamem: obwód skrzyżowany jest **z budowy** odruchem Braitenberga. Nasza lekcja (przekaźnik lewy → lewy daje 20/20) dotyczy jego wyniku tak samo. |
| Pokazy fizyczne: robot **ANT** (ok. 1400 neuronów, 4 czujniki ultradźwiękowe, kamera z zewnętrznym detektorem celu; sieć wybiera szukanie, podejście albo omijanie), **ręka** (ok. 3400 neuronów, dotyk reguluje chwyt), dron w Webots. Autor sam pisze, że dla tych pokazów **nie podaje wskaźnika sukcesu**. | REPORTED (full text) | „ANT” to nazwa robota. O mózgu mrówki ani o danych biologicznych artykuł nic nie mówi. |
| Ramię SO-101 i neurony nazwane od stawów | **brak w artykule** | Interfejs z filmu nie jest opisany w pracy. |
| Podział pracy: oprogramowanie robi czujniki, kodowanie, detektor obrazu, przeliczenie na silniki i bezpieczeństwo. Sieć tylko wybiera akcję. | REPORTED (full text) | To ten sam podział co w naszym KT/KD: wybór akcji ma należeć do sieci, a reszta jest jawnie inżynierią. |

**Wniosek (INFERRED).** Artykuł jest staranniejszy niż film: ma sieci odłożone, zapowiedziane testy, sham i podaje porażkę. Jednak:
- neuron jest tajny;
- obwód jest w całości zaprojektowany (HD);
- najmocniejszy wynik dotyczy odruchu, który z budowy omija przeszkody, a nie ma porównania z prostą regułą.

Dla FlyMind to dobry **wzór raportowania** (sham z tym samym budżetem połączeń, odłożone sieci i światy, test znaku po sieciach). Jest też gotowym ramieniem porównawczym HD, gdyby kod był dostępny, a nie jest. Nic z tego nie zmienia rekomendacji HE.

**Do czego to podobne.** Nazwy neuronów wyglądają tak: nazwa stawu + kierunek („pos”/„neg”) + grecka litera. Nazwy sugerują (HYPOTHESIS), że wyjścia przypisano ręcznie do stawów; zakładka „Training” wskazuje, że część wag mogła być uczona. Metoda jest nieznana. Nie wiadomo też, co znaczą litery theta i beta.

Najbliższe opublikowane odpowiedniki (szczegóły w pkt 2.3):
- komórki wyjściowe dla zginacza i prostownika jednego stawu (Chadderdon 2012, przez przegląd Bing 2018);
- kodowanie przedziałów kąta z regułą Hebba (Hulea 2021);
- R-STDP na ramieniu z jednym stawem (Juarez-Lora 2022).

W literaturze o omijaniu przeszkód „bez treningu” zwykle oznacza ręcznie zbudowany odruch (typ LGMD) z ręcznie strojonymi parametrami (pkt 2.6). Według zasady z 3 XI taki projekt to wariant HD (całkowicie zaprojektowany, pkt 6). Może u nas służyć co najwyżej jako ramię porównawcze.

**Czego brakuje, żeby ocenić „98%” (INFERRED):**
- liczby prób i układów przeszkód;
- definicji sukcesu;
- informacji, czy testowe przeszkody różniły się od tych użytych przy strojeniu;
- trywialnego punktu odniesienia, np. „zatrzymaj, gdy zadziała czujnik zbliżenia”;
- informacji, czy to symulacja, czy prawdziwe ramię.

---

## 2. Temat 1: jak powstają projektowane neurony i połączenia

### 2.1 Model neuronu: prawie zawsze LIF

| Twierdzenie | Etykieta | Źródło |
|---|---|---|
| Przegląd SNN w robotyce: model LIF (całkuj i odpal z upływem) to jeden z najczęściej używanych, Hodgkin-Huxley jest najbardziej wpływowy, a Izhikevich pojawia się tylko w porównaniach i w regule R-STDP. W przeglądzie nie ma przykładu robota sterowanego modelem HH ani Izhikevicha. | REPORTED (read: full text, Europe PMC PMC6043678) | [Bing et al. 2018](https://doi.org/10.3389/fnbot.2018.00035) |
| Zaidel i in. 2021 (laboratorium Ezry Tsura, Open University of Israel; współautor Supic z Accenture Labs) używają LIF w populacjach NEF, ale nie podają parametrów LIF. Przy 5 wymiarach równomierne „progi zapłonu” (intercepty) nie dawały zbieżności, trójkątne dawały. | REPORTED (read: full text, PMC7887770) | [Zaidel et al. 2021](https://doi.org/10.3389/fnbot.2021.631159) |
| Typowe liczbowe parametry LIF w kontrolerach ramion | NOT VERIFIED (nie znaleziono) | — |
| LIF wybiera się, bo jest tani i wspierany przez narzędzia Nengo i Loihi. Nasz ALIF (z adaptacją progu) jest bardziej szczegółowy niż większość tych kontrolerów. | INFERRED | — |

### 2.2 Połączenia projektuje się na trzy sposoby, a uczenie zwykle się dokleja

**(a) Kompilacja z wzoru (NEF).** U Zaidela populacja „Current q” łączy się z „Target q”. Wagi wynikają z dekoderów i enkoderów, a reguła PES poprawia dekodery w trakcie pracy. PID złożono z torów P, I i D:
- w symulacji kp = 1, ki = 0,1, kd = 0,35, τ = 0,1;
- w tekście dla Loihi podano τ = 10 ms, kp = −1, ki = −0,1, co przeczy podpisowi rysunku („te same parametry”);
- autorzy przyznają, że pochodną trudno było zrobić na Loihi.

REPORTED (read: full text) ([Zaidel 2021](https://doi.org/10.3389/fnbot.2021.631159)).

**(b) Hierarchia „prymitywów ruchowych”.** Tieck i in. sięgają do celu bez kinematyki odwrotnej: sieć łączy prymitywy korekcyjne sygnałem błędu. Dwa eksperymenty, oba w symulacji. REPORTED (read: abstract) ([Tieck et al. 2019](https://doi.org/10.4018/ijcini.2019010101)).

**(c) Małe obwody z regułą Hebba na sprzęcie analogowym.** Hulea i in. sterują jednym stawem palca ze stopu z pamięcią kształtu. Osobne ścieżki neuronów odpowiadają przedziałom kąta. Wynik jest tylko opisowy. REPORTED (read: abstract) ([Hulea et al. 2021](https://doi.org/10.3390/s21082730)).

**(d) Neurony jako PID.** Stagsted i in. zbudowali PID na Loihi dla drona ograniczonego do 1 stopnia swobody i opisują go jako pierwszy w pełni neuromorficzny PID. REPORTED (read: abstract na stronie RSS) ([Stagsted et al. 2020](https://roboticsproceedings.org/rss16/p074.html)). Wcześniejsza notatka podawała też robota mobilnego i opinię recenzenta, że klasyczny PID był lepszy. Weryfikacja nie znalazła ani jednego, ani drugiego, więc te twierdzenia **usuwam**.

**(e) Sekwencje wzorców.** Michaelis i in. budują sieć „anizotropową” na Loihi. Sprawdzono ją na trajektoriach z zadania ramienia robota, ale z abstraktu nie wynika, że sterowała ramieniem. Główny problem: impulsy trwają milisekundy, a sterowanie wymaga setek milisekund. REPORTED (read: abstract) ([Michaelis et al. 2020](https://doi.org/10.3389/fnbot.2020.589532)).

**(f) Generatory rytmu (CPG).** Przegląd Ijspeerta istnieje (VERIFIED, metadane), treści nie czytano ([Ijspeert 2008](https://doi.org/10.1016/j.neunet.2008.03.014)).

**Wniosek (INFERRED).** Wywołanie `synapse(pre, post, weight)` z wagą wpisaną ręcznie to najprostsza forma ręcznego okablowania. NEF to wersja zasadnicza: wagi wynikają tam z zadanej funkcji. W każdym sprawdzonym przykładzie autorzy jasno mówią, które wagi zaprojektowano, a które wyuczono. FlyMind potrzebuje tego samego jawnego podziału. Nasze wagi z konektomu pochodzą z liczby synaps, a nie z funkcji.

### 2.3 Para neuronów „plus/minus” na staw: dobry pomysł, ale bez opublikowanego wzoru

Nie znalazłem opublikowanego schematu z parą neuronów „pos/neg” nazwanych od stawu i literą grecką, jak na filmie (NOT VERIFIED, że taki istnieje). Najbliższe są:

| Praca | Co koduje | Zakres | Etykieta |
|---|---|---|---|
| Chadderdon i in. 2012 (opis w Bing 2018) | komórki wyjściowe zginacza i prostownika | ramię o 1 stawie; 144 neurony pobudzające i 64 hamujące; 5 celów | REPORTED (secondary: Bing 2018, full text) |
| Kaiser i in. 2016 (opis w Bing 2018) | agonista i antagonista „kierownicy” | pojazd, nie ramię | REPORTED (secondary) |
| [Hulea 2021](https://doi.org/10.3390/s21082730) | przedziały kąta; wartość czujnika jako częstość impulsów | 1 staw palca | REPORTED (abstract) |
| [Zaidel 2021](https://doi.org/10.3389/fnbot.2021.631159) | 5 kątów jako jeden wektor w jednej populacji | ramię 6 DOF, 9 serw, 5 stawów w IK | REPORTED (full text) |
| Chen i in. 2020 ([DOI](https://doi.org/10.1109/iciea48937.2020.9248389)); Bouganis i Shanahan 2010 ([DOI](https://doi.org/10.1109/ijcnn.2010.5596525)) | ramię 4-DOF (tytuły) | treści nie czytano | VERIFIED (tylko istnienie) |

**INFERRED.** Para „pos/neg” na staw to naturalny wzór: odpowiada mięśniom antagonistycznym. W FlyMind odczyt „DNa02 lewy minus prawy” jest już taką parą dla obrotu podstawy. To my go zaprojektowaliśmy jako odczyt, więc to ENGINEERING.

W danych MaleCNS najbliższym odpowiednikiem są pule zginaczy i prostowników nogi. Na przykład w T2L: Ti flexor (5 MN) i Acc. ti flexor (6) przeciw Ti extensor (2). Liczby są VERIFIED (pkt 4.2), ale funkcję znamy tylko z nazwy.

### 2.4 Wagi częściej się uczy niż projektuje

| Metoda | Po ludzku | Przykład i wynik | Etykieta |
|---|---|---|---|
| Ręcznie / NEF | wagi wpisane albo wyliczone z wzoru | Zaidel 2021; [DeWolf, Jaworski, Eliasmith 2020](https://arxiv.org/abs/2007.10227): adaptacja neuronowa dodana do klasycznego sterownika siłowego na prawdziwym ramieniu Kinova Jaco2 (uzupełnia klasyczny sterownik, nie zastępuje go) | REPORTED (abstract) |
| STDP / R-STDP | reguła „razem zapalone, razem wzmocnione”, plus nagroda | [Bing et al. 2020](https://doi.org/10.1016/j.neunet.2019.05.019): utrzymanie pasa ruchu, 3 scenariusze; R-STDP lepsze w dokładności i liczbie kroków od 3 innych algorytmów z tej pracy. Ten abstrakt (nie przegląd z 2018) wskazuje brak praktycznych metod uczenia jako główne ograniczenie. [Juarez-Lora et al. 2022](https://doi.org/10.3389/fnbot.2022.904017): wahadło o 1 stawie, symulacja, wynik opisowy (gładszy ruch niż PID) | REPORTED (abstract; Juarez-Lora full text) |
| Gradient zastępczy / BPTT | uczenie „wsteczne” mimo skokowych impulsów | [Neftci, Mostafa, Zenke 2019](https://arxiv.org/abs/1901.09948) (metadane); Huebotter 2025 (pkt 2.5) | VERIFIED (istnienie) / REPORTED |
| e-prop | przybliżenie BPTT działające w trakcie pracy | [Bellec et al. 2020](https://doi.org/10.1038/s41467-020-17236-y): zbliża się do wyników BPTT | REPORTED (abstract) |
| Konwersja ANN → SNN | zwykła sieć przepisana na impulsy | [Rueckauer et al. 2017](https://doi.org/10.3389/fnins.2017.00682): ponad 2× mniej operacji za kilka punktów procentowych błędu; klasyfikacja obrazów, nie sterowanie | REPORTED (abstract) |
| Ewolucja / optymalizacja bayesowska | szukanie parametrów metodą prób | [Salt et al. 2019](https://arxiv.org/abs/1910.07960): parametry LGMD dobierane metodami DE, SADE i BO, bo sprzęt analogowy szumi; nagrania DVS z drona | REPORTED (abstract) |
| Głębokie RL z aktorem impulsowym | uczenie przez nagrodę w symulatorze | PopSAN (pkt 2.5); [Jaisankar et al. 2025](https://arxiv.org/abs/2510.10516) (inna grupa): Franka w Isaac Gym, „do 96,10%” oszczędności energii; [arXiv 2508.12038](https://arxiv.org/abs/2508.12038): ramię 9-DOF, PPO, energia z modelu obliczeniowego | REPORTED (abstract) |
| Przeszukiwanie parametrów | strojenie zamiast uczenia wag | [Supic & Stewart 2022](https://arxiv.org/abs/2210.01243): 15% szybsze uczenie w scenariuszach z 6 lub 9 losowymi celami | REPORTED (abstract) |

**INFERRED (ok. 10 prac, głównie abstrakty).** Wśród przeczytanych prac jedyne wyniki liczbowe dla ramienia wielostawowego (Franka) ze SNN uczoną od początku do końca (Huebotter 2025, Jaisankar 2025) pochodzą z uczenia gradientowego lub RL w symulacji. PopSAN uczono 1 mln kroków; liczby kroków dla Huebottera i Jaisankara nie podaję (NOT VERIFIED). Projektowane lub NEF-owe kontrolery wielostawowe istnieją (Zaidel 2021, DeWolf 2016/2020, Polykretis 2022), ale mają opisowe wyniki i brak zewnętrznego punktu odniesienia. Nasza sieć z konektomu należy do rodziny „okablowanie biologiczne, bez uczenia wag”. Najbliżsi krewni (NEF, modele LGMD) mają albo wagi skompilowane z wzoru, albo strojone parametry.

### 2.5 Kto to robi i jak uczciwie mierzy

| System (grupa) | Co zaprojektowano / wyuczono | Próby i ziarna | Punkt odniesienia | Sym./real | Etykieta |
|---|---|---|---|---|---|
| [Zaidel et al. 2021](https://doi.org/10.3389/fnbot.2021.631159) (Ezra Tsur) | struktura NEF i PID zaprojektowane; IK adaptowana regułą PES | 10 000 punktów mapy osiągalności (bez ruchu), 2 losowe punkty z ruchem; bez powtórzeń i ziaren | brak zewnętrznego | pokazany ruch pochodzi z MuJoCo. Autorzy deklarują fizyczne ramię 6-DOF, ale nie podają liczb z ruchu fizycznego. „1 mm” to kryterium osiągalności / specyfikacja ramienia, nie zmierzona dokładność. | REPORTED (full text) |
| [DeWolf et al. 2016](https://doi.org/10.1098/rspb.2016.2134) | model kory ruchowej i móżdżku | ramię 3-członowe; zgodność z danymi z 19 badań | dane z literatury | symulacja (INFERRED) | REPORTED (abstract) |
| [Polykretis, Supic, Danielescu 2022](https://arxiv.org/abs/2209.02787) | kontroler stawu inspirowany biologią | brak w abstrakcie | nieokreślony | wg abstraktu prawdziwe ramiona | REPORTED (abstract): 19% mniejsze szarpnięcie (jerk) |
| [Tang et al. 2020, PopSAN](https://arxiv.org/abs/2010.09635) ([PMLR](https://proceedings.mlr.press/v155/tang21a.html)) | aktor impulsowy uczony RL (DDPG/TD3/SAC/PPO), krytyk ANN | 10 ziaren na algorytm, 1 mln kroków | PopSAN na Loihi vs ten sam PopSAN na GPU: HalfCheetah 10505 vs 10729, Hopper 3289 vs 3599, Walker2d 4280 vs 4995, Ant 5220 vs 5416. To porównanie urządzeń, nie SNN vs ANN. | symulacja (OpenAI Gym) | REPORTED (full text, ar5iv, tab. 1) |
| [Huebotter et al. 2025](https://arxiv.org/abs/2509.05356) | SNN uczona gradientem zastępczym, sterowanie predykcyjne | symulowana Franka 6-DOF, 64 stałe pary start/cel; SNN 10 ziaren, baza bez impulsów 3 ziarna | rekurencyjna sieć bez impulsów; brak klasycznego sterownika | symulacja | REPORTED (HTML, tabele): sukces 0,986 vs 0,970; parametry 907 336 vs 12 709 919; różna liczba ziaren nie pozwala porównać przedziałów |
| [Steffen et al. 2026, ICONS](https://doi.org/10.1145/3822454.3822466) ([arXiv 2606.11034](https://arxiv.org/abs/2606.11034)) | NEF/SPA; jądra podstawy wybierają między ręką a chodem | brak w abstrakcie | — | symulowany humanoid (Nengo + Isaac Sim) | REPORTED (abstract) |
| [Linares-Barranco et al. 2024](https://arxiv.org/abs/2405.12849) | rekurencyjna SNN uczona online na układzie ReckOn (FPGA) | brak w abstrakcie | — | sprawdzona na sterowaniu ramieniem | REPORTED (abstract) |
| [Stagsted et al. 2020](https://roboticsproceedings.org/rss16/p074.html) | PID z neuronów na Loihi | brak w abstrakcie | — | dron ograniczony do 1 DOF | REPORTED (abstract) |
| [Fu et al. 2021](https://doi.org/10.3389/frobt.2021.529872) | dwa modele LGMD jako jedyny czujnik kolizji | brak liczb w abstrakcie | — | prawdziwe mikroroboty, arena z ekranem LCD jako podłogą | REPORTED (abstract) |
| Spaun ([Eliasmith et al. 2012](https://doi.org/10.1126/science.1225266)) | w pełni zaprojektowany „mózg” NEF/Nengo z ok. 2,5 mln neuronów; moduły odpowiadające strukturom mózgu; 8 zadań | brak danych w notatce | — | symulacja; wyjście to ruch fizycznie modelowanego ramienia | REPORTED (secondary: wcześniejsza notatka `laczenie_modyfikacje.md`); metadane VERIFIED (Crossref: Science, 2012). Kanoniczny przykład projektowanych neuronów sterujących ramieniem, najbliższy opublikowany odpowiednik wariantu HD (pkt 6). |

**INFERRED.** Często powtarza się ten sam wzór: brak zewnętrznego punktu odniesienia, mało powtórzeń, wyniki opisowe. W ok. 10 przeczytanych pracach (głównie abstraktach) żadna nie używa konektomu. To nie jest przegląd systematyczny.

### 2.6 „Bez treningu” zwykle znaczy „bez uczenia wag”, nie „bez strojenia”

- **Przegląd LGMD.** Qin, Peng, Yue i Fu (2025) podają jako jedyny jawny wskaźnik sukcesu w przeczytanej części 95,3% dla modelu LGMD2 na robocie Colias w testach na arenie (przypisany Fu i in. 2016). Fu jest też współautorem przeglądu, więc to nie jest niezależne potwierdzenie. Poza tym w przeglądzie są głównie pokazy opisowe, brak standardowego benchmarku, a modele radzą sobie gorzej w złożonych, zaszumionych scenach. REPORTED (read: HTML preprintu, ok. 100 z 128 tys. znaków) ([J. R. Soc. Interface 2025](https://doi.org/10.1098/rsif.2025.0433); preprint [arXiv 2501.02982](https://arxiv.org/abs/2501.02982); to ta sama praca). Rozmiarów aren nie znaleziono w tekście.
- **Gao, Liu, Wang, Fu 2024.** Zoptymalizowany model LGMD na mikrorobocie osiągnął „najwyższy wskaźnik” omijania: 97,51%. Liczba prób, punkt odniesienia i zestaw strojenia są nieznane. REPORTED (read: abstract przez API DOAJ) ([Biomimetics 2024](https://doi.org/10.3390/biomimetics9110650)).
- **INFERRED.** Jeśli progi, wzmocnienia i stałe czasowe stroi się, aż pokaz działa, to zestaw strojenia jest zarazem zestawem testowym. Odruchy na zbliżanie są z budowy zlateralizowane (przeszkoda z lewej, skręt w prawo), więc trywialny przekaźnik rozwiązuje dużą część zadania. Tak samo jest u nas: przekaźnik daje 20/20 (pkt 8).

### 2.7 Argument energetyczny nas nie dotyczy

- **PopSAN.** Na Loihi zużywa 140× mniej energii na decyzję niż na Jetson TX2 (11,98 µJ vs 1670,94 µJ). Liczono jednak tylko moc dynamiczną: moc spoczynkową płytki Loihi (1,084 W wobec 0,003 W dynamicznej) pominięto. Loihi był też wolniejszy: 226 decyzji/s wobec 438–7450 na innych urządzeniach. REPORTED (full text, tab. 2); arytmetyka INFERRED ([arXiv 2010.09635](https://arxiv.org/abs/2010.09635)).
- **Davidson i Furber.** Przy tej samej technologii krzemu większość SNN z kodowaniem częstością nie jest wydajniejsza od zwykłych sieci. REPORTED (abstract) ([Davidson & Furber 2021](https://doi.org/10.3389/fnins.2021.651141)).
- **Yan i in.** W ich modelu analitycznym SNN wygrywa z kwantyzowaną siecią tylko przy średniej aktywności poniżej 5,7% (przy T = 5). REPORTED (abstract) ([arXiv 2409.08290](https://arxiv.org/abs/2409.08290)).
- **INFERRED.** FlyMind liczy gęstą symulację na CPU, więc zdanie „energooszczędne” nie miałoby pokrycia.

---

## 3. Temat 2: połączenie z siecią muchy jest możliwe, ale w przeczytanych pracach nikt nie pokazał, że decyduje mucha

### 3.1 Kto już łączy dane z konektomu z częścią projektowaną albo uczoną

| Układ | Co jest z danych | Co zaprojektowane / uczone | Łącze | Czy pokazano, że dane mają znaczenie | Etykieta |
|---|---|---|---|---|---|
| Eon Systems, „embodied brain emulation” ([strona](https://eon.systems/updates/embodied-brain-emulation)) | LIF całego mózgu z FlyWire: ok. 140 000 neuronów i 50 mln synaps wg strony; [The Register](https://www.theregister.com/a/5224139) podaje 125 000 i Brian2 | czujniki ręczne (wirtualny smak, „kurz”); aktywność sieci Lappalainena wstrzykiwana do neuronów (firma nazywa ją „decorative”); chód z gotowych kontrolerów NeuroMechFly uczonych imitacją; bez VNC | kilka DN jako uchwyty (DNa01/DNa02 skręt, oDN1 prędkość, MN9 karmienie, DN czułkowe czyszczenie); mapowanie wybrane ręcznie; synchronizacja co 15 ms; ciało z 87 stawami | Na stronie nie ma słowa „ablat” (PARTIALLY VERIFIED brak ablacji). Firma sama zastrzega, że to nie dowód, że sama struktura wystarcza. | REPORTED (read: full page) |
| NeuroMechFly v2 ([Wang-Chen et al. 2024](https://doi.org/10.1038/s41592-024-02497-y)) | sieć wzrokowa ograniczona konektomem w jednym pokazie (podążanie za inną muchą) | sterowniki inspirowane biologią, RL | — | brak w abstrakcie | REPORTED (abstract) |
| flybody ([Vaxenburg et al. 2025](https://doi.org/10.1038/s41586-025-09029-4)) | brak konektomu | sterowniki uczone RL, hierarchia | polecenia sterowania wysokiego poziomu | nie dotyczy | REPORTED (abstract) |
| [Lappalainen et al. 2024](https://doi.org/10.1038/s41586-024-07939-3) | połączenia 64 typów komórek płata wzrokowego | nieznane parametry neuronów i synaps dopasowane głębokim uczeniem do wykrywania ruchu | — | Zgodność z pomiarami z 26 badań. Wg autorów łączność plus dopasowane parametry wystarczają do przewidzenia aktywności, zwłaszcza przy rzadkich połączeniach. | REPORTED (abstract) |
| [Cowley et al. 2024](https://doi.org/10.1038/s41586-024-07451-8) | jednostki modelu przypisane 1:1 do typów neuronów projekcyjnych | głęboka sieć uczona przez „knockout training” na skutkach wyciszania ponad 12 typów | — | Wniosek autorów: kod populacyjny, a nie „jeden kanał = jedno zachowanie” | REPORTED (abstract) |
| [Shiu et al. 2024](https://doi.org/10.1038/s41586-024-07763-9) | LIF całego mózgu (FlyWire, ponad 125 000 neuronów, 50 mln synaps); znak synapsy z przewidzianego neuroprzekaźnika | jeden wolny parametr W_syn | pobudzanie wybranych neuronów (otwarta pętla) | **Tak, przy słabszym tasowaniu, w jednym zadaniu.** Przy przetasowanych wagach neuron ruchowy MN9 włączył się w 1 na 100 symulacji, przy prawdziwych w 100% (Suppl. Table 1d). Tasowanie zachowało tylko globalny rozkład wag, nie siłę wejścia/wyjścia każdego neuronu (jak nasze 3/40, nie jak `equal_weight` 10/10); miara to aktywacja MN po sztucznym pobudzeniu w otwartej pętli. Nie przenosi się to na naszą sieć (INFERRED). Autorzy wymieniają braki: brak synaps elektrycznych, neuronów bez impulsów, stanu wewnętrznego i neuropeptydów; zerowa aktywność spoczynkowa. | REPORTED (read: full text PMC11446845) |
| Pugliese et al. ([bioRxiv 2025](https://doi.org/10.1101/2025.09.12.675944); [Nature 2026](https://doi.org/10.1038/s41586-026-11195-y), tylko metadane) | symulacje VNC z 4 zbiorów danych | brak warstwy projektowanej | — | Przycinanie zostawiło obwód 3 neuronów (1 hamujący + 2 pobudzające), konieczny i wystarczający dla rytmu we wszystkich 6 nogach. DNg100 najsilniej wywołuje rytm. Przewidywanie dla DNb08 potwierdzono optogenetyką. R. Berg (The Transmitter) zauważa brak wzajemnego hamowania. | REPORTED (abstract; [press](https://www.thetransmitter.org/systems-neuroscience/long-sought-walking-circuit-found-in-fruit-flies/)) |
| FlyGM ([Jin, Zhu, Zhang, Sui, arXiv 2602.17997](https://arxiv.org/abs/2602.17997)) | graf FlyWire jako sieć przekazująca sygnały; wagi ze znakiem z liczby synaps | uczony imitacją ekspertów z flybody, potem PPO | — | **Tak.** Porównano z grafem przetasowanym z zachowaniem stopni, grafem losowym Erdősa–Rényiego i MLP przy identycznym uczeniu. Graf muchy wypadł lepiej jako szkielet uczonej polityki (chód, skręt, lot). | REPORTED (read: full text HTML) |
| „Digital sphinx” ([Brunton, Abe, Hu, Tuthill 2026](https://doi.org/10.64898/2026.03.20.713233), preprint) | konektom robaka C. elegans | sieć ANN uczona głębokim RL zamienia neurony ruchowe robaka na napęd nóg muchy | uczony dekoder | To pokaz-przestroga, nie test z kontrolą. Chód „bardzo realistyczny”, a biologicznie bez znaczenia. | REPORTED (read: abstract przez API bioRxiv) |
| FPGAFly ([Ye, arXiv 2610.38118](https://arxiv.org/abs/2610.38118)) | **MaleCNS**: 166,7 tys. neuronów, 25,6 mln połączeń, LIF na jednym FPGA | — | — | bez robota i bez zachowania; okno 100 ms liczone w 86,83 ms | REPORTED (abstract) |
| FlySoul ([GitHub](https://github.com/heyobi/flysoul)), DesktopFly ([GitHub](https://github.com/DenisSergeevitch/desktop-fly)) | MaleCNS (wg README) | — | — | projekty hobbystyczne, bez publikacji i kontroli | VERIFIED (istnienie: HTTP 200 + README) |

Dwa przykłady spoza muchy. Pierwszy to model pszczoły [Stone et al. 2017](https://doi.org/10.1016/j.cub.2017.08.052): obwód integracji drogi i sterowania, w którym neurony dla każdego kroku są tylko „zasugerowane” anatomicznie (REPORTED, abstract; robota w abstrakcie nie ma, więc to model bez ciała robota). Drugi to [AntBot](https://doi.org/10.1126/scirobotics.aau0307): algorytm inspirowany mrówką na robocie 6-nożnym, błąd powrotu „nawet 0,67%” w najlepszych warunkach światła (REPORTED, abstract). To nie jest obwód z konektomu; jak zrobiono chód, w abstrakcie nie ma (NOT VERIFIED). W AntBot model nawigacji wyznacza kierunek, a pozostała część robota go wykonuje (INFERRED). To podobny podział, co w FlyMind.

### 3.2 Pięć technik łączenia

1. **Zamrozić połączenia z danych, uczyć tylko pozostałe parametry** (Lappalainen).
2. **Przywiązać projektowane jednostki do prawdziwych komórek** danymi z wyciszeń (Cowley).
3. **Wąskie, ręcznie wybrane łącze na poziomie neuronów zstępujących** (Eon, REPORTED ze strony firmy; czy tak działa NeuroMechFly v2: NOT VERIFIED, pełnego tekstu nie czytano). Dokładnie tak działa nasz odczyt DNa02 lewy − prawy.
4. **Uczony dekoder z neuronów ruchowych do ciała** („digital sphinx”). To najbardziej ryzykowna technika.
5. **Graf konektomu jako szkielet uczonej polityki, z kontrolą przez przetasowanie grafu** (FlyGM).

**INFERRED.** Techniki 1, 2 i 5 wymagają uczenia, więc w świetle zasady z 3 XI to osobna decyzja (DH4). Technikę 3 już stosujemy. Techniki 4 odradzam.

### 3.3 Ostrzeżenie: łącze potrafi zrobić całą robotę

- **„Digital sphinx”.** Autorzy piszą wprost: „behavioral fidelity is achievable without biological fidelity” (wierne zachowanie nie wymaga wiernej biologii). Zalecają, by części i łącza miały podstawę w biologii. REPORTED (read: abstract).
- **The Transmitter, 2 IV 2026 (N. Mesa).**
  - Turaga: dowolna losowa sieć podpięta w ten sposób do ciała NeuroMechFly mogłaby dać chodzącą muchę.
  - Cowley: zaproponował sprawdzić, czy losowo połączony konektom da te same zachowania.
  - Philip Shiu (szef inżynierii Eon; tożsamość z pierwszym autorem Shiu 2024: INFERRED z nazwiska) przyznał, że to nie jest pełna kopia muchy.

  REPORTED (secondary; wypowiedzi w artykule prasowym) ([artykuł](https://www.thetransmitter.org/systems-neuroscience/digital-sphinx-raises-questions-about-connectome-models/)).
- **S. Furber w The Register.** Ocenił pracę Eon jako imponującą, ale nazwał jej mózg „machine learning, clamped into the shape of a fly connectome”. Zarzucił też, że wejścia to proste pobudzenia, a nie wirtualne dane zmysłowe. REPORTED (read: page).
- **Carboncopies Foundation** (organizacja popierająca emulację mózgu; wpis bez autora). Opisuje „efekt kukiełki”: konektom działa jako przełącznik wbudowanych procedur ciała. Ostrzega też, że w prostym środowisku może istnieć tylko jedna poprawna akcja na krok. Część tez jest postawiona hipotetycznie, bez danych. REPORTED (advocacy) ([wpis](https://carboncopies.org/Blog/Posts/FruitFlyNotUploaded/Post/)).
- **INFERRED.** Drugi zarzut Furbera (proste pobudzenia zamiast zmysłów) trafia wprost w nasz enkoder koloru, który 12 XI uznałeś za sztuczne pobudzanie.

### 3.4 Dopasowanie do SO-101: część już istnieje

**Stan dziś.** W głównych przebiegach sieć decyduje tylko o obrocie podstawy (DNa02 lewy − prawy) i o sile chwytaka (obwód dotyku nogi T2L, FJ1). Resztę robi kod klasyczny (IK, skrypty).

Jak często polecenia pochodzą z sieci (REPORTED, `flymind/reports/bio_advantage_research_20261110.md` w. 98; tam przeliczone, tu niepowtarzane):

| Seria | Szczęka (chwytak) | Podstawa |
|---|---|---|
| demo v3 | 8,8% tików | 16,0% tików |
| ramię „E” benchmarku z 10 XI (nie decyzja E1–E3) | 12,6% tików | 6,2% tików |

Łącznie to 3–4% wszystkich poleceń stawów.

**FJ2 to już hybryda typu HE** (klasyfikacja INFERRED; projekt w `flymind/experiments/fj2_fly_arm/DESIGN.md` z 3 XI, REPORTED, plik lokalny). Mapowanie v1 ustalono przed pilotami:

| Staw | Agonista (+) | Antagonista (−) |
|---|---|---|
| shoulder_pan | DNa02 lewy − prawy | — |
| shoulder_lift | Pleural remotor/abductor MN | Sternal anterior rotator MN |
| elbow_flex | Tr flexor | Tr extensor |
| wrist_flex | stały | — |
| wrist_roll | stały | — |
| gripper | Ti extensor | Ti flexor + Acc. ti flexor |

- **Prawo sterowania:** prędkość stawu = k_j·(r_agonista − r_antagonista). Wzmocnienie k_j jest wspólne dla stawów 1–3 (DESIGN.md), wygładzanie 50 ms; J0 = 0,275 (nie 0,2 jak w FJ1). Pilot 2 badał jednak odwrócenia znaków s1, s2 ∈ {+1, −1} i Glu ±1 na tych samych odległościach, więc „ustalone z góry” dotyczy tylko v1 (REPORTED, `PILOT_NOTES.md`).
- **Wejście:** obraz → `encoder.py` → LC9. INFERRED: to ten sam rodzaj wejścia co enkoder koloru dla LC10a, więc podlega ocenie z 12 XI.
- **Wyniki pilotów** (bez ziaren, szum 0, to nie są wyniki testu; REPORTED, `PILOT_NOTES.md`):
  - przy Glu −1 i piłeczce w 0,30 m punkt chwytu zbliżył się z 71 do 17 mm, w 0,34 m z 94 do 80 mm;
  - przy Glu +1 wyniki były niespójne;
  - nie znaleziono naturalnego sygnału „podnieś po chwycie”; red team wycofał kandydata T2L → T2R;
  - chwytak wciskał się w stół z siłą 29–44 N, bo `safety.py` nie pilnuje stołu.

**Co dane dają na każdy staw SO-101.** Liczby to VERIFIED (pkt 4.2), przypisanie to HYPOTHESIS:

| Staw SO-101 | Kandydat w MaleCNS | Kłopot | Status |
|---|---|---|---|
| 0 podstawa | DNa02 (2 ciała, ACh); ewentualnie DNa01 (2 ciała) | DNa02 sam słabo wywołuje skręt, a bez głowy efekt znika ([Braun 2024](https://doi.org/10.1038/s41586-024-07523-9)). Nasz wynik mierzy lateralizację. | używany dziś (ENGINEERING) |
| 1 bark | pule biodra T2L, łącznie 11 MN z nazwą: Pleural remotor/abductor 3, Sternal anterior rotator 2, Sternal posterior rotator 4, Sternal adductor 1, Tergotr. 1 | Znaczenie „podpór/wymach” pochodzi z literatury. Przypisanie do „podnieś ramię” jest arbitralne. | HYPOTHESIS (FJ2 v1) |
| 2 łokieć | Tr flexor 7, Tr extensor 2 (oraz Acc. tr flexor 2, Sternotrochanter 2, Fe reductor 3) | „Tr flexor = unoszenie” NIEZWERYFIKOWANE | HYPOTHESIS |
| 3 zgięcie nadgarstka | Ti flexor 5 + Acc. ti flexor 6 vs Ti extensor 2 | te same pule już służą chwytakowi (konflikt); alternatywą byłyby MN szyi (pkt 4.2) | HYPOTHESIS |
| 4 obrót nadgarstka | brak takiego stawu u muchy; najbliżej obrót głowy przez MN szyi | brak odpowiednika | brak analogii |
| 5 chwytak | dziś obwód dotyku T2L (FJ1); MN stopy z nazwy tylko w T1L (Ta depressor 5, Ta levator 2), w T2 zero; trąbka (PhN 40, MxLbN 26) jako luźna analogia | stopa w T2 nienazwana w danych | HYPOTHESIS |

**INFERRED.**
- Dane dają nazwane pule neuronów ruchowych dla 3–4 stawów, ale przypisanie do stawów SO-101 zawsze będzie naszym wyborem projektowym.
- Obrót nadgarstka nie ma odpowiednika biologicznego.
- W przyszłym wariancie HE najwyżej 4 stawy byłyby sterowane przez muchę, a 2 stałe (HYPOTHESIS). Dziś w głównych przebiegach: tylko podstawa i siła chwytu; stawy 1–2 jedynie w pilocie FJ2 bez ziaren.
- Nie znalazłem opublikowanego przeniesienia nogi muchy na ramię robota. Prace o przenoszeniu ruchu między ciałami ([STMR, arXiv 2404.11557](https://arxiv.org/abs/2404.11557), [Human2Humanoid, arXiv 2606.03476](https://arxiv.org/abs/2606.03476); VERIFIED tylko tytuły) dotyczą kinematyki i uczenia, nie obwodów muchy.

### 3.5 Co już wiemy z raportów 3–12 XI

Z wcześniejszej notatki `research_notes/Hybrydowe mózgi z konektomów/laczenie_modyfikacje.md` (przeczytane fragmenty; treść REPORTED za tą notatką, istnienie źródeł VERIFIED przez Crossref/arXiv 13 XI):
- **Spaun** (Eliasmith 2012) dopisany do tabeli w pkt 2.5 jako kanoniczny przykład wariantu HD.
- **Neurorobotics Platform (EBRAINS)**: jawne „funkcje transferu” neuron → robot i robot → neuron; gotowy precedens dla tłumacza KT (pkt 5).
- **Tasowania „null” bywają mylące** (Dhiman 2026, Therianos 2026; preprinty): dopisane do pkt 8.
- **Taksonomia 5 klas z 3 XI → warianty HA–HE (INFERRED):** HD = klasa 2 lub 4 (model zaprojektowany albo sztuczny, bez danych muchy); HC = klasa 3 (zmodyfikowany konektom: wstawki zamieniają DATA w MODEL); HE = klasa 1 dla części muchy + cienka mapa inżynierska; HA i HB = klasa 1 (mucha) połączona z klasą 2/4 (część projektowana). Takiej hybrydy taksonomia nie ma wprost (klasa 5 dotyczy modułów różnych gatunków).

---

## 4. Temat 3: mózg wybiera, VNC wykonuje, a anatomia naszych danych jest z tym zgodna (to liczby synaps, nie dowód funkcji; INFERRED)

### 4.1 Co mówi biologia

| Fakt | Etykieta | Źródło |
|---|---|---|
| **Wąskie gardło.** Z mózgu do VNC biegnie ok. 350 DN na stronę. Namiki 2018 opisał 190 par DN w co najmniej 98 typach, czyli ok. połowę wszystkich. | REPORTED (full text) | [Namiki et al. 2018](https://doi.org/10.7554/eLife.34272) |
| **MANC (VNC samca):** 1 328 DN, 1 862 AN, 733 MN, ok. 23 500 neuronów, w tym 13 066 interneuronów. | REPORTED (full text) | [Cheong et al. 2026](https://doi.org/10.7554/eLife.96084) |
| **Trzy zbiory EM:** 1 315–1 347 DN i 1 733–1 865 AN; 51% typów DN dopasowano do linii genetycznych. | REPORTED (full text) | [Stürner et al. 2025](https://doi.org/10.1038/s41586-025-08925-z) |
| **Bezpośrednie połączenia DN → MN są słabe, choć częste.** DN dają średnio 7% wejścia neuronów ruchowych (liczone grupami). Ok. 80% grup MN ma jednak co najmniej 1% bezpośredniego wejścia od jakiejś grupy DN. Tylko 13 z 92 grup DN dolnego tectulum daje ≥1% wejścia któremukolwiek MN. Start do lotu koordynują „węzły” wewnątrz VNC. | REPORTED (full text) | [Cheong et al. 2026](https://doi.org/10.7554/eLife.96084) |
| **Neurony „rozkazowe” działają populacją.** DN pobudzają inne DN; 73% synaps DN–DN w mózgu leży w zwoju podprzełykowym (GNG). U much bez głowy znika skręt wywoływany przez DNa01 i DNa02 oraz cofanie przez DNp42. DNa02 łączy się wprost z 18 innymi DN i sam słabo wywołuje skręt. „Samodzielne” DN (oviDN, DNg11, Mute, DNg14) działają też bez głowy. | REPORTED (full text) | [Braun et al. 2024](https://doi.org/10.1038/s41586-024-07523-9) |
| **DNa02 a DNa01.** DNa02 przewiduje szybki skręt o dużym wzmocnieniu, DNa01 trwały skręt o małym wzmocnieniu. | REPORTED (full text) | [Rayshubskiy et al. 2025](https://doi.org/10.7554/eLife.102230) |
| **Inne DN.** DNp09 (P9) wywołuje chód do przodu ze skrętem w tę samą stronę i jest potrzebny samcowi w pościgu. MDN wywołuje chód do tyłu. | REPORTED (abstract) | [Bidaye 2020](https://doi.org/10.1016/j.neuron.2020.07.032); [Bidaye 2014](https://doi.org/10.1126/science.1249964) |
| **Rola VNC.** Generatory rytmu plus sprzężenie z nóg; sygnały zstępujące tylko je modyfikują. Większość danych pochodzi od większych owadów, dowód dla samej Drosophila jest cieńszy. | REPORTED (abstract) | [Bidaye, Bockemühl, Büschges 2018](https://doi.org/10.1152/jn.00658.2017); [Tuthill & Wilson 2016](https://doi.org/10.1016/j.cub.2016.06.070) |
| **Noga.** 14 mięśni i 53 MN (liczba cytowana za wcześniejszymi pracami). Duże, szybkie MN dają siłę, małe i wolne postawę. Różnią się jednak też sprzężeniem proprioceptywnym, więc nie działa tu tylko zasada wielkości. | REPORTED (full text) | [Azevedo et al. 2020](https://doi.org/10.7554/eLife.56754) |
| **Rekrutacja.** W modułach nóg waga każdego neuronu przedruchowego jest proporcjonalna do wielkości docelowego MN (rekrutacja hierarchiczna); w skrzydle tak nie jest. Atlas MN nóg i skrzydeł z VNC samicy (FANC). | REPORTED (abstract) | [Lesser 2024](https://doi.org/10.1038/s41586-024-07600-z); [Azevedo 2024](https://doi.org/10.1038/s41586-024-07389-x) |
| **Propriocepcja.** Neurony czuciowe stawu goleni kodują pozycję, kierunek ruchu i drgania. | REPORTED (abstract) | [Mamiya et al. 2018](https://doi.org/10.1016/j.neuron.2018.09.009) |
| **Ruchy celowane.** Czyszczenie miejsca dotyku na głowie idzie przez somatotopowe drogi mózgu. Przy przejściu nad szczeliną mucha ocenia jej szerokość wzrokiem, ale obwodu nie wskazano. Nie ma znanego obwodu „sięgnij do celu w przestrzeni 3-D”. | REPORTED (abstract) + INFERRED | [Calle-Schuler 2026](https://doi.org/10.7554/eLife.108044); [Pick & Strauss 2005](https://doi.org/10.1016/j.cub.2005.07.022) |
| **Droga zwrotna do mózgu.** Neurony wstępujące (AN) przekazują stan zachowania. Komórki HS niosą sygnał chodu niezależny od wzroku, podobny do kopii eferentnej. | REPORTED (abstract) | [Chen et al. 2023](https://doi.org/10.1038/s41593-023-01281-z); [Fujiwara et al. 2017](https://doi.org/10.1038/nn.4435) |

### 4.2 Co jest w naszych lokalnych danych MaleCNS (VERIFIED, zapytania tylko do odczytu)

**Dane:** katalog `/Users/admin/so101_fly_project/data/malecns/`:
- `body-annotations-male-cns-v1.0-minconf-0.5.feather` (211 577 wierszy);
- `body-neurotransmitters-male-cns-v1.0.feather` (1 835 518 wierszy);
- `connectome-weights-male-cns-v1.0-minconf-0.5.feather` (151 856 684 wiersze).

„Waga” to liczba synaps na parę neuronów (opis schematu REPORTED w `research_notes/Konektom muchy dla SO101/malecns_data_access.md`). Próg t oznacza, że para musi mieć co najmniej t synaps.

**Komendy:**
```
SCR=/private/tmp/claude-501/-Users-admin--claude-spares-spare-72aeAc/18088efc-118a-40f7-a6fd-25f3036bed30/scratchpad/malecns_queries
PY="/Users/admin/so101_fly_project/.venv/bin/python -I -B"
cd $SCR
$PY q1_annotations.py > q1_annotations.out      # superklasy, DN, AN, MN
$PY q2_legmn.py > q2_legmn.out; $PY q3_jointgroups.py > q3_jointgroups.out   # MN nóg
$PY q4_scan.py > q4_scan.out; $PY q4_report.py > q4_report.out               # wyjście DN, wejście MN (próg 1)
$PY q6_scan_thr.py 5 > q6_scan_thr5.out; $PY q6_report.py 5 > q6_report_thr5.out   # to samo przy progu 5
$PY q5_dn_types.py > q5_dn_types.out            # DNa02, DNa01, DNp09
$PY q7_hops_nt_an.py > q7_hops_nt_an.out        # skoki, neuroprzekaźniki, AN
$PY q8_nonleg_search.py > q8_nonleg_search.out; $PY q9_synonyms.py > q9_synonyms.out
```

Niezależne powtórzenie (`malecns_verify/v1.py`, `v2.py`, `v3.py`) odtworzyło wszystkie liczby nagłówkowe. Poprawki weryfikatora uwzględniłem niżej.

**(a) Podział na mózg, VNC i ruch jest wprost w adnotacjach.**

| Superklasa | Liczba |
|---|---|
| descending_neuron (DN) | 1 314 (L 656 / P 648 / środek 10), 480 typów |
| ascending_neuron (AN) | 1 846, 567 typów |
| vnc_intrinsic (interneurony VNC) | 13 161 |
| vnc_motor | 708; w tym nogi: 319 (T1 81, T2 116, T3 122; T2: 58 + 58) |
| cb_motor (MN po stronie mózgu) | 107 |
| bez superklasy | 44 877 |

Dziewięć ciał DN ma notatkę „does not reach the VNC”, więc mogą nie być DN.

**(b) MN nóg z nazwami mięśni.**
- **T2L, 58 MN:** Tr flexor 7, Ti flexor 5, Acc. ti flexor 6, Ti extensor 2, Tr extensor 2, Acc. tr flexor 2, Fe reductor 3, Sternotrochanter 2, Pleural remotor/abductor 3, Sternal adductor 1, Sternal anterior rotator 2, Sternal posterior rotator 4, Tergotr. 1, ltm 3, ltm1-tibia 1, ltm2-femur 2, numerowane MNml 12. Żaden MN w T2 nie ma w nazwie stopy.
- **T1L, 41 MN:** m.in. Ta depressor 5, Ta levator 2 (stopa), Acc. ti flexor 10.
- **Grupy „stawowe”** dla T2L: biodro 11, krętarz/udo 16, udo/goleń 14, ltm 5, stopa 0, numerowane 12. To moja umowna reguła słów kluczowych, nie anatomia.

**(c) DN rzadko trafiają wprost w MN; MN nogi karmi VNC.**

| Miara | Wynik |
|---|---|
| Wyjście wszystkich DN, próg 1 (11 578 566 synaps) | 64,6% do fragmentów bez adnotacji, vnc_intrinsic 14,8%, cb_intrinsic 7,5%, DN 5,2%, AN 3,7%, **vnc_motor 2,0%** |
| To samo, tylko cele z adnotacją (4 102 860) | vnc_intrinsic 41,9%, **vnc_motor 5,6%** |
| To samo przy progu ≥5 (3 694 203) | vnc_intrinsic 38,4%, **vnc_motor 5,7%** |
| Wejście MN T2L, próg 1 (225 935 synaps) | **vnc_intrinsic 84,1%**, DN 6,4%, bez adnotacji 4,4%, AN 2,5%, vnc_sensory 2,3% |
| Wejście MN T2L, próg ≥5 (198 864 synapsy) | vnc_intrinsic 88,4%, DN 6,7%, AN 2,5%, vnc_sensory 2,1% |
| Wszystkie MN nóg (904 684 synapsy) | vnc_intrinsic 82,5%, DN 6,2% |

Udział „czuciowe → MN” (ok. 2%) liczy tylko vnc_sensory, więc jest dolną granicą.

**(d) Trzy DN ważne dla FlyMind.** Wszystkie mają po 2 ciała i wszystkie są cholinergiczne (ACh).

| DN | Ciała | Wyjście (synapsy) | Na MN nóg | Uwagi |
|---|---|---|---|---|
| DNa02 | 10360 i 523769 | 47 622 | 888 = **1,9%**; T2L: 161 synaps na 8 z 58 MN (od 1 z 2 ciał DNa02) | Największy nazwany cel ruchowy to Sternal anterior rotator MN (776 synaps). Na vnc_motor łącznie 1 501 (3,2%). |
| DNa01 | 2 | 40 323 | 426 | — |
| DNp09 | 2 | 39 234 | 18 | — |

Najwięcej synaps bezpośrednio na MN T2L (próg ≥5) dają DNg105 (1 707), DNge079 (1 320) i DNg93 (1 004). DNa02 nie ma w pierwszej ósemce.

**(e) Zasięg „w dwóch krokach” niczego nie wyróżnia** (próg ≥5):
- 87 DN (78 typów) łączy się z MN T2L wprost;
- 1 114 interneuronów VNC karmi te MN;
- 887 z 1 314 DN (67,5%) sięga MN T2L w najwyżej dwóch krokach;
- 49 z 58 MN T2L dostaje ≥5 synaps wprost od jakiegoś DN.

Reguła wymaga ≥t synaps na każdym odcinku, ale nie mierzy siły całej ścieżki. To górna granica wpływu, nie miara sterowania.

**(f) Znaki synaps (neuroprzekaźniki).**
- **DN** wg `consensus_nt`: ACh 931, GABA 241, Glu 104, niejasne 36, serotonina 2.
- **DN → MN T2L** (≥5; 13 364 synapsy): ACh 51,0%, **GABA 46,0%**, Glu 2,9%.
- **Interneurony VNC → MN T2L** (190 020 synaps): ACh 54,1%, GABA 26,7%, **Glu 19,0%** wagowo.
- Z 1 114 interneuronów (≥5): 626 ACh, 286 GABA, 196 Glu, 5 niejasnych, 1 histamina. Mediana pewności przewidywania 0,955.
- **INFERRED:** znak glutaminianu (Glu) dotyczy ok. 1/5 napędu przedruchowego, a dane go nie rozstrzygają.

**(g) Droga zwrotna z nogi T2L.**
- 196 AN ma ciało w T2L (168 typów); łącznie z AN, które dostają ≥5 synaps od czuciowych T2L, jest ich 415.
- Ich wyjście (≥5): ok. 30–33% do mózgu (cb_intrinsic), ok. 28–31% zostaje w VNC, 8–10% trafia do DN. Najczęstsze cele w mózgu to typy AVLP (wśród 196 AN z ciałem w T2L także GNG). Pięć głównych celów wśród DN (415 AN, ≥5): DNg108 2 452; DNge079 2 003; DNge122 2 003; DNg35 1 885; DNg100 1 885 synaps.
- Żaden z głównych celów nie należy do drogi LC10a.

**(h) W danych nie ma etykiet funkcji.** Szukanie w 9 kolumnach tekstowych 15 wzorców („groom”, „walk”, „steer”, „escape”, „feeding” i in.) dało 0 trafień. „reach” dało 9 trafień, wszystkie to notatka „does not reach the VNC”. Są tylko synonimy z literatury, np. MDN = „Carreira-Rosario 2018: DNp50”, DNg62 = „Hampel 2015: aDN1”, DNp01 = olbrzymie włókno. 199 z 1 314 DN ma synonim.

**Pułapki.**
- 44% końców krawędzi (133 806 112 z 303 713 368) to ciała spoza pliku adnotacji. Przyczyny pliki nie podają; prawdopodobnie to nieukończone fragmenty (INFERRED).
- Zawsze trzeba podać próg i mianownik.
- Pliki nie mają podziału na rejony mózgu (ROI), więc nie wiadomo, gdzie leży synapsa.

### 4.3 Co z tego wynika dla ramienia (INFERRED)

1. Biologia ma trzy piętra:
   - mózg wybiera cel i skręt populacją ok. 1 300 DN;
   - VNC zamienia to na wzorce ruchu;
   - pule MN rekrutują się według wielkości i korzystają ze sprzężenia zwrotnego.

   W FlyMind z piętra mózgu jest jeden odczyt (DNa02 L − R → podstawa); siła chwytu pochodzi z obwodu VNC nogi T2L (piętra 2–3, FJ1), więc pętla chwytu już dziś przypomina wariant HE. Resztę stawów obsługuje kod klasyczny, który robi więcej niż VNC, bo planuje geometrię sięgania.
2. Skoro 84–88% wejścia MN pochodzi z interneuronów VNC, w danych to VNC wykonuje (biologicznie) polecenie mózgu; to liczby synaps, nie dowód funkcji. VNC jest przy tym częścią muchy i sam też decyduje lokalnie (rytm, odruchy, DN działające bez głowy, pkt 4.1). W wariancie HE jest więc po stronie muchy, a jedynym zaprojektowanym tłumaczem zostaje stała mapa MN → staw. To biologiczne uzasadnienie wariantu HE.
3. Skoro 887 z 1 314 DN sięga nogi w dwóch krokach, sama osiągalność nie pozwala wybrać „właściwego” DN dla stawu. Potrzebna jest ścieżka ważona siłą i znakiem albo test perturbacyjny.
4. Droga zwrotna (AN) istnieje w danych. W FlyMind sieć chwytu dostaje propriocepcję chwytaka (kanały FeCO w `vision_leg.py`, `sensory_manipulation.py`, `vision_manipulation.py`; PARTIALLY VERIFIED przez grep weryfikatora). Nie widzieliśmy natomiast kopii stanu stawów ramienia podawanej do sieci (NOT IMPLEMENTED, sprawdzenie niepełne).
5. Wynik Braun 2024 (DNa02 bez głowy nie skręca) i nasz red team są **zgodne, ale niezależne**. Pierwszy mówi o biologii muchy, drugi o mocy naszego testu. Jeden nie potwierdza drugiego (poprawka weryfikacji).

---

## 5. Temat 4: zasada z 3 XI, czyli gdzie kończy się tłumaczenie, a zaczyna decydowanie

**Zasada (słowa Adama, 3 XI, z `FLYMIND_MASTER_CONTEXT.md`):** „najważniejsze jest to, żeby nie algorytm tym sterował, tylko mucha, nawet jeżeli stracimy na tym jakościowo”. Wejścia tylko przez naturalne zmysły. 12 XI Adam uznał enkoder koloru podający ten sam prąd wszystkim LC10a jednej strony za sztuczne pobudzanie.

**Główna myśl (INFERRED).** Zasadę łamie nie sama obecność zaprojektowanych neuronów, tylko to, co one robią. Nie znalazłem opublikowanej, przyjętej definicji granicy „tłumaczenie a decyzja” dla układów hybrydowych. Literatury o współsterowaniu w interfejsach mózg–maszyna nie przeszukano.

**Proponowane kryteria tłumacza KT1–KT8 oraz KT9 dla warstwy bezpieczeństwa (HYPOTHESIS, do zatwierdzenia przez Adama).** Zaprojektowany element D między wyjściami muchy a stawami jest tłumaczem tylko wtedy, gdy spełnia wszystkie KT1–KT8:

| Kryterium | Treść |
|---|---|
| **KT1 Zamrożony przed testem** | Parametry wynikają z reguły albo z jednej kalibracji na osobnym zbiorze. Są zapisane z sumą kontrolną; żadnego strojenia na scenach testowych. |
| **KT2 Bez pamięci** | Najwyżej stały filtr liniowy. Bez zatrzasków, bez „trzymania celu”, bez trybów. |
| **KT3 Monotoniczny w każdym wejściu, ze stałą listą wejść na staw** | Polecenie każdego stawu to rosnąca lub malejąca funkcja każdego ze wskazanych wyjść muchy. Lista wyjść dla każdego stawu jest spisana przed testem. Wolno używać stałych sum i różnic nazwanych wyjść (np. DNa02 L − R, pula agonistów − pula antagonistów). Bez tablic uczonych na danych zadania. |
| **KT4 Bez wyboru** | Brak argmax, „zwycięzca bierze wszystko” i if/else zależnego od stanu zadania. |
| **KT5 Bez bramkowania** | Brak wejść z czujników lub stanu zadania, które mnożą albo przełączają sygnał muchy. Wolno: stałe wzmocnienie, limit prędkości, bezpieczeństwo na warunkach KT9. |
| **KT6 Bez własnego stanu** | Brak liczników, zegarów i wag uczonych w trakcie pracy, które zmieniają to, *która* akcja zachodzi. |
| **KT7 Test ciszy** | Przy wyciszonej musze D sam nie przekracza poziomu przypadku P0 (ramię z poleceniem zerowym lub losowym na tych samych scenach i ziarnach). Próg liczbowy: KD1 w pkt 7. |
| **KT8 Rozliczenie informacji** | Wejścia D nie zawierają informacji o zadaniu (strona celu, moment chwytu). Cała ta informacja musi przejść przez muchę (KD11). |
| **KT9 Bezpieczeństwo tylko ogranicza** (dotyczy warstwy bezpieczeństwa, nie D) | Bezpieczeństwo może tylko przyciąć polecenie do zakresu albo je zatrzymać. Nigdy nie wybiera celu, kierunku ani ponownego startu. Każda interwencja jest zapisywana w każdym tiku. Próby, w których interwencja bezpieczeństwa zmieniła wynik (np. reset, recover albo halt z etapu pick-and-place), wyłącza się z liczenia „decyduje mucha”, a ich udział podaje się w KD7. |

Niespełnienie KT4–KT7 oznacza, że D **decyduje**. Warstwa bezpieczeństwa (zakresy stawów, prędkość, stół) jest dozwolona tylko na warunkach KT9. Bez KT9 bezpieczeństwo mogłoby po cichu rozstrzygać wynik, bo czyta stan zadania (stół, kontakt) (INFERRED).

**VNC z danych to część muchy (DATA), więc wolno mu decydować.** W wariancie HE kryteria KT1–KT8 dotyczą wyłącznie zaprojektowanej mapy MN → staw (INFERRED).

**Precedens (REPORTED, secondary: `laczenie_modyfikacje.md`).** Neurorobotics Platform (EBRAINS) łączy modele mózgu z ciałami robotów przez jawne „funkcje transferu”: częstość impulsów → polecenie ruchu i czujnik → prąd ([EBRAINS NRP](https://www.ebrains.eu/tools/nrp)). To gotowy wzór tłumacza nazwanego wprost jako inżynieria. Kryteria KT dodają do niego to, czego NRP nie wymaga: dowód, że tłumacz nie decyduje.

**Strona wejścia: kryteria KW1–KW3 (HYPOTHESIS, do zatwierdzenia przez Adama).** Każda hybryda ma dwa łącza: wejście (enkoder: zmysł → mucha) i wyjście (D: mucha → stawy). Zasadę trzeba sprawdzić na obu. Enkoder spełnia zasadę tylko wtedy, gdy spełnia wszystkie:

| Kryterium | Treść |
|---|---|
| **KW1 Tylko neurony czuciowe** | Wejście wchodzi wyłącznie do typów neuronów czuciowych: fotoreceptorów (każda kolumna oka osobno), mechano- i proprioreceptorów. Nigdy do neuronów projekcyjnych ani interneuronów (np. LC10a, LC9). |
| **KW2 Ta sama stała przemiana** | Dla każdej kolumny lub czujnika ta sama stała przemiana (bodziec → prąd), ustalona przed testem. |
| **KW3 Bez wiedzy o zadaniu** | Enkoder nie wykrywa obiektu, koloru ani celu; nie niesie informacji o zadaniu. |

Test: spis ścieżek kodu enkodera (odczyt kodu, bez uruchamiania). Enkoder koloru → LC10a łamie KW1 i KW3, co zgadza się z decyzją z 12 XI. `encoder.py` → LC9 w FJ2 łamie KW1. Wariant planu oka z 12 XI z prądem do neuronów blaszki L1–L3 zamiast do fotoreceptorów R1–R6 też łamałby KW1 (INFERRED).

**Klasyfikacja tego, co już mamy (INFERRED):**

| Element FlyMind / z raportów 12 XI | Ocena wg KT | Wniosek |
|---|---|---|
| Enkoder koloru → LC10a (V5) | łamie zasadę wejścia (decyzja z 12 XI) | sztuczne pobudzanie |
| Dekoder DNa02 L − R → prędkość podstawy | KT2–KT6 spełnione, jeśli wzmocnienie jest stałe; stałość w obecnym kodzie (demo v3 / V5 v4.x): **NOT VERIFIED** (do sprawdzenia odczytem kodu w KD7) | tłumaczenie. Ale w V5 v2 wzmocnienie kalibrowano osobno dla każdej sieci (nachylenie 495,6 dla danych vs 100,9–146,9 dla tasowań SHUF_STR 3001–3003; tasowania w obrębie strony, dev: 491–494; `results/audit_shared_decoder_20261029.txt`, REPORTED), co w porównaniach łamie KT1. |
| IK i skrypty dla barku, łokcia, nadgarstka | wybierają pozę i trajektorię | decydują; jawne rusztowanie |
| Mapa MN → staw w FJ2 | KT1–KT3 deklarowane w projekcie (HYPOTHESIS); k_j wspólne dla stawów 1–3; pilot badał odwrócenia znaków (s1, s2 ∈ {+1, −1}) i Glu ±1 na tych samych odległościach (0,30/0,34/0,38 m), więc test musi użyć nowych scen i ziaren; KT7 i KT8 niesprawdzone | kandydat na tłumacza |
| Tłumacz T1 z raportu 12 XI (polecenie → bodziec) | wybiera cel, więc łamie KT4 | decyduje „co”; mucha tylko „jak” |
| K1 (z projektu W3, 12 XI), mapa ważności | bramkuje czułość oka, więc łamie KT5 | granica (ocena Claude w raporcie 12 XI, `vla_with_fly_design_20261112.md` w. 357; decyzja Adama nadal otwarta) |
| W3 + K3 (tryby podawane do wybranych DN) | sztuczne pobudzanie | sprzeczne z zasadą |

**Gdzie kończy się tłumaczenie (INFERRED).** Na pierwszym elemencie, który ma dostęp do stanu zadania albo do alternatyw. Praktyczny test: zastąpić D jego zamrożonym odpowiednikiem liniowym (KD10). Jeśli sukces zmienia się o więcej niż z góry ustalony margines (np. 5 pp, parowy test McNemara na wspólnych ziarnach; progi w pkt 7), D liczył coś więcej niż tłumaczenie.

---

## 6. Warianty architektury HA–HE

| Wariant | Co decyduje | Co tłumaczy | Które stawy steruje mucha | Zgodność z zasadą 3 XI | Główne ryzyka | Kontrola, która by to wykazała |
|---|---|---|---|---|---|---|
| **Wariant HA**: warstwa zaprojektowana tłumaczy (mucha decyduje na poziomie DN, stała warstwa „rdzeniowa” z par pos/neg mapuje DN na 6 stawów) | mucha (DN), ale tylko tam, gdzie znamy sygnał | zaprojektowane neurony | realnie podstawa (DNa02) i chwytak (obwód dotyku). Dla barku, łokcia i nadgarstka nie ma rozpoznanego DN, więc warstwa musiałaby wymyślać polecenia. | **częściowo**: tak dla 1–2 stawów, jeśli spełnia KT1–KT8; na 6 stawach po cichu staje się HB albo HD | trywialny przekaźnik wystarcza; wybór DN „pod wynik” | KD1, KD4, KD7, KD10 |
| **HB**: zaprojektowana „kora” decyduje, mucha działa jak odruchy | część zaprojektowana | obwody muchy jako wykonawca | żaden w sensie decyzji | **nie**: wybór należy do części projektowanej. Tylko jako jawnie nazwane ramię porównawcze. | sukces przypisany musze | KD1 (kora sama robi zadanie), KD7 |
| **HC**: zaprojektowane neurony wstawione do obwodu muchy (przekaźniki, wzmocnienia) | niejasne, rozproszone | mieszanka | jak HA, ale bez wyraźnej granicy | **granica, zwykle nie**: przekaźnik ze stałym wzmocnieniem jest tłumaczeniem, ale wtedy dorównuje naszemu przekaźnikowi (mucha zbędna); uczone wzmocnienie, bramka lub hamowanie wybierające drogę to decyzja; „DATA” staje się „MODEL” | najtrudniejszy do audytu; degeneracja (różne mechanizmy, to samo zachowanie) | KD3 (tasowanie blokowe), KD5, KD6, KD12 |
| **HD**: całkowicie zaprojektowany lub uczony, bez muchy (układ z filmu może tu należeć, ale jego metoda jest nieznana; Spaun to przykład z literatury) | projektant / uczenie | — | 0 | **nie**: nie ma w nim muchy | pomylenie z hybrydą | sam służy jako ramię porównawcze w KD5 |
| **HE**: prawdziwy VNC z danych jako wykonawca (DN → interneurony VNC z MaleCNS → pule MN; ręcznie ustalone tylko przypisanie pul MN do stawów) | mucha (mózg + VNC z danych; VNC jako część muchy też decyduje lokalnie) | tylko stała mapa MN → staw (KT1–KT8 dotyczą wyłącznie jej) | do 4: podstawa, bark, łokieć, chwytak (jak FJ2 v1); oba stawy nadgarstka stałe | **tak, z zastrzeżeniami**: mapa MN → staw to nadal druga warstwa zaprojektowana; VNC steruje nogami, więc ruch ramienia to analogia; dopóki nie ma oka, wejście wzrokowe idzie przez enkoder (problem z 12 XI); znak Glu (19% napędu przedruchowego T2L) nieustalony | brak naturalnego sygnału „podnieś” (pilot FJ2); chwytak wciskany w stół; wybór pul pod wynik; zasięg w 2 krokach nieselektywny (887 z 1 314 DN) | KD3 osobno na warstwie VNC i osobno na warstwie mózgu; KD2, KD9, KD10; osobne ramiona Glu −1 / 0 / +1 |

**Rekomendacja (INFERRED).** HE jako kierunek główny. HD tylko jako ramię porównawcze. HB i HC nie. HA też nie: dla podstawy i chwytaka oznaczałby zastąpienie obecnego wzoru (DNa02 L − R, różnica pul MN) parą zaprojektowanych neuronów, co nic nie dodaje ponad ten wzór. Obecny stan to „HA bez neuronów”: stały wzór odczytu, czyli ENGINEERING.

---

## 7. Kontrole „kto decyduje” (KD)

Wszystkie kontrole to HYPOTHESIS / NOT IMPLEMENTED. Nic z tego nie zostało uruchomione.

| Kontrola | Co robimy | Co pokaże | Wynik, który obala „decyduje mucha” |
|---|---|---|---|
| **KD1 Wyciszenie muchy** | Wyjścia sieci muchy ustawiamy na 0 albo na ich średnią w czasie; reszta bez zmian. | Czy część zaprojektowana sama robi zadanie. | Sukces wyższy niż poziom przypadku P0: 95% przedziały Wilsona rozłączne albo różnica > 10 pp (progi niżej). |
| **KD2 Podmiana sygnału muchy** | (a) szum o tej samej częstości i statystyce; (b) zapis wyjścia muchy z innej próby; (c) wyjście przetasowane w czasie. | Czy liczy się bieżący sygnał muchy. | (b) daje podobny sukces, czyli cel niesie tłumacz albo sama scena. |
| **KD3 Rodzina tasowań okablowania** | Kolejno coraz ostrzej: losowa sieć tej samej wielkości; zachowane stopnie; zachowana siła wejścia i wyjścia każdego neuronu (nasze `equal_weight`); zachowane bloki typ × typ (klasa, strona, warstwa); zamiana stron. | Czy liczą się konkretne połączenia, czy tylko lateralizacja i klasy. | Dane ≤ tasowanie blokowe. Wtedy twierdzenie obniżamy do „struktura na poziomie typów / lateralizacja”. |
| **KD4 Trywialny przekaźnik** | Ręczny minimalny obwód (lewy → lewy DNa02; sign(gL − gR)). Z góry ustalamy miarę, której przekaźnik nie może „zdobyć”: wybór jednego z dwóch celów, odrzucenie dystraktora, odporność na opóźnienie, modulacja siły chwytu. | Czy sieć muchy wnosi coś ponad przekaźnik. | Sieć ≤ przekaźnik na tej mierze. |
| **KD5 Sieć zastępcza z tym samym łączem** | (a) losowa, stała; (b) SNN tej samej wielkości uczona RL/BPTT na tym zadaniu; (c) sieć zaprojektowana jak HD. | Czy kompetencja pochodzi z okablowania muchy (test „digital sphinx” zastosowany do nas). | (a) albo (c) ≥ mucha. Jeśli (b) ≥ mucha, mucha po prostu nie jest najlepsza; zasada na to pozwala, ale wtedy nie wolno twierdzić przewagi. |
| **KD6 Tłumacz zamrożony vs strojony osobno** | To samo, zamrożone łącze we wszystkich ramionach; osobno wariant strojony na nowo dla każdej sieci. | Czy to tłumacz, a nie mucha, się dopasowuje. | Po ponownym strojeniu tasowania doganiają dane. (Przykład naruszenia u nas: V5 v2, nachylenie dekodera 495,6 vs 100,9–146,9 dla SHUF_STR.) |
| **KD7 Rejestr punktów decyzji i udziału poleceń** | Spis każdego progu, argmax, if/else, zatrzasku, zegara i uczonej wagi w torze; klasyfikacja: bezpieczeństwo / tłumaczenie / decyzja wg KT1–KT9; udział tików, w których polecenie stawu pochodzi z sieci; udział prób, w których bezpieczeństwo zmieniło wynik (KT9). Pierwszy krok: odczytem kodu (bez uruchamiania) sprawdzić, czy wzmocnienie obecnego dekodera DNa02 jest stałe. | Ile decyzji naprawdę podejmuje mucha. | Jakakolwiek „decyzja” poza bezpieczeństwem w części zaprojektowanej przy deklaracji „decyduje mucha”. |
| **KD8 Zabawka z ustaloną prawdą** | Dwa sztuczne układy: w jednym decyduje tłumacz, w drugim zabawkowa „mucha”. Sprawdzamy, czy KD1–KD7 je rozróżniają. | Czy cały zestaw kontroli w ogóle działa (lekcja z [Jonas & Kording 2017](https://doi.org/10.1371/journal.pcbi.1005268)). | Zestaw ich nie rozróżnia. Wtedy nie wolno go używać na prawdziwym układzie. |
| **KD9 Sceny odłożone i właściwa moc testu** | Dystraktor, odległości poza zakresem strojenia, opóźnienie, tolerancja mniejsza niż początkowe odchylenie (naprawa H3/H4). Sceny strojenia spisane przed testem. | Czy wynik nie jest dopasowany do scen strojenia. | Wynik znika poza zakresem strojenia. |
| **KD10 Linearyzacja tłumacza** | Tłumacz zastąpiony jego zamrożonym odpowiednikiem liniowym. | Czy tłumacz liczy coś ponad tłumaczenie. | Zmiana sukcesu > 5 pp i istotna w parowym teście McNemara na wspólnych ziarnach (progi niżej). |
| **KD11 Rozliczenie informacji** | Pokazujemy, że wejścia tłumacza nie zawierają strony celu ani momentu chwytu. Pomocniczo: informacja wzajemna i entropia transferu, potwierdzane interwencją ([Schreiber 2000](https://doi.org/10.1103/PhysRevLett.85.461)). | Którędy płynie informacja o zadaniu. | Tłumacz ma dostęp do informacji o zadaniu. |
| **KD12 Atrybucja Shapleya z wielu wyciszeń** | Wkład elementów {mucha, tłumacz, enkoder, skrypty} liczony z kombinacji wyciszeń (MSA, [Keinan et al. 2004](https://doi.org/10.1162/0899766041336387)). Drogie, tylko po KD1–KD7. | Ilościowy udział każdej części. | Udział muchy ≈ 0. |

**Rejestracja przed uruchomieniem (HYPOTHESIS).** Przed każdym biegiem powstaje plik z:
- hipotezą, miarą główną, tolerancją i progami dla każdego ramienia;
- nową pulą ziaren i regułami wykluczeń;
- testami: przedziały Wilsona, McNemar dla par, poprawka Bonferroniego;
- zdaniem „co uznamy za porażkę”.

Analiza ma sumę kontrolną, a etykiety ramion są ślepe („ramię 1…k”).

**Progi rozstrzygające (HYPOTHESIS; liczby wpisuje się do rejestracji przed biegiem, przykładowe wartości do zatwierdzenia):**
1. **Poziom przypadku P0** = sukces ramienia z poleceniem zerowym albo losowym (o tej samej statystyce) na tych samych scenach, z tym samym n i tymi samymi ziarnami.
2. **KD1 / KT7 obala „decyduje mucha”**, jeśli część zaprojektowana sama (mucha wyciszona) ma sukces wyższy niż P0, a 95% przedziały Wilsona się nie nakładają, albo przewyższa P0 o więcej niż z góry ustalony margines, np. 10 pp.
3. **KD10 obala „D tylko tłumaczy”**, jeśli zamiana D na zamrożony odpowiednik liniowy zmienia sukces o więcej niż z góry ustalony margines, np. 5 pp, i zmiana jest istotna w parowym teście McNemara na wspólnych ziarnach.
4. **Uwaga o mocy (INFERRED):** przy n = 40 na ramię różnicy 5 pp nie da się wykryć (tabela niżej). Liczbę prób trzeba więc dobrać do marginesu przed testem, a nie po nim.

**Moc testu (VERIFIED, policzone tutaj).** Komenda:
```
python3 -c "from math import sqrt;z=1.96;W=lambda k,n:((k/n+z*z/(2*n))/(1+z*z/n)-z*sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n),(k/n+z*z/(2*n))/(1+z*z/n)+z*sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n));[print(k,n,*[round(x,3) for x in W(k,n)]) for k,n in [(38,40),(40,40),(10,10),(20,20),(3,40)]]"
```
Przedziały Wilsona 95%:

| Wynik | Przedział |
|---|---|
| 38/40 | 0,835–0,986 |
| 40/40 | 0,912–1,0 |
| 10/10 | 0,722–1,0 |
| 20/20 | 0,839–1,0 |
| 3/40 | 0,026–0,199 |

Przedziały się nakładają, więc 38/40 (n = 40) nie da się odróżnić od 40/40, 10/10 (n = 10) ani 20/20 (n = 20) (INFERRED). Różnice rzędu kilkunastu punktów procentowych wymagają więcej prób.

**Minimalny zestaw, który rekomenduję (INFERRED):** najpierw KD8, potem KD1, KD3 (z tasowaniem blokowym), KD4, KD5a, KD6, KD7, KD9, wszystko z rejestracją przed biegiem. KD11 i KD12 są drogie i słabsze.

---

## 8. Typowe błędy i nadinterpretacje, w tym nasze

| Błąd | Na czym polega | Przykład w literaturze | Przykład u nas |
|---|---|---|---|
| Sukces zadania brany za wierność biologiczną | dobre zachowanie nie znaczy, że mechanizm jest biologiczny | „Digital sphinx”; wypowiedzi Turagi i Cowleya ([The Transmitter](https://www.thetransmitter.org/systems-neuroscience/digital-sphinx-raises-questions-about-connectome-models/)) | 38/40 w V5 nie jest dowodem na połączenia: tasowanie z zachowaną siłą daje 10/10, a przekaźnik lewy → lewy 20/20 (REPORTED, `VALIDATION_PLAN.md` ok. w. 181–188) |
| Lateralizacja mylona z topologią | wystarcza podział na lewo i prawo | odruchy LGMD są zlateralizowane z budowy (INFERRED) | Zamiana stron daje 0/40, ale to pokazuje tylko, że strony mają znaczenie. „Mirrored” w naszych raportach znaczy **zamiana stron**, nie test topologii. |
| Tasowanie bez zachowania siły | tasowanie niszczy też siłę wejścia, więc sieć po prostu słabnie | — | 3/40 po tasowaniu bez dopasowania siły **nie** dowodzi roli połączeń. Porównanie z 10/10 to różne n (40 vs 10) i różne ziarna. |
| Tasowanie za słabe albo za mocne | tasowanie miesza też warstwy i klasy; wynik „konektom lepszy od losowego” zależy od tego, jak ostra jest kontrola i co się mierzy | [Dhiman 2026](https://arxiv.org/abs/2604.04033) (preprint): przy wspólnej losowej inicjalizacji i tasowaniu z zachowaniem stopni pozorna przewaga konektomu w dużej mierze znika (1 sieć, 5 próbek tasowania); [Therianos 2026](https://arxiv.org/abs/2606.17745) (preprint): zgrubna odpowiedź zależy od stopni i wag, a dokładne okablowanie tylko od niektórych miar. REPORTED (secondary: `laczenie_modyfikacje.md`); istnienie VERIFIED (arXiv) | Red team FJ2: zwykłe tasowanie mieszało warstwy receptor → IN → MN. Tasowanie zachowujące bloki klasa × noga (3–4 instancje, eksploracyjnie) dało −1,8…+1,8 Hz wobec 22,9 Hz dla danych, więc dane nadal wygrały. Miara to aktywność pul T2R; efekt zależał od Tr flexor i bodźca 40 mV; twierdzenie o uniesieniu T2L → T2R wycofano (REPORTED, `PILOT_NOTES.md`). |
| Łącze niesie inteligencję / ukryte strojenie | decoder, enkoder albo parametry stroi się pod wynik | Eon: mapowanie wybrane ręcznie; strojenie LGMD; [Supic & Stewart 2022](https://arxiv.org/abs/2210.01243): parametry z rozległego przeszukiwania | V5 v2: dekoder kalibrowany osobno dla każdej sieci (nachylenie 495,6 dla danych vs 100,9–146,9 dla SHUF_STR), co podważa tamten wynik „topologia ma znaczenie”. Później v3 (DATA − SWS równoważne w ±1°) i v4 (znak zależy od reżimu) go nie potwierdziły (REPORTED, master context). Siłę synapsy (J0) ustalono drugą regułą dopiero po tym, jak pierwsza zawiodła (w pętli 2/10), czyli po zobaczeniu wyniku (REPORTED, `VALIDATION_PLAN.md`, red team pkt 5). |
| Test na scenach strojenia | przeciek danych | [Kapoor & Narayanan 2023](https://doi.org/10.1016/j.patter.2023.100804): 294 prace z przeciekiem w 17 dziedzinach | Gdy cel stał dalej niż w zakresie strojenia (0,30 m), sieć trafiła 0/10, a regulator P 10/10. Przy progu sukcesu 6° sieć miała 40/40, przy ostrzejszym 4° już 29/40, więc wynik zależy od wybranego progu (REPORTED, `VALIDATION_PLAN.md`, red team pkt 4 i 7). |
| Kontrola, która z budowy nie może rozróżnić | test źle zaprojektowany | — | Kontrole H3/H4: cel zawsze startował co najmniej 10° od osi, a za sukces liczono błąd poniżej 5°. Wariant bez obrazu nie mógł więc wygrać z samej budowy testu, a zamiana stron oblewa dla każdego sterownika ze znakiem. To sprawdzenie łańcucha, nie dowód roli sieci (REPORTED, red team pkt 3). |
| Pojedyncze liczby z małej liczby prób; różne ziarna w ramionach | brak przedziałów ufności | [Henderson 2018](https://doi.org/10.1609/aaai.v32i1.11694); [Agarwal 2021](https://arxiv.org/abs/2108.13264); Huebotter: 10 vs 3 ziarna | 38/40 vs 40/40 nierozróżnialne (pkt 7) |
| Brak trywialnego lub klasycznego punktu odniesienia | SNN porównywana tylko z ANN tego samego kształtu | PopSAN, Huebotter | U nas P i przekaźnik są w porównaniach. P był lepszy w 446/450 parach (REPORTED: master context w. 122, tam VERIFIED 2026-11-03 w poprzedniej sesji; teraz nie powtarzane) i to zgłaszamy. |
| Energia liczona tylko z mocy dynamicznej | pominięta moc spoczynkowa i pamięć | PopSAN 140×; [Davidson & Furber 2021](https://doi.org/10.3389/fnins.2021.651141) | nie dotyczy; nie używać |
| Symulacja przedstawiana jako zdolność robota | — | Zaidel: pokazany ruch pochodzi z MuJoCo | FlyMind działa tylko w symulacji; nigdy nie był podłączony do ramienia |
| Degeneracja | to samo wyjście z różnych mechanizmów | [Prinz et al. 2004](https://doi.org/10.1038/nn1352): ponad 20 mln wersji 3-komórkowego modelu (skorupiak) | chwyt: 3 z 10 tasowań (99, 101, 102) lepsze od danych (90) |
| Konektom traktowany jak pełna funkcja | brak neuromodulacji, stanu, synaps elektrycznych | [Bargmann & Marder 2013](https://doi.org/10.1038/nmeth.2451); ograniczenia Shiu 2024 | neuromodulatory bez efektu; brak plastyczności; znak Glu nieustalony |
| „Konieczny i wystarczający” / „neuron od X” | logika N&S stosowana źle | [Yoshihara & Yoshihara 2018](https://doi.org/10.1080/01677063.2018.1468443) | DNa02 jako „neuron skrętu”: sam działa słabo, bez głowy nie działa (Braun 2024) |
| Odczyt jednej pary DN brany za pełne sterowanie | — | Braun 2024 | Sterujemy tylko podstawą: sieć decyduje o 1 z 6 stawów (plus siła chwytu); w demo 16,0% tików podstawy i 8,8% tików szczęki |
| Metody analizy niesprawdzone na układzie o znanym mechanizmie | — | Jonas & Kording 2017 | stąd KD8 |
| Język „wgranego mózgu” | — | Eon w prasie; Furber; Eon sam: „nie pełna kopia” | Przy prezentacji mówić: symulacja, MaleCNS, ALIF, wycinek, bez plastyczności, bez prawdziwego ramienia |
| Sztuczne pobudzanie nazwane zmysłem | — | Furber: proste pobudzenia zamiast danych zmysłowych | enkoder koloru → LC10a (decyzja 12 XI). Nie wolno pisać, że mucha „widzi” cel przez enkoder. |
| Łączenie niezależnych dowodów w jeden | — | — | Braun (bez głowy) i nasz red team: zgodne, ale niezależne |
| Nowość z braku wyników wyszukiwania | — | Lacuna nie ma grafu cytowań | nasze zdania „nikt tego nie zrobił” (pkt 9) |

**Chwyt, pełny obraz (REPORTED, `bio_advantage_research_20261110.md` w. 84–92, tam VERIFIED przez przeliczenie):**
- **Miękki kontakt, n = 135:** sieć 90, klasyczny 93, odruch 80.
  - Sieć vs klasyczny: p = 0,70.
  - Sieć vs odruch: p = 0,031. Źródło zastrzega, że próby nie są niezależne (45 obiektów × 3 pozy), więc p jest tylko orientacyjne; brak też poprawki na wiele porównań.
- **Sztywny kontakt:** klasyczny 101, sieć 84 (p = 0,001, też orientacyjne).
- **10 tasowań z dopasowaną siłą:** mediana 82, zakres 4–102; 3 z 10 (99, 101, 102) są lepsze od danych (90); dane są 4. na 11. Przewagi nad odruchem nie można więc przypisać połączeniom muchy.
- **FJ1** (12/12 vs odruch 12/12, REPORTED, master context) to inne, prostsze zadanie, bez przewagi.

Nie wykazano roli konkretnych połączeń.

---

## 9. Sprawdzenie nowości (Lacuna): LAC1–LAC3 (hipotezy Lacuny)

**Werdykt: CZĘŚCIOWO ZROBIONE (INFERRED).** Każdy składnik ma już poprzedników:
- modele muchy z konektomu;
- symulacje całego ciała muchy;
- SNN sterujące ramieniem.

Weryfikacja poprawiła dwie rzeczy. FlyGM już stosuje kontrole z grafem przetasowanym z zachowaniem stopni i z grafem losowym, choć jako test szkieletu uczonej polityki, a nie test „kto decyduje”. FPGAFly już uruchamia MaleCNS jako sieć LIF na sprzęcie. **Zostaje tylko wąska luka:** test „kto decyduje” w hybrydzie z zaprojektowanym tłumaczem i ciałem innym niż mucha. To wniosek z braku trafień w wyszukiwaniu, nie dowód.

Klastry Lacuna (REPORTED):
- „Translating Static Connectomes into Dynamic Functional Models”: 349 prac, głównie spoza muchy ([Lacuna](https://lacuna.tiptreesystems.com/direction/translating-static-connectomes-into-dynamic-functional-models-19037));
- „Energy Efficient Computing with SNNs”: 1555 prac (liczba sprawdzona przez weryfikatora) ([Lacuna](https://lacuna.tiptreesystems.com/direction/energy-efficient-computing-with-spiking-neural-networks-23868));
- pozostałe liczby (589, 410, 776, 834) niesprawdzone.

Hipotezy poniżej wygenerowała maszyna (Lacuna). Wszystkie to **HYPOTHESIS**:

| Id | Hipoteza | Związek z nami | Sprawdzenie |
|---|---|---|---|
| **LAC1** | „Context as Threshold”: kontekst (np. modulacja) wpisany w progi zapłonu neuronów; testowane na białkach ([Lacuna](https://lacuna.tiptreesystems.com/hypothesis/context-as-threshold-spiking-networks-whose-firing-rules-encode-biological-c6ae390947e2d494)) | słaby: pomysł, jak neuromodulacja (u nas bez efektu) mogłaby działać przez progi | weryfikator nie sprawdzał |
| **LAC2** | „Function-Guided Connectome Completion”: na ile znana funkcja (pierścień kierunku głowy, 439 neuronów) wyznacza okablowanie; punkt odniesienia to model blokowy typów komórek; kontrola „złej funkcji” ([Lacuna](https://lacuna.tiptreesystems.com/hypothesis/function-guided-connectome-completion-with-discrete-flow-matching-9a0b2a7c568b7d58)) | najbardziej użyteczna: model blokowy typów jako „null” i celowo zła funkcja jako kontrola | Potwierdzone, że istnieje (wygenerowana 2026-10-04). W źródle model blokowy służy do odtwarzania krawędzi; użycie go jako „null” dla tasowania to **nasze przeniesienie** (HYPOTHESIS). |
| **LAC3** | „Screening Robot Controller Structures by How They Fail Early”: tani wskaźnik oparty na zachowaniu przy fizyce spoza zakresu ([Lacuna](https://lacuna.tiptreesystems.com/hypothesis/screening-robot-controller-structures-by-how-they-fail-early-df03531b999b55a0)) | test na zakłóceniach przypomina nasz test opóźnienia 50 ms (17/40) | weryfikator nie sprawdzał |

---

## 10. Ograniczenia tego raportu

- **Filmu nie oglądałem.** Wszystko o obrazie pochodzi od Adama. Opisu filmu, daty i autora nie udało się pobrać.
- **Pełnych tekstów tych prac nie czytano:**
  - NeuroMechFly v2, Lappalainen, Cowley, flybody, Pugliese, „digital sphinx”, Stone;
  - Tieck, Hulea, Polykretis, Supic & Stewart, Aitsam (2022), Davies (2021);
  - Takemura i Marin (MANC), Eichler 2024;
  - tabel mięśni i stawów z suplementu Azevedo 2024.

  Powód: strony nature.com, eLife i PDF-y bioRxiv zwracały 403 albo były nieczytelne, a IEEE zwróciło 418. Liczby z tabel PopSAN, Huebotter i przeglądu LGMD pochodzą z wersji HTML/ar5iv, nie z PDF.
- **Usunięte albo niewykorzystane** (weryfikacja nie potwierdziła):
  - Stagsted: „robot mobilny” i opinia recenzenta;
  - liczby BAAIWorm (136 neuronów, 96 mięśni, 30 fps);
  - „rate-type” i lista ograniczeń z artykułu The Transmitter o CPG;
  - liczba 9/111 prac z miarami energii;
  - status „eLife reviewed preprint” dla „digital sphinx”;
  - liczby cytowań PopSAN.
- **Preprintu Sapkal i in.** nie odnaleziono (znany tylko z prasy). Carboncopies to źródło rzecznicze. Eon znamy tylko ze strony firmy i z prasy.
- **Dane MaleCNS — zastrzeżenia:**
  - plik z pewnością ≥0,5;
  - 44% końców krawędzi bez adnotacji;
  - brak podziału na rejony mózgu (ROI);
  - znak Glu nieznany;
  - funkcje mięśni znamy tylko z nazw typów;
  - grupy „stawowe” to umowna reguła;
  - przypisanie aDN = czyszczenie czułków niesprawdzone.
- **Wyniki lokalne** (V5, red team, chwyt, FJ2) są REPORTED z plików. Niczego nie uruchamiałem ponownie.
- **Nie przeszukano:** literatury o współsterowaniu w interfejsach mózg–maszyna (gdzie pada to samo pytanie „kto decyduje”), robotów z hybrydowym dynamic clamp, OpenWorm c302.
- **Nowość** (pkt 9) to wniosek z braku trafień, nie przegląd systematyczny.
- **Wcześniejsze notatki** przeczytałem tylko częściowo: z `research_notes/Hybrydowe mózgi z konektomów/laczenie_modyfikacje.md` fragmenty o Spaun, NRP, Dhiman, Therianos i taksonomii 5 klas (pkt 3.5). Pozostałych (`snn_neuromorficzne.md`, `obwody_funkcje.md`, `konkurencja_platformy.md`, folder `research_notes/Konektom muchy dla SO101/`) nie czytałem ponownie; opierałem się na nowych notatkach, ich weryfikacji i wybranych plikach lokalnych.
- **Notatki źródłowej nie poprawiałem:** `principle_controls_pitfalls.md` w. 39 nadal błędnie przypisuje Adamowi ocenę K1 jako „boundary”. Poprawna wersja jest w pkt 5 tego raportu (ocena Claude z 12 XI, decyzja Adama otwarta).
- **Raport nie jest niezależny:** pisze go ten sam system, który budował FlyMind.

---

## 11. Źródła

Oznaczenia: [full] pełny tekst; [abs] abstrakt; [meta] tylko metadane / istnienie; [sec] źródło wtórne; [page] strona WWW.

**Film i metadane**
- Founders, Inc., film: https://youtu.be/NIMEbZJHQBM; oEmbed: https://www.youtube.com/oembed?url=https://youtu.be/NIMEbZJHQBM&format=json [meta]

**Projektowane kontrolery SNN**
- Zaidel, Shalumov, Volinski, Supic, Ezra Tsur 2021: https://doi.org/10.3389/fnbot.2021.631159 [full, Europe PMC PMC7887770]
- Bing, Meschede, Röhrbein, Huang, Knoll 2018 (przegląd): https://doi.org/10.3389/fnbot.2018.00035 [full, PMC6043678]
- Mompó Alepuz, Papageorgiou, Tolu 2024: https://doi.org/10.3389/fnbot.2024.1395617 [abs, początek]
- DeWolf, Stewart, Slotine, Eliasmith 2016: https://doi.org/10.1098/rspb.2016.2134 [abs]
- DeWolf 2021, Science Robotics: https://doi.org/10.1126/scirobotics.abk3268 [meta]
- DeWolf, Jaworski, Eliasmith 2020 (Nengo): https://arxiv.org/abs/2007.10227 [abs]
- Tieck et al. 2019: https://doi.org/10.4018/ijcini.2019010101 [abs]; Tieck et al., IROS 2019: https://doi.org/10.1109/iros40897.2019.8968128 [meta]
- Hulea, Uleru, Caruntu 2021: https://doi.org/10.3390/s21082730 [abs]
- Stagsted et al. 2020 (RSS XVI): https://roboticsproceedings.org/rss16/p074.html, DOI 10.15607/RSS.2020.XVI.074 [abs]
- Michaelis, Lehr, Tetzlaff 2020: https://doi.org/10.3389/fnbot.2020.589532 [abs]
- Ijspeert 2008: https://doi.org/10.1016/j.neunet.2008.03.014 [meta]
- Steffen et al. 2026 (ICONS): https://doi.org/10.1145/3822454.3822466; https://arxiv.org/abs/2606.11034 [abs]
- Juarez-Lora et al. 2022: https://doi.org/10.3389/fnbot.2022.904017 [full, PMC9161736]
- Polykretis, Supic, Danielescu 2022: https://arxiv.org/abs/2209.02787 [abs]
- Supic & Stewart 2022: https://arxiv.org/abs/2210.01243 [abs]
- Linares-Barranco et al. 2024: https://arxiv.org/abs/2405.12849 [abs]
- Traub, Legenstein, Otte 2021 (IROS): https://doi.org/10.1109/iros51168.2021.9636001 [meta]
- Chen et al. 2020: https://doi.org/10.1109/iciea48937.2020.9248389 [meta]; Bouganis & Shanahan 2010: https://doi.org/10.1109/ijcnn.2010.5596525 [meta]
- Eliasmith et al. 2012 (Spaun), Science: https://doi.org/10.1126/science.1225266 [meta, Crossref 13 XI; treść sec: `laczenie_modyfikacje.md`]
- Neurorobotics Platform (EBRAINS): https://www.ebrains.eu/tools/nrp [sec: `laczenie_modyfikacje.md`; strony nie otwierano 13 XI]
- Kreiser et al. 2020: https://doi.org/10.3389/fnins.2020.00551 [meta]; Vasco et al. 2016: https://doi.org/10.1109/humanoids.2016.7803355 [meta]; D'Angelo et al. 2022: https://doi.org/10.1088/2634-4386/ac6b50 [meta]

**Uczenie SNN i rzetelność pomiaru**
- Tang, Kumar, Yoo, Michmizos 2020 (PopSAN): https://arxiv.org/abs/2010.09635 [full, ar5iv]; PMLR: https://proceedings.mlr.press/v155/tang21a.html [meta]
- Jaisankar et al. 2025: https://arxiv.org/abs/2510.10516 [abs]
- Huebotter, Lanillos, van Gerven, Thill 2025: https://arxiv.org/abs/2509.05356 [full HTML, tabele]
- arXiv 2508.12038 (ramię 9-DOF, PPO): https://arxiv.org/abs/2508.12038 [abs]; Zahra, Navarro-Alarcon, Tolu: https://arxiv.org/abs/2011.01641 [meta]
- Neftci, Mostafa, Zenke 2019: https://arxiv.org/abs/1901.09948 [meta]
- Bellec et al. 2020: https://doi.org/10.1038/s41467-020-17236-y [abs]
- Rueckauer et al. 2017: https://doi.org/10.3389/fnins.2017.00682 [abs]
- Bing et al. 2020: https://doi.org/10.1016/j.neunet.2019.05.019 [abs]
- Salt, Howard, Indiveri, Sandamirskaya 2019: https://arxiv.org/abs/1910.07960 [abs]
- Henderson et al. 2018: https://doi.org/10.1609/aaai.v32i1.11694; https://arxiv.org/abs/1709.06560 [abs]
- Agarwal et al. 2021: https://arxiv.org/abs/2108.13264 [abs]
- NeuroBench (Yik et al. 2023): https://arxiv.org/abs/2304.04640 [abs]
- Putra et al. 2024: https://arxiv.org/abs/2404.03325 [abs]; Marchisio & Shafique 2025: https://arxiv.org/abs/2507.18139 [abs]; Novo et al. 2024: https://arxiv.org/abs/2407.06792 [abs]
- Aitsam, Davies, Di Nuovo 2022: https://doi.org/10.1109/ACCESS.2022.3219440 [meta]
- CVUT, informacja prasowa o ramach oceny agentów neuromorficznych (Nature Machine Intelligence 2026): https://aktualne.cvut.cz/en/reports/20260324-how-to-measure-the-intelligence-of-nature-inspired-robots-study-with-first-author [page; DOI i autorzy niesprawdzone]

**Energia**
- Davidson & Furber 2021: https://doi.org/10.3389/fnins.2021.651141 [abs]
- Yan, Bai, Tang, Wong 2024: https://arxiv.org/abs/2409.08290 [abs]
- Dampfhoffer et al. 2023: https://doi.org/10.1109/TETCI.2022.3214509 [meta]
- Davies et al. 2021 (Loihi): https://doi.org/10.1109/JPROC.2021.3067593 [meta; treść abstraktu tylko z wtórnego streszczenia]
- arXiv 2506.09599: https://arxiv.org/abs/2506.09599 [meta; liczba 9/111 NOT VERIFIED]

**„Bez treningu”: LGMD**
- Qin, Peng, Yue, Fu 2025, J. R. Soc. Interface: https://doi.org/10.1098/rsif.2025.0433; preprint https://arxiv.org/abs/2501.02982 [full HTML preprintu, częściowo; jedna praca, dwie wersje]
- Gao, Liu, Wang, Fu 2024: https://doi.org/10.3390/biomimetics9110650 [abs przez DOAJ API]
- Fu et al. 2021: https://doi.org/10.3389/frobt.2021.529872 [abs]
- Zhao et al. 2020: https://arxiv.org/abs/2005.04397 [abs]; Zhao et al. 2019: https://arxiv.org/abs/1904.07206 [meta]; OppLoD: https://arxiv.org/abs/2302.10284 [meta]

**Hybrydy z konektomem i modele muchy**
- Wang-Chen et al. 2024 (NeuroMechFly v2): https://doi.org/10.1038/s41592-024-02497-y [abs]
- Lappalainen et al. 2024: https://doi.org/10.1038/s41586-024-07939-3 [abs]
- Cowley et al. 2024: https://doi.org/10.1038/s41586-024-07451-8 [abs]
- Vaxenburg et al. 2025 (flybody): https://doi.org/10.1038/s41586-025-09029-4 [abs]
- Shiu et al. 2024: https://doi.org/10.1038/s41586-024-07763-9 [full, PMC11446845: ograniczenia i kontrola tasowania]
- Pugliese et al.: https://doi.org/10.1101/2025.09.12.675944 [abs]; Nature: https://doi.org/10.1038/s41586-026-11195-y [meta]
- The Transmitter, obwód chodu: https://www.thetransmitter.org/systems-neuroscience/long-sought-walking-circuit-found-in-fruit-flies/ [page, sec]
- Eon Systems: https://eon.systems/updates/embodied-brain-emulation [page, full]
- The Register (Furber): https://www.theregister.com/a/5224139 [page]
- Carboncopies Foundation: https://carboncopies.org/Blog/Posts/FruitFlyNotUploaded/Post/ [page, advocacy]
- Brunton, Abe, Hu, Tuthill 2026 („digital sphinx”): https://doi.org/10.64898/2026.03.20.713233 [abs przez bioRxiv API; preprint]
- The Transmitter, N. Mesa, 2 IV 2026: https://www.thetransmitter.org/systems-neuroscience/digital-sphinx-raises-questions-about-connectome-models/ [page, sec]
- Pospisil et al. 2024 (effectome): https://doi.org/10.1038/s41586-024-07982-0 [abs]
- Jin, Zhu, Zhang, Sui (FlyGM): https://arxiv.org/abs/2602.17997 [full HTML]
- Ye (FPGAFly): https://arxiv.org/abs/2610.38118 [abs]
- Liew et al. (NeurIPS 2025, arXiv 2026): https://arxiv.org/abs/2609.01330 [abs]
- BAAIWorm: https://doi.org/10.1038/s43588-024-00740-2 [meta]; State of Brain Emulation Report 2025: https://arxiv.org/abs/2510.15745 [meta]
- Stone et al. 2017 (pszczoła): https://doi.org/10.1016/j.cub.2017.08.052 [abs]
- Dupeyroux, Serres, Viollet 2019 (AntBot): https://doi.org/10.1126/scirobotics.aau0307 [abs]
- STMR: https://arxiv.org/abs/2404.11557 [meta]; Human2Humanoid: https://arxiv.org/abs/2606.03476 [meta]
- FlySoul: https://github.com/heyobi/flysoul [page, README]; DesktopFly: https://github.com/DenisSergeevitch/desktop-fly [page, README]

**Biologia: mózg i VNC**
- Namiki et al. 2018: https://doi.org/10.7554/eLife.34272 [full]
- Cheong et al. 2026 (MANC, DN/AN/MN): https://doi.org/10.7554/eLife.96084 [full]
- Takemura et al. 2024 (MANC): https://doi.org/10.7554/eLife.97769 [meta]
- Stürner et al. 2025: https://doi.org/10.1038/s41586-025-08925-z [full, PMC12222017]
- Braun, Hurtak, Wang-Chen, Ramdya 2024: https://doi.org/10.1038/s41586-024-07523-9 [full, PMC11186778]
- Rayshubskiy et al. 2025: https://doi.org/10.7554/eLife.102230 [full, PMC12279373]
- Bidaye et al. 2020 (P9): https://doi.org/10.1016/j.neuron.2020.07.032 [abs]; Bidaye et al. 2014 (MDN): https://doi.org/10.1126/science.1249964 [abs]
- Carreira-Rosario et al. 2018: https://doi.org/10.7554/eLife.38554 [meta]
- Azevedo et al. 2020: https://doi.org/10.7554/eLife.56754 [full, PMC7347388]
- Lesser et al. 2024: https://doi.org/10.1038/s41586-024-07600-z [abs]; Azevedo et al. 2024 (FANC): https://doi.org/10.1038/s41586-024-07389-x [abs]
- Bidaye, Bockemühl, Büschges 2018: https://doi.org/10.1152/jn.00658.2017 [abs]; Tuthill & Wilson 2016: https://doi.org/10.1016/j.cub.2016.06.070 [abs]
- Mamiya et al. 2018: https://doi.org/10.1016/j.neuron.2018.09.009 [abs]
- Hampel et al. 2015: https://doi.org/10.7554/eLife.08758 [abs]
- Baek & Mann 2009: https://doi.org/10.1523/JNEUROSCI.1585-09.2009 [abs]; Brierley et al. 2012: https://doi.org/10.1002/cne.23003 [abs]
- Pick & Strauss 2005: https://doi.org/10.1016/j.cub.2005.07.022 [abs]
- Calle-Schuler et al.: https://doi.org/10.7554/eLife.108044 [abs]; bioRxiv: https://doi.org/10.1101/2025.05.19.654894 [meta]
- Chen et al. 2023: https://doi.org/10.1038/s41593-023-01281-z [abs]; Fujiwara et al. 2017: https://doi.org/10.1038/nn.4435 [abs]

**Kontrole, atrybucja, błędy**
- Keinan, Sandbank, Hilgetag, Meilijson, Ruppin 2004: https://doi.org/10.1162/0899766041336387 [abs]
- Keinan et al. 2006: https://doi.org/10.1162/artl.2006.12.3.333 [meta]; Keinan, Hilgetag, Meilijson, Ruppin 2004 (Neurocomputing): https://doi.org/10.1016/j.neucom.2004.01.046 [meta]
- Aharonov, Segev, Meilijson, Ruppin 2003: https://doi.org/10.1162/08997660360581949 [meta]
- Schreiber 2000: https://doi.org/10.1103/PhysRevLett.85.461 [abs]
- Jonas & Kording 2017: https://doi.org/10.1371/journal.pcbi.1005268 [abs]
- Bargmann & Marder 2013: https://doi.org/10.1038/nmeth.2451 [abs]
- Prinz, Bucher, Marder 2004: https://doi.org/10.1038/nn1352 [abs]; Marder & Taylor 2011: https://doi.org/10.1038/nn.2735 [meta]
- Yoshihara & Yoshihara 2018: https://doi.org/10.1080/01677063.2018.1468443 [abs]
- Kapoor & Narayanan 2023: https://doi.org/10.1016/j.patter.2023.100804 [abs]
- Krakauer et al. 2017: https://doi.org/10.1016/j.neuron.2016.12.041 [meta]
- Dhiman 2026, „Topological Sensitivity in Connectome-Constrained Neural Networks”: https://arxiv.org/abs/2604.04033 [meta, arXiv API 13 XI; treść sec: `laczenie_modyfikacje.md`]
- Therianos 2026, „A frozen rate operator from the complete larval connectome…”: https://arxiv.org/abs/2606.17745 [meta, arXiv API 13 XI; treść sec: `laczenie_modyfikacje.md`]

**Lacuna (wygenerowane maszynowo / metadane)**
- LAC1: https://lacuna.tiptreesystems.com/hypothesis/context-as-threshold-spiking-networks-whose-firing-rules-encode-biological-c6ae390947e2d494
- LAC2: https://lacuna.tiptreesystems.com/hypothesis/function-guided-connectome-completion-with-discrete-flow-matching-9a0b2a7c568b7d58
- LAC3: https://lacuna.tiptreesystems.com/hypothesis/screening-robot-controller-structures-by-how-they-fail-early-df03531b999b55a0
- Klastry: https://lacuna.tiptreesystems.com/direction/translating-static-connectomes-into-dynamic-functional-models-19037; https://lacuna.tiptreesystems.com/direction/energy-efficient-computing-with-spiking-neural-networks-23868; https://lacuna.tiptreesystems.com/direction/surrogate-gradient-learning-for-spiking-neural-networks-24429; https://lacuna.tiptreesystems.com/direction/low-latency-spiking-neural-network-inference-23852; https://lacuna.tiptreesystems.com/direction/closing-the-neuromorphic-hardware-deployment-gap-25184; https://lacuna.tiptreesystems.com/direction/overcoming-the-reality-gap-in-robotic-control-28247

**Pliki lokalne (tylko odczyt)**
- `/Users/admin/so101_fly_project/flymind/FLYMIND_MASTER_CONTEXT.md`
- `/Users/admin/so101_fly_project/flymind/VALIDATION_PLAN.md` (ok. w. 175–250)
- `/Users/admin/so101_fly_project/flymind/reports/bio_advantage_research_20261110.md` (w. 86–99)
- `/Users/admin/so101_fly_project/flymind/reports/vla_with_fly_design_20261112.md` (W3, K1, K3), `fly_learning_research_20261112.md` (tłumacz T1), `fly_eye_plan_20261112.md` (LPLC2, G2): przez notatki i grep
- `/Users/admin/so101_fly_project/flymind/experiments/fj2_fly_arm/DESIGN.md`, `PILOT_NOTES.md`
- `/Users/admin/so101_fly_project/flymind/results/audit_shared_decoder_20261029.txt`
- `/Users/admin/so101_fly_project/research_notes/Projektowane neurony i hybryda z muchą/*.md` (7 notatek + 7 weryfikacji)
- `/Users/admin/so101_fly_project/research_notes/Hybrydowe mózgi z konektomów/laczenie_modyfikacje.md` (fragmenty: sekcje 1, 4, 6)

---

## Decyzje dla Adama

Kolejność: najpierw jedyna decyzja z terminem (DH6), potem pozostałe w kolejności numerów.

**DH6. TERMIN 16 XI. Co z tego idzie na plakat?**
- **Opcje:**
  - (a) nic o projektowanych neuronach i hybrydach;
  - (b) jedno zdanie „dalszy plan: sprawdzamy, kto naprawdę decyduje”, bez wyników;
  - (c) schemat architektury HE jako plan.
- **Rekomendacja Claude:** (a), najwyżej (b). Na plakat nie trafiają:
  - film i liczba „98%”;
  - „38/40 vs 3/40” jako dowód na połączenia;
  - zdanie, że mucha „widzi” cel.
- **Koszt i ryzyko:** zero kosztu. Przy (c) jurorzy mogą wziąć plan za wynik.
- **Po decyzji:** treść plakatu zostaje przy sprawdzonych twierdzeniach z pkt 10 master context: symulacja, MaleCNS, SNN obraca podstawę, P lepszy. O chwytaku jedno spójne zdanie: w FJ1 sieć bez przewagi nad odruchem (12/12 vs 12/12); w benchmarku 10 XI (miękki kontakt, n = 135) sieć 90 > odruch 80 (p = 0,031, orientacyjne), ale nie lepsza od klasycznego (93), gorsza przy sztywnym kontakcie (84 vs 101) i bez wykazanej roli połączeń (REPORTED, pkt 8).

**DH1. Czy przyjmujesz KT1–KT9 (pkt 5) jako obowiązującą regułę granicy tłumacz/decyzja, także dla obecnego dekodera DNa02?**
- **Opcje:** tak / nie.
- **Rekomendacja Claude:** tak.
- **Koszt i ryzyko:** decyzja bez obliczeń. Ryzyko: nawet „tłumacz” może po cichu nieść decyzję, dlatego potrzebne są kontrole KD i progi z pkt 7.
- **Po „tak”:** po Twojej zgodzie dopisuję KT1–KT9 (oraz KW1–KW3 dla wejścia, jeśli je też zatwierdzisz) do zasad w `FLYMIND_MASTER_CONTEXT.md` i stosuję je w każdym projekcie; obecny dekoder DNa02 trzeba wtedy sprawdzić pod KT1 (stałe wzmocnienie, KD7). **Po „nie”:** granica zostaje nieformalna, a każde twierdzenie „decyduje mucha” wymaga osobnego uzasadnienia. W obu przypadkach rekomendowany następny krok to ten sam DH3. Pytanie, czy część zaprojektowaną wolno uczyć i czy wolno ją mieć jako ramię porównawcze, jest w DH4.

**DH2. Który wariant planować?**
- **Opcje:** HE (VNC z danych, rozwinięcie FJ2) / HA (para zaprojektowanych neuronów dla podstawy i chwytaka) / HC / HB albo HD jako porównanie / żaden.
- **Rekomendacja Claude:** HE jako kierunek główny; HD tylko jako ramię porównawcze w KD5; HA nie (nic nie dodaje ponad obecny wzór odczytu, który jest „HA bez neuronów”); HB i HC nie.
- **Koszt i ryzyko:** HE wymaga najpierw kroku na danych (DH3) i niezależnej kontroli odstępu od stołu (pilot FJ2: 29–44 N wciskania). Jako zmierzony wynik raczej nie zdąży na 1 XII (INFERRED).
- **Po „tak”:** tylko plan na papierze z protokołem KD; nic nie uruchamiam bez osobnej zgody. **Po „nie”:** zostaje obecny stan (podstawa i chwytak).

**DH3. Czy najpierw zrobić krok tylko na danych, bez żadnej symulacji?** Zakres: mapa pul MN T1/T2 → stawy SO-101 z uzasadnieniem z literatury (tabele mięśni Azevedo 2024), ścieżki DN → interneurony → MN ważone siłą i znakiem, osobno dla Glu −1 / 0 / +1; plus odczyt kodu, czy wzmocnienie obecnego dekodera DNa02 jest stałe.
- **Opcje:** tak / nie / później.
- **Rekomendacja Claude:** tak.
- **Koszt i ryzyko:** ok. jedna sesja, tylko zapytania do lokalnych plików i odczyt kodu. Ryzyko doboru pul „pod wynik” ograniczamy tak, że mapę i uzasadnienie spisujemy przed jakimkolwiek uruchomieniem.
- **Po „tak”:** raport z mapą, tabelami i listą luk (np. brak MN stopy z nazwy w T2, brak odpowiednika obrotu nadgarstka). **Po „nie”:** HE zostaje przy częściowo arbitralnej mapie FJ2 v1.

**DH4. Część zaprojektowana lub uczona: jaka rola?**
- **Opcje:**
  - (a) tylko stała, wg KT (ręcznie albo jedna kalibracja na osobnym zbiorze, potem zamrożona);
  - (b) jak (a), a do tego wersje uczone lub w pełni zaprojektowane (HB/HD) wyłącznie jako jawnie nazwane ramiona porównawcze, nigdy jako „mucha”;
  - (c) uczona w głównym układzie.
- **Rekomendacja Claude:** (b).
- **Koszt i ryzyko:** przy (c) wyuczony łącznik może zrobić całą pracę („digital sphinx”) i wynik nic by nie mówił o musze.
- **Po (a) lub (b):** KD6 (zamrożony vs strojony) staje się obowiązkowa; przy (b) ramiona porównawcze dostają osobne nazwy w rejestracji. **Po (c):** każdy wynik trzeba opisać jako „decyduje układ uczony”, nie „mucha”.

**DH5. Które kontrole są obowiązkowe przed jakimkolwiek twierdzeniem „decyduje mucha”?**
- **Opcje:**
  - pełny zestaw KD1–KD12;
  - zestaw minimalny: KD8 najpierw, potem KD1, KD3 (z tasowaniem blokowym), KD4, KD5a, KD6, KD7, KD9, z rejestracją przed biegiem i progami z pkt 7;
  - mniej.
- **Rekomendacja Claude:** zestaw minimalny.
- **Koszt i ryzyko:** wiele ramion po co najmniej 40 prób. Przy 40 próbach różnic rzędu kilkunastu punktów procentowych nie widać (pkt 7), więc może trzeba więcej prób i nowych ziaren.
- **Po „tak”:** każdy protokół musi zawierać te kontrole, progi i zdanie „co uznamy za porażkę”. **Po „nie”:** nie wolno twierdzić, że decyduje mucha.

**DH7. Czy hybryda ze wzrokiem ma czekać na „oko” z planu z 12 XI?**
- **Opcje:**
  - tak: do czasu bramki G2 (test kierunku ruchu T4/T5) hybryda HE tylko z dotykiem albo tylko na papierze;
  - nie: dopuszczasz enkoder (koloru dla LC10a, LC9 w FJ2) jako jawnie oznaczone rusztowanie.
- **Rekomendacja Claude:** tak, bo enkoder uznałeś 12 XI za sztuczne pobudzanie (łamie też KW1, pkt 5).
- **Koszt i ryzyko:** ruch ramienia w stronę obiektu przez muchę odsuwa się w czasie. Przy „nie” każdy wynik wzrokowy hybrydy łamałby zasadę wejścia.
- **Po „tak”:** łączę plan HE z planem oka (LPLC2 najpierw). **Po „nie”:** każdy taki wynik opisuję jako „wejście: sztuczne pobudzanie”.

**DH8. ZAŁATWIONE 13 XI:** Adam wkleił transkrypcję; uzupełnienie w pkt 1. Dalsze szukanie niepotrzebne. Poniżej pierwotna treść decyzji.

**DH8 (pierwotnie). Czy szukać więcej informacji o filmie?**
- **Opcje:** Adam wkleja opis filmu i linki z opisu / Claude próbuje odczytać napisy narzędziem (wymaga osobnej zgody na pobranie i ewentualną instalację narzędzia; nic nie instaluję bez zgody) / nie szukamy.
- **Rekomendacja Claude:** niski priorytet. Jeśli tak, najprościej, żebyś wkleił opis. Nic nie wysyłam do autora bez Twojej zgody.
- **Koszt i ryzyko:** minimalny. Bez tych informacji film zostaje inspiracją, nie źródłem.
- **Po „tak”:** dopisuję, co da się z opisu sprawdzić. **Po „nie”:** sekcja 1 zostaje bez zmian.
