# AI, AGI i uczenie robotów (pytania 7, 8, 9) — notatki z 12 XI 2026

Metoda: ~20 wywołań WebSearch/WebFetch. Otwarte bezpośrednio: abstrakty arXiv (2511.14759, 2505.22954, 2506.01844, 2504.16054, 2503.14734, 2107.04034), blog DeepMind AlphaEvolve, arcprize.org (strona ARC-AGI-3 i analiza 2025), the-decoder (2 artykuły), wpis LessWrong o raporcie METR. Reszta to wyniki wyszukiwania (REPORTED). Nie otwarto: strony Physical Intelligence (HTTP 429), raportu Gemini 4 Argon, raportu METR, kart modeli. Etykiety: VERIFIED = otwarte źródło; REPORTED = wynik wyszukiwania/wtórne; INFERRED = mój wniosek.

## Dlaczego roboty się uczy (7)

### Takeaway
Nowe zadania nie dają się ręcznie zaprogramować, a kopiowanie struktury mózgu nie daje umiejętności. Dlatego czołowe systemy (π0.5, π*0.6, Gemini Robotics, GR00T, SmolVLA) uczą się z danych i z doświadczenia. Konektom muchy to schemat połączeń, a nie umiejętności. Rośnie rola uczenia ze wzmocnieniem na robocie, a dane robotów pozostają wąskim gardłem.

### Cited Findings
- π0.5 (Physical Intelligence): ko-trening na danych z wielu robotów, semantyce i danych z sieci; autorzy twierdzą, że to pierwszy end-to-end system uczący się, który wykonuje długie, zręczne zadania (sprzątanie kuchni/sypialni) w „całkowicie nowych domach" — VERIFIED (abstrakt, deklaracja autorów) — [arXiv 2504.16054](https://arxiv.org/abs/2504.16054)
- π*0.6 z metodą RECAP (RL warunkowane przewagą, offline RL + dane z robota): na najtrudniejszych zadaniach „ponad dwukrotnie" większa przepustowość i „mniej więcej o połowę" mniej porażek; pranie w domach, składanie pudełek, espresso — VERIFIED (abstrakt, bez liczb bezwzględnych) — [arXiv 2511.14759](https://arxiv.org/abs/2511.14759). Blog PI (espresso 5:30–23:30, 50 nowych sztuk prania, 59 pudełek) — REPORTED, strona nie otworzyła się (429) — [pi.website/blog/pistar06](https://pi.website/blog/pistar06). Publikacja na RSS 2026 — REPORTED — [roboticsproceedings.org/rss22/p087.pdf](https://roboticsproceedings.org/rss22/p087.pdf)
- SmolVLA: wydajność „porównywalna z VLA 10× większymi", trening na jednym GPU, wdrożenie na konsumenckim GPU/CPU, kod, modele i dane otwarte — VERIFIED (abstrakt, deklaracja autorów; liczb nie ma w abstrakcie) — [arXiv 2506.01844](https://arxiv.org/abs/2506.01844)
- GR00T N1 (NVIDIA): otwarty model dla humanoidów, System 2 (VLM) + System 1 (transformer dyfuzyjny), dane: trajektorie z robotów, wideo ludzi, dane syntetyczne; deklaruje przewagę nad bazami imitacyjnymi w symulacji i na Fourier GR-1 — VERIFIED (abstrakt) — [arXiv 2503.14734](https://arxiv.org/abs/2503.14734)
- Gemini Robotics 2 (30 VII 2026) trzy modele: flagowy VLA dla całego humanoida, ER 2, On-Device 2; Gemini Robotics 2.5 (10 XI 2026) — według jednego źródła Apollo 2 w zakładzie Mercedesa 96% sukcesu — REPORTED, tylko wtórne — [ai2.work](https://ai2.work/blog/gemini-robotics-2-one-checkpoint-for-humanoids-arms-and-edge), [siliconangle](https://siliconangle.com/2026/08/google-deepmind-debuts-gemini-robotics-2-model-series/), [letsdatascience](https://letsdatascience.com/news/deepmind-releases-gemini-robotics-25-and-open-asimov-jailbre-ca67d149). GR00T N2 tylko zapowiedziany na GTC 2026, wydane jest GR00T 1.7; brak liczb — REPORTED (jw.)
- Uczenie w symulacji → świat rzeczywisty: RMA, czworonóg uczony wyłącznie w symulacji adaptuje się „w ułamkach sekundy", bez dostrajania na robocie A1 (skały, piasek, schody) — VERIFIED (abstrakt, 2021) — [arXiv 2107.04034](https://arxiv.org/abs/2107.04034)
- Dane: według jednego bloga π0 trenowano na ok. 10 000 h demonstracji, a LLM na rzędzie 1,2 mld godzin tekstu (różnica ok. 100 000×); Goldberg szacuje lukę na ok. 100 000 lat czytania — REPORTED (blogi/prasa, liczby się różnią między źródłami) — [Peike Li](https://gogoduck912.github.io/blog/robotics-scaling-law/), [Berkeley news](https://news.berkeley.edu/?p=134910). Nie otwarto, więc traktować jako rząd wielkości.
- Moravec: to, co łatwe dla ludzi, jest trudne dla robotów (opis Goldberga) — REPORTED — [vcresearch.berkeley.edu](https://vcresearch.berkeley.edu/news/are-we-truly-verge-humanoid-revolution). Seminarium Stanford 2026 mówi też o „algorytmicznym paradoksie Moraveca" (niestabilność ciągłego sterowania) — REPORTED — [pulse.bot](https://www.pulse.bot/ai/video/stanford-robotics-seminar-engr319-winter-2026-gen-control-action-chunking-moravecs-paradox-eff254af-70c7-46cf-bbf9-cfdf3ae71133)
- Z wcześniejszej pracy (cytowane plikami, nie sprawdzane ponownie): niezależny test π0 (Penn) średni postęp 42,3%; Open X-Embodiment 22 roboty/527 umiejętności; π0.5: ok. 400 h z robota mobilnego w ok. 100 domach — `/Users/admin/so101_fly_project/flymind/reports/robot_ai_revolution_20261112.md` (VERIFIED tam, tu tylko odwołanie). Benchmark SO-101: π0.5 56%, SmolVLA 32,5% (arXiv 2606.08881, z kontekstu zadania, nie otwierano).

### Inferences
- Odpowiedź na pytanie 7 w prostych słowach: (a) ręczne programowanie działa tam, gdzie świat jest znany i powtarzalny; (b) zwierzę też się uczy — mucha ma ciała grzybkowe (4064 komórek Kenyona, 340 DAN, 97 MBON w MaleCNS, z kontekstu projektu), więc „konektom" to dopiero sprzęt, a nie wiedza; (c) VLA łączą wiedzę z internetu i dane z robotów, a od 2025 dokładają uczenie z własnych prób (RECAP) — INFERRED.
- Premise pytania („mózgi nie są lepsze od konektomów robota") jest do doprecyzowania: nie ma dowodu, że konektom muchy sterujący ramieniem bije metody uczone; nasze własne wyniki w symulacji (T2L: klasyczny 93/101 vs sieć 90/84; wiring bez przewagi) tego nie pokazują. Uczciwa teza: konektom jest obiektem badań i źródłem pomysłów, nie zamiennikiem uczenia — INFERRED.
- Sim-to-real RL (RMA) pokazuje, że da się uczyć tanio w symulacji, ale dla kontaktu/zręczności nie znaleziono tak mocnego odpowiednika (zgodnie z wcześniejszym raportem) — INFERRED.

### Gaps
- Brak liczb sukcesu z samych kart modeli π0.5/π*0.6/Gemini Robotics 2/2.5 (blog PI 429; Gemini tylko wtórne). Brak niezależnego porównania GR00T N1.x z π0.5 na jednym robocie.
- Moravec: nie znaleziono pierwotnego źródła liczbowego dla luki danych; szacunki rzędu wielkości.
- Zużycie energii (pytanie o energię): nie sprawdzono w tej rundzie; patrz `/Users/admin/so101_fly_project/flymind/reports/robot_ai_revolution_20261112.md`.

## AGI — definicje, miary, stan (8)

### Takeaway
Nie ma jednej definicji AGI; trzy główne to skala poziomów DeepMind (wydajność × ogólność), definicja ekonomiczna OpenAI i definicja Chollet'a przez efektywne uczenie nowych zadań (ARC). Na ARC-AGI-2 czołowe modele są w 2026 prawdopodobnie na poziomie 90%+, natomiast na interaktywnym ARC-AGI-3 (marzec 2026) modele-LLM miały poniżej 1%, a najlepszy zgłoszony wynik w lipcu to 7,8%.

### Cited Findings
- DeepMind „Levels of AGI" (Morris i in., ICML 2024; arXiv v1 4 XI 2023): poziomy wydajności 0–5 (brak AI, Emerging, Competent, Expert, Virtuoso, Superhuman), osobno ogólność i 6 poziomów autonomii — VERIFIED jako istnienie i struktura przez wyszukiwanie, nazwy poziomów REPORTED; przykład AlphaFold/Stockfish na poziomie 5 według prasy, nie sprawdzono — [arXiv 2311.02462](https://arxiv.org/abs/2311.02462), [techxplore](https://techxplore.com/news/2023-11-consensus-constitutes-artificial-general-intelligence.amp)
- OpenAI: Karta z kwietnia 2018: AGI = „wysoce autonomiczne systemy, które przewyższają ludzi w większości pracy o wartości ekonomicznej"; pięć poziomów (Chatboty, Reasoners, Agenci, Innowatorzy, Organizacje), zaprezentowane wewnętrznie w VII 2024; Altman w I 2025 nazwał AGI „bardzo niechlujnym terminem" — REPORTED (wtórne) — [the-decoder](https://the-decoder.com/openai-unveils-five-level-ai-scale-aims-to-reach-level-2-soon/), [enlightenedspectator](https://enlightenedspectator.substack.com/p/artificial-general-intelligence-the)
- Chollet / ARC: ARC-AGI-3 to „interaktywny benchmark rozumowania": agenci eksplorują nowe środowiska, zdobywają cele w locie, budują modele świata, uczą się ciągle; 100% = pokonanie wszystkich gier równie efektywnie jak ludzie; wyniki ARC Prize 2026 mają być ogłoszone 4 XII 2026 — VERIFIED — [arcprize.org/arc-agi/3](https://arcprize.org/arc-agi/3)
- ARC-AGI-3 wyniki: wydany pod koniec III 2026; 135 środowisk, każde rozwiązane przez co najmniej dwie osoby bez przygotowania; GPT-5.5 0,43% (koszt ok. 10 000 USD), Opus 4.7 0,18% (analiza z 2 V 2026) — VERIFIED — [the-decoder](https://the-decoder.com/even-the-latest-ai-models-make-three-systematic-reasoning-errors-arc-agi-3-analysis-shows/). Premiera: Gemini 3.1 Pro 0,37%, GPT-5.4 0,26%, Opus 4.6 0,25%, Grok 4.2 0%; najlepszy agent w podglądzie 12,58% (wyspecjalizowany, nie LLM); snapshot BenchLM z 23 VII 2026: GPT-5.6 Sol 7,8% — REPORTED — [eweek](https://www.eweek.com/news/ai-test-reality-check-neuron/), [benchlm](https://www.benchlm.ai/benchmarks/arcAgi3). Krytycy kwestionują metodę punktacji; Chollet: modele radzą sobie, gdy ludzie budują wokół nich rusztowanie — REPORTED (eweek).
- ARC-AGI-2 (ARC Prize 2025, zbiór prywatny): NVARC 24,03% (ok. 0,20 USD/zadanie), ARChitects 16,53%, MindsAI 12,64%; najlepszy zweryfikowany model komercyjny na koniec 2025: Claude Opus 4.5 (Thinking) 37,6% (ok. 2,20 USD/zadanie); Poetiq z pętlą doskonalenia na Gemini 3 Pro ok. 54% (ok. 30 USD/zadanie, wobec 31% bez pętli); Tiny Recursive Model 7M parametrów ok. 8% — VERIFIED — [arcprize.org/blog/arc-prize-2025-results-analysis](https://arcprize.org/blog/arc-prize-2025-results-analysis). Konkurs: 26 III–3 XI 2025, 1455 zespołów — REPORTED — wyszukiwanie, [arXiv 2601.10904](https://arxiv.org/abs/2601.10904)
- ARC-AGI-2 w 2026 wg agregatora BenchLM (6 XI 2026): czołowy model ok. 95%, dalsze 94,2% i 93,3%; w lipcu/sierpniu 92,5% (wg jednego źródła zweryfikowane przez ARC Prize na zbiorze półprywatnym) — REPORTED, nie potwierdzono na arcprize.org, nazwy modeli nieznane mi z innych źródeł — [benchlm.ai/benchmarks/arc-agi-2](https://benchlm.ai/benchmarks/arc-agi-2)
- Zadania AI-R&D: DeepMind GCI v1 (123 modele, 92 benchmarki) i RE-Bench: Argon rozwiązuje ok. połowy z 74 zadań ML, Gemini 3.7 Flash 27% — VERIFIED (relacja the-decoder) — [the-decoder](https://the-decoder.com/google-says-self-improving-ai-isnt-anywhere-close/)
- METR: horyzont czasowy zadań podwajał się co ok. 7 mies. historycznie; po aktualizacji I 2026 od 2023 r. ok. 129–131 dni (przedział 105–157) — REPORTED (wtórne, LessWrong/Medium) — [lesswrong](https://www.lesswrong.com/posts/GAJbegsvnd85hX3eS/thoughts-on-extrapolating-time-horizons)

### Inferences
- Rozbieżność główna: czy AGI to ogólność umiejętności (DeepMind), praca gospodarcza (OpenAI), czy efektywność uczenia nowego (Chollet). Przy tej samej dacie jeden benchmark (ARC-AGI-2) wygląda na prawie nasycony, a drugi (ARC-AGI-3) prawie zerowy — stąd spór „AGI jest" kontra „daleko". INFERRED
- Żaden z tych benchmarków nie mierzy robota w ciele; wszystkie wyniki to tekst/gry — INFERRED.
- Modele o nazwach „GPT-6", „Claude Opus 5.5", „Gemini 4 Argon" pojawiają się tylko w źródłach wtórnych; nie weryfikowałem ich wydania. Należy je podawać jako „według wtórnych źródeł".

### Gaps
- Brak potwierdzenia liczb ARC-AGI-2/3 z listopada 2026 na arcprize.org (strona ARC-AGI-3 nie podała liczb). Brak numeru bazowego ludzi dla ARC-AGI-2 w otwartych źródłach.
- Nie otwarto pierwotnej strony OpenAI ani samego artykułu DeepMind (nazwy poziomów z wyszukiwania).

## Dlaczego to trudne (część pytania 9)

### Takeaway
Trudność to: mało danych o ciele (rząd 10⁴ h vs 10⁹ h tekstu), niezawodność w otwartym świecie, długie zadania i słaba ocena, a nie samo „za mały model".

### Cited Findings
- Dane robotów rzędu 10⁴–10⁵ h wobec miliardów godzin tekstu/wideo — REPORTED, rząd wielkości (zob. wyżej: Peike Li, Berkeley, Bessemer w wyszukiwaniu) — [sebastiansartor](https://sebastiansartor.substack.com/p/scaling-laws-in-robotics)
- Teleoperacja jest ograniczona fizyką (24 h/dobę, człowiek nadzoruje); obejścia: symulacja, wideo; pipeline NVIDIA GR00T: 6500 h w świecie rzeczywistym z małego zbioru demonstracji, kompresja 591× — REPORTED (wtórne) — [pulse.bot/diginomica](https://diginomica.com/robot-futures-1-why-your-dirty-socks-are-preventing-future)
- Niezawodność: zob. test Penn dla π0 (VERIFIED w poprzednim raporcie) oraz wcześniej zacytowane >90% epizodów ewaluacji Gemini Robotics 1.5 w symulacji (arXiv 2510.03342) — z `robot_ai_revolution_20261112.md`.
- „Najczęściej brak dotyku/siły w pętli" — arXiv 2504.11827 (z poprzedniego raportu).

### Inferences
- Pasuje do FlyMind: nasz robot to jeden SO-101, jedna kamera FaceTime, dotyk tylko w symulacji — czyli bardzo daleko od skali danych tych systemów. INFERRED

### Gaps
- Energia: brak liczb w tej rundzie.

## Czy AI może sama się ulepszać (9)

### Takeaway
Tak, w wąskim sensie: AlphaEvolve (Google) znajduje lepsze algorytmy i przyspieszył własne trenowanie o ok. 1%, Darwin Gödel Machine podniósł wynik agenta kodującego z 20% na 50% (SWE-bench). Ale to ulepszanie wąskie, z weryfikatorem, drogie i z człowiekiem w pętli. W październiku 2026 sam DeepMind raportował brak mierzalnego przyspieszenia badań AI; METR (5 XI 2026) szacuje ok. 2× w Anthropic z szerokim przedziałem 1,3–3×.

### Cited Findings
- AlphaEvolve (DeepMind, V 2025): agent kodujący Gemini + automatyczne ewaluatory; Borg: ok. 0,7% mocy obliczeniowej Google odzyskane, działa w produkcji ponad rok; jądro mnożenia macierzy o 23% szybsze → ok. 1% krótsze trenowanie Gemini; FlashAttention do 32,5% szybciej; mnożenie 4×4 zespolone w 48 mnożeniach (lepiej niż Strassen 1969); >50 problemów matematycznych: dorównał stanowi wiedzy w ok. 75%, poprawił w ok. 20%; liczba kontaktowa 593 w 11 wymiarach — VERIFIED (blog DeepMind, wersja czytana przez narzędzie; data publikacji V 2025 z wiedzy własnej, nie z tej strony) — [deepmind.google blog](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- Retrospektywa roczna AlphaEvolve (7 V 2026): wdrożenia w genomice, sieciach energetycznych (wykonalność ACOPF z 14% do >88% wg jednego źródła), Google Cloud w wczesnym dostępie; matematycy nadal muszą weryfikować wyniki — REPORTED, tylko agregatory, nie otwarto posta DeepMind — [gigazine](https://www.gigazine.net/gsc_news/en/20260508-google-deepmind-alphaevolve), [signal-and-syntax](https://signal-and-syntax.pages.dev/updates/deepmind-alphaevolve-gemini-coding-agent-impact-acopf-deepconsensus/), [implicator](https://www.implicator.ai/deepminds-alphaevolve-scales-mathematical-search-proofs-still-need-people.md)
- Darwin Gödel Machine (Sakana + UBC, V 2025): agent przepisuje własny kod, archiwum agentów; SWE-bench 20,0% → 50,0%, Polyglot 14,2% → 30,7% — VERIFIED (abstrakt) — [arXiv 2505.22954](https://arxiv.org/abs/2505.22954). Koszt jednego 80-iteracyjnego przebiegu ok. 2 tygodnie i ok. 22 000 USD; brak testów istotności; ok. 50% to tuż pod najlepszym otwartym agentem (51%) — REPORTED — [sakana.ai/dgm](https://sakana.ai/dgm/), [the-decoder](https://the-decoder.com/sakana-ais-darwin-godel-machine-evolves-by-rewriting-its-own-code-to-boost-performance/)
- AlphaProof/AlphaGeometry 2 (IMO 2024): 4 z 6 zadań, 28 pkt = srebro; Gemini Deep Think (IMO 2025): 5 z 6, 35/42 pkt = złoto, w języku naturalnym w 4,5 h; OpenAI też 35 pkt — REPORTED (wtórne; blog DeepMind w wynikach wyszukiwania, nie otwarty) — [deepmind.google blog IMO 2025](https://deepmind.google/blog/advanced-version-of-gemini-with-deep-think-officially-achieves-gold-medal-standard-at-the-international-mathematical-olympiad/), [9to5google](https://9to5google.com/2025/07/21/gemini-deep-think-math-imo-2025/)
- DeepMind, raport wewnętrzny (14 X 2026, wg relacji): brak mierzalnego przyspieszenia badań AI wywołanego przez AI; AI pisze >75% kodu produkcyjnego, ale ok. 88% zmian wymaga nadzoru, każda zmiana jest przeglądana przez człowieka; udział zmian w pełni zleconych AI wzrósł z 7,5% do 11,9%; GCI rośnie ok. 0,1 pkt/mies. bez zmiany tempa; ryzyko automatyzacji badań AI oceniono jako niskie — VERIFIED jako treść relacji the-decoder, NIE jako treść raportu (Gemini 4 safety report, str. 75, nieotwarty) — [the-decoder](https://the-decoder.com/google-says-self-improving-ai-isnt-anywhere-close/). Pichai: pełna autonomiczna samopoprawa daleko, ale spodziewa przyspieszenia w 12 mies.; Brin: „zaczynamy wchodzić na bieżnię RSI" — REPORTED — [benzinga](https://www.benzinga.com/markets/prediction-markets/26/10/62525802/google-self-improving-ai-rsi-pichai), [cryptobriefing](https://cryptobriefing.com/googles-pichai-says-ai-self-improvement-still-in-early-stages/)
- METR (okres 12 VIII–29 X 2026, raport 5 XI 2026): Anthropic poprawia możliwości na dobrze zdefiniowanych zadaniach ok. 2× szybciej niż w III 2024–X 2025 (przedział 1,3–3×; wskaźnik AECI ok. 1,9×, CI 1,5–2,8×); większość przypisana AI w badaniach, głównie asysta, nie autonomia; nie przez szybsze skalowanie obliczeń; część kluczowych dowodów zredagowano; sam raport METR nie otwarty — REPORTED (wpis LessWrong) — [lesswrong](https://lesswrong.com/posts/N5AmYkRks5CqAxvBg/metr-independent-assessment-of-ai-r-and-d-acceleration-at)
- Ponad 20 badaczy (m.in. Hinton, Bengio, Pachocki) ostrzega przed „eksplozją inteligencji" w pracy naukowej; argumentują, że AI może zautomatyzować całość badań AI w ciągu kilku lat — REPORTED (the-decoder, ten sam artykuł)

### Inferences
- „To, co widział Adam od Google": najprawdopodobniej (a) AlphaEvolve (dwukrotnie głośny: V 2025 i retrospektywa V 2026) lub (b) komentarze z 14 X 2026 (raport o braku przyspieszenia, Pichai, Brin „RSI treadmill"). Nie ma sposobu, by to rozstrzygnąć z tekstu zadania; trzeba zapytać Adama — INFERRED.
- Uczciwy obraz: rzeczywiste, ale wąskie samopoprawianie (kod, algorytmy, kernel) z weryfikatorem i człowiekiem w pętli; ok. 1% oszczędności treningu i ok. 2× u Anthropic to nie „eksplozja". Dwa źródła (DeepMind: brak przyspieszenia; METR: ok. 2× w Anthropic) różnią się metodą i laboratorium, więc nie należy ich uśredniać — INFERRED.
- Dla FlyMind: żadne z tych nie dotyczy fizycznego robota; self-improvement w sieciach z konektomu nie istnieje w naszym projekcie. Nie sugerować przeciwnego.

### Gaps
- Nie otwarto: post DeepMind z 7 V 2026, raport Gemini 4 Argon, raport METR; „Gemini 4 Argon", „Gemini 3.7 Flash" znane tylko z relacji the-decoder.
- AlphaZero/self-play: nie przeszukane w tej rundzie. Inne systemy (AI Scientist, STOP, Absolute Zero) nie sprawdzone.
