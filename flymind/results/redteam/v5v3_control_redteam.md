# Red Team: kontrola SHUF_WITHIN_SIDE (V5 v3) — czy izoluje „topologię” od „lateralizacji”?

Data: 2026-10-29. Zakres: `flymind/side_shuffle.py`, `flymind/test_side_shuffle.py`, `flymind/results/v5v3_prep/v5v3_control_check_20261029T161803.json`,
`visual_path.network(0.2)` (424 neurony, 13 510 krawędzi, LC10a 135 L / 140 R, 147 pośrednich, DNa02 L/R).
Nie zmieniono żadnego pliku repozytorium poza tym raportem; nie importowano `bio2`; żadnej pętli zamkniętej / MuJoCo.
Skrypty i surowe wyniki: `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam3/` (a0–a16, `*.json`, `*.out`, `*.npy`).
Ziarna: tasowania SWS 1401–1409 (1410 nie ukończone — proces zabity z powodu głodzenia CPU), SHUF_STR 1411–1413, tasowanie warstwa×strona 1431–1432, test mieszania 1421, ALIF 1001–1020. Żadne z ziaren z zakazanych pul.
Konwencja: „DATA” = sieć z danych; „SWS” = SHUF_WITHIN_SIDE; „STR” = SHUF_STR; „LSS” = moja dodatkowa kontrola warstwa×strona (patrz niżej).
Wszystkie liczby poniżej wyliczone w sesji (komendy w §6); nic nie jest przepisane z pamięci.

## 0. Werdykt

**SWS jest poprawnie zaimplementowaną i ściślejszą od SHUF_STR kontrolą „bloku strona×strona”, ale NIE jest kontrolą, która izoluje „topologię ponad lateralizację” w sensie przyczynowym.**
Różnica DATA − SWS zawiera co najmniej cztery składniki, z których tylko jeden jest „tożsamością partnerów wśród neuronów tej samej strony”:

1. **Rekurencja LC10a×LC10a (zlokalizowana, rozstrzygnięta eksperymentem).** Cały deficyt czułości przy słabym napędzie siedzi w bloku LC10a→LC10a: DATA z samym blokiem LC×LC wziętym z tasowania warstwa×strona zachowuje się jak SWS; sieć tasowana warstwa×strona z przywróconym blokiem LC×LC z DATA zachowuje się jak DATA (§4). To jest topologia, ale to nie jest topologia ścieżki wzrokowo-motorycznej LC→AOTU→DNa02 i nie ma nic wspólnego z DNa02 ani lateralizacją.
2. **Zmiana architektury warstw.** SWS tworzy 78–95 bezpośrednich krawędzi LC10a→DNa02 (w DATA 0), zmniejsza MID→DNa02 z 151 do 56–73, zwiększa MID→LC z 310 do 1020–1056 (§3).
3. **Utrata 17–29% ipsilateralnej masy ścieżek 2-skokowych** (kontralateralna −1,2…−3,9%) — asymetria E/I, której „indeks lateralizacji 0,84–0,91” nie widzi (§3, §4).
4. **Szkielet 6 krawędzi nigdy nie ruszony** (AOTU019 ×2, AOTU025 ×2, AOTU012 ×2 → DNa02; 75,7% masy ścieżek 2-skokowych), bo mają unikalny klucz (waga, strona, strona) (§5). Zachowana „lateralizacja” jest więc w dużej mierze zagwarantowana konstrukcją, a wynik zerowy DATA ≈ SWS byłby nieinterpretowalny.

Poprawne, ograniczone sformułowanie wniosku (to, co SWS faktycznie pozwala powiedzieć):
„Przewaga DATA nad SWS nie wynika z (a) stopni/sił we-wy, (b) składu stron partnerów, (c) bloku somaSide×somaSide, (d) 6 dominujących krawędzi do DNa02 — wszystkie zachowane — a w tej sieci przy jednorodnym napędzie na stronę jest zlokalizowana w rekurencyjnym bloku LC10a×LC10a.”
Nie wolno pisać „topologia (tożsamość partnerów) ponad lateralizację”, ani interpretować DATA ≈ SWS jako „topologia nieistotna”.

Co zostaje obalone, a co nie (skrót): obalone — (i) „deficyt = resztkowa utrata lateralizacji” (LSS ma identyczny wskaźnik lateralizacji i ten sam deficyt); (ii) „SWS zmienia tylko tożsamość partnerów” (warstwy, wzajemność, widmo); (iii) „10–15% utraty LI to nieistotny konfound” w sensie masy ipsi (−17…−29%). Nie obalone — (iv) poprawność implementacji tasowania (14 deklarowanych niezmienników spełnionych na 9 instancjach; dodatkowo zachowany jest per-neuron multizbiór wag we/wy — niezadeklarowany w `properties()`); (v) mieszanie (10 zamian/krawędź to nadmiar).

## 1. Tabela twierdzeń

| # | Twierdzenie | Dowód (źródło) | Alternatywne wyjaśnienie | Test obalający | Wynik |
|---|---|---|---|---|---|
| T1 | SWS zachowuje stopnie, siły we/wy, prawo Dale'a, zbiór wag, skład stron partnerów, blok strona×strona | `side_shuffle.py:31-68`, `properties` `:81-103`, `test_side_shuffle.py` | `properties()` nie sprawdza reguły „równa waga” per krawędź; tożsamość/identyczność przechodzi; etykiety poza L/R/U niewidoczne | Syntetyczne sieci A–I (a1.py) + sprawdzenie multizbiorów wag per neuron na 9 instancjach (a4.py) | **Częściowo potwierdzone.** Wynik tasowania spełnia wszystkie 14 niezmienników + (niezadeklarowane) multizbiory wag per neuron (`inw_multiset_same=True`, `outw_multiset_same=True`, 9/9). Ale `properties()` zwraca True dla (A) permutacji wag na tym samym zbiorze krawędzi i (B) tożsamości, (C) dla przestawienia podpisanych wag E/I między stronami (§2) — to słaby detektor, nie błąd tasowania |
| T2 | SWS zachowuje lateralizację ścieżek ≤2 skoki (LI 0,84–0,91 DATA) i funkcjonalną (ipsi ~221 Hz, kontra 0) | v5v3_control_check JSON | Zachowanie wynika z 6 nigdy nie ruszanych krawędzi (grupy rozmiaru 1) | Koncentracja masy ścieżek + `bb_out_to_DN_kept` (a6.py, a12.py) | **Potwierdzone, ale trywialnie.** 6 krawędzi mid→DNa02 niesie 75,7% masy |ścieżek| 2-skokowych (AOTU019 pary: 49,3%), 100% z nich pozostaje na miejscu w 9/9 instancjach. Kontra = 0 jest gwarantowane przez nieruszone hamowanie AOTU019→DNa02 (waga −59,4/−57,8) |
| T3 | SWS niszczy tylko „tożsamość partnerów” (topologię), nie inne własności | nagłówek `side_shuffle.py:1-13` („NIE zachowane: tożsamość partnerów, struktura typów, ścieżki wieloskokowe”) | Zmienia też architekturę warstw, wzajemność, widmo | Spis blok-warstwa, pary wzajemne, widmo W (a3.py, a4.py) | **OBALONE.** LC→DN 0→78–95 krawędzi; MID→DN 151→56–73; MID→LC 310→1020–1056; MID→MID 2089→1432–1464; pary wzajemne 3301→795–873 (LC–LC: 2450→383–460); pośrednie z wyjściem do DNa02 147→55–70; max Re λ(W) 26,07→34,07–36,27 (+31…+39%) |
| T4 | Utrata czułości przy słabym napędzie (DATA 33 Hz vs SWS 0–4 Hz przy 0,5·g) to efekt topologii, nie resztkowej lateralizacji | v5v3 JSON, g0.5 | Resztkowy ubytek LI (10–15%) / masy ipsi (17–29%) działa jak mała zmiana wzmocnienia na stromej krzywej | (i) krzywa odpowiedzi amp 0,44–0,58, 5 ziaren×2 strony; (ii) korelacja LI↔odpowiedź między 9 instancjami; (iii) kontrola LSS o identycznym LI; (iv) DATA z osłabionym wejściem pobudzającym DNa02; (v) rozkład blokowy LC×LC (a5, a10, a13, a14, a16) | **Hipoteza „LI-skalar” obalona, hipoteza „topologia ścieżki” też niepotwierdzona.** LSS: LI = 100% DATA (z konstrukcji), a deficyt identyczny z SWS. Deficyt = blok LC×LC (przywrócenie go → DATA; samo jego tasowanie w DATA → SWS). Korelacja LI↔odpowiedź w SWS: Spearman −0,29…+0,42, p 0,26…0,45 (n=9; zakres LI tylko 0,84–0,91 — test o mocy bliskiej zeru) |
| T5 | „Strona” = somaSide to właściwa strona do zachowania lateralizacji | `side_labels` `:23-28`, nagłówek `:6-8` | 25/147 pośrednich ma somę po stronie wejścia, a wyjście do przeciwległego DNa02 | Rozkład wejścia/wyjścia wg strony somy (a2.py) | **Częściowo obalone dla interpretacji, nieszkodliwe dla bloków.** LC10a→pośrednie: 13 812,4 vs 0,8 (dodatnia/ujemna masa wag) po stronie somy — soma = strona wyjścia wejścia. Ale 25 pośrednich (17%) ma wejście z tej samej strony somy a wyjście głównie do DNa02 po drugiej stronie; niosą 99,99% znakowanej masy kontralateralnej (−151 425 z −151 426) i 54% masy bezwzględnej ścieżek 2-skokowych. „Strona somy” ≠ „strona działania” |
| T6 | 10 zamian/krawędź wystarcza do wymieszania | `n_swaps_per_edge=10` `:31` | Mała liczba zamian = nadmierne podobieństwo do DATA | Nakładanie krawędzi z DATA przy 2, 5, 10 zamianach/krawędź (a7.py, a4.py) | **Potwierdzone.** Zachowane krawędzie: 28,5% (2/kraw.), 28,5% (5/kraw.), 27,4–28,4% (10/kraw., 9 inst.) — plateau po 2 zamianach. n=20 nie uruchomione (patrz §6.6, ograniczenia) |
| T7 | „Ta sama strona” jest dobrze określona dla pojedynczych DNa02 i dla enkodera | `loop.py:110`, `encoder.py:72-75` | Enkoder daje identyczny prąd wszystkim LC10a danej strony, więc tożsamość LC10a jest dla pętli niewidzialna; 2 neurony wyjściowe = brak uśredniania | Analiza + a14 | **Ograniczenie istotne.** Przy jednorodnym napędzie permutacje „który LC10a łączy się z którym pośrednim” są niewykrywalne poza sumą wejść LC na pośredni (zachowaną w LSS: LI i E identyczne z DATA). Jedyny dynamiczny skutek tasowania w bloku LC→LC/LC→mid to rekurencja LC×LC. Szczegóły §7 |

## 2. Poprawność `shuffle_within_side` i `properties()` (zadanie 1)

Kod `shuffle_within_side` (`side_shuffle.py:31-68`) jest poprawny: każda zamiana (a→b, c→d)→(a→d, c→b) zachowuje (waga, strona_pre, strona_post) obu krawędzi, zbiór `exists` jest aktualizowany, autapse i duplikaty odrzucane, deterministyczne po ziarnie. Dodatkowo (niezadeklarowane) zachowuje multizbiór wag wejściowych każdego neuronu i multizbiór wag wyjściowych każdego neuronu — sprawdziłem bezpośrednio (a4.py, `inw_multiset_same`, `outw_multiset_same`: True, 9/9 SWS; True też dla STR i LSS).

Syntetyczne przypadki przeciwne (a1.py, wynik wydrukowany):

| Przypadek | Co robi W1 | `properties()` | Komentarz |
|---|---|---|---|
| A | te same krawędzie, wagi przestawione ({1,3}↔{3,1}) — łamie regułę „równa waga per krawędź” | **wszystkie 14 True**, `changed_edges=0` | `properties()` nie widzi per-krawędziowych wag; `weight_multiset`, siły i stopnie zagregowane |
| B | tożsamość (brak tasowania) | **wszystkie True**, `changed_edges=0` | detekcja „nic się nie stało” tylko przez `changed_edges` (test sprawdza `>0`, `test_side_shuffle.py:63` `changed_frac>0.5` — tylko na 3 ziarnach) |
| C | po stronie L: {+2,−1}, po R: {+1,−2} na pośrednim → po L: {+1,−2}, po R: {+2,−1} (zachowane: stopnie, wartości bezwzględne po stronach, suma podpisana, blok) | **wszystkie True**, `changed_edges=0` | `in_strength`/`out_strength` używają sum podpisanych (`:95`), skład stron — wartości bezwzględnych (`:85`): skład E/I per strona niewidoczny |
| F | zamiana między-stronowa L→L,R→R ⇒ L→R,R→L | wykryte: `pre_side_composition`, `post_side_composition`, `side_block` | OK |
| G | dwie wzajemnie kompensujące zamiany między-stronowe (liczby w blokach równe) | wykryte przez `pre/post_side_composition` (nie przez `side_block`) | skład per-neuron jest niezbędny |
| H | prawdziwy SWS na losowej sieci 40 neuronów | wszystkie True | OK |
| I | prawdziwy SWS + jedna dodatkowa zamiana międzystronowa | wykryte | OK |

Nie udało mi się skonstruować przypadku, w którym wyjście `shuffle_within_side` łamie deklarowany niezmiennik, a `properties()` zwraca True — natomiast `properties()` jako niezależny detektor jest słabszy niż deklaracja w nagłówku (A, B, C). Etykiety spoza {L,R,U} są pomijane w kontrolach składu (`:85`, `:88` stała `"LRU"`); nie zademonstrowałem fałszywego True (blokada: `side_block` używa realnych etykiet), więc to „code smell”.

## 3. Ukryte zmiany własności (zadanie 3)

Spis krawędzi wg warstw (LC = LC10a, MID = 147 pośrednich, DN = DNa02), liczba krawędzi (a3.py/a4.py):

| Blok | DATA | SWS (9 inst.) | STR (3 inst.) | LSS (2 inst.) |
|---|---|---|---|---|
| LC→LC | 6189 | 5438–5471 | 5275–5317 | 6189 |
| LC→MID | 4750 | 5383–5419 | 5515–5557 | 4750 |
| MID→LC | 310 | 1020–1056 | 1170–1212 | 310 |
| MID→MID | 2089 | 1432–1464 | 1294–1336 | 2089 |
| LC→DN (bezpośrednie) | **0** | **78–95** (ipsi, |w| łącznie 349–492 mV) | 107–108 | 0 |
| MID→DN | 151 | 56–73 | 43–44 | 151 |
| DN→MID / DN→LC | 21 / 0 | 9–16 / 5–12 | 6–9 / 12–15 | 21 / 0 |

Dalsze własności (a4.py; DATA | SWS min–max (średnia) | STR | LSS):
- pary wzajemne (reciprocal): 3301 | 795–873 (823) | 420–465 | 867–916; w tym LC–LC: 2450 | 383–460 (419) | 183–211 | 538–567.
- promień widmowy ρ(W) (podpisana W): 32,54 | 34,07–36,27 (35,06) | 18,76–22,17 | 31,49–31,78.
- największa część rzeczywista λ: 26,07 | 34,07–36,27 (35,06; wiodąca wartość własna staje się rzeczywista dodatnia) | 15,62–22,06 | 26,55–26,71 (+34% w SWS).
- ρ(|W|): 42,92 | 43,56–45,52 (44,29) | 43,0–44,0 | 41,43–41,73.
- pośrednie z wejściem LC i wyjściem do DNa02: 147 | 55–70 (61) | 37–40 | 147.
- liczba odrębnych ścieżek 2-skokowych LC→x→DN: 4918 | 4719–5109 | 4381–4552 | 4918 (zbieżność liczbowa niezmieniona; zmienia się ich waga).
- masa 2-skokowa |W|²: 338 097 | 284 719–305 558 | 285 102–295 287 | 338 097.
- E_ipsi (ΣW²+W, ipsi): 156 010 | 111 378–129 678 (−17…−29%) | 2 547–23 260 | 156 010; E_kontra: −151 426 | −145 553…−149 592 (−1,2…−3,9%) | −47 300…−57 063 | −151 426.

Wniosek: SWS jest „kontrolą mieszaną”. Zmienia (i) rolę warstw (powstają krawędzie LC→DN i MID→LC, a MID→DN zanika), (ii) wzajemność, (iii) widmo W (+34% w wiodącej wartości własnej — to jest zmiana wzmocnienia dynamicznego), (iv) asymetrię E/I (ipsi pobudzająca masa −17…−29%, kontra hamująca ≈ stała). Dlatego „LI 0,84–0,91” jest wskaźnikiem zbyt grubym: nie widzi, że obrona przed „utratą lateralizacji” polega na tym, że hamowanie kontra jest nieruszone, a pobudzenie ipsi osłabione.
Rozwiązanie wykorzystujące to samo narzędzie: `shuffle_within_side(spec, etykiety_warstwa_strona, seed)` przyjmuje dowolne etykiety (klucz grup `:43`), więc kontrolę warstwa×strona (LSS) można otrzymać bez zmiany kodu (a9.py). W LSS: spis warstw identyczny z DATA, wejście DNa02 zamrożone (zachowane 100%), LI i E_ipsi/E_kontra identyczne z DATA (wejście LC na pośredni jest zachowane co do wagi), ρ(W) i λ_max ≈ DATA.

## 4. Czy 10–15% utraty LI wyjaśnia utratę czułości? (zadanie 4)

Test rozstrzygający (open-loop ALIF, 300 ms, szum 2 mV, 12 mV·amp na LC10a strony, ziarna 1001–1020; ocena: średnia rate DNa02 ipsi przez 2 strony × 5 ziaren; a5/a10/a13/a14/a16).

Krzywa odpowiedzi (Hz) DATA, ziarna 1001–1005: 0,44→0; 0,46→0; 0,48→2,3; 0,50→24,7; 0,52→31,7; 0,54→59,7; 0,56→65,3; 0,58→91,3.
Szum DATA przy tych samych krzywych (kolejne niezależne zestawy ziaren 1006–1010 / 1011–1015 / 1016–1020): r(0,50) = 8,0 / 18,3 / 16,3 Hz; amplituda dla 60 Hz: 0,5392 / 0,5455 / 0,5386 (oraz 0,5412 dla 1001–1005) → średnia 0,5411, SD 0,0031. Oryginalne „33 Hz” z 3 ziaren leży więc w górnej części szumu (średnia 4 zestawów r(0,50) = 16,8 Hz, SD ≈ 7 Hz).
SWS (9 instancji, ziarna 1001–1005): r(0,50) = 0,0–2,7 Hz we wszystkich 9; amplituda dla 33,3 Hz: 0,5213–0,5259 (średnia 0,5244, DATA 0,5217 ± szum); amplituda dla 60 Hz: 0,5617–0,5640 (średnia 0,5631; DATA 0,5411) → przesunięcie +4,1% (≈ 7 SD szumu DATA). Wniosek ilościowy: „deficyt przy 0,5·g” to skok na stromej krzywej (33→60 Hz na 0,02 amp); odpowiada przesunięciu krzywej o ~0,3–4% amplitudy, nie rzędowi 10–15%.

Korelacja LI ↔ odpowiedź między instancjami SWS (n = 9, LI 0,842–0,908): Spearman LI vs amp@33 = +0,42 (p=0,26), vs amp@60 = −0,29 (p=0,45), vs r(0,50) = +0,49 (p=0,19), vs r(0,52) = −0,41 (p=0,28), vs r(0,54) = −0,03 (p=0,95). Brak zależności; zakres LI jest zbyt wąski, a poziom odpowiedzi w SWS — dla r(0,50) — przy podłodze (0–2,7 Hz), więc ten test nie ma mocy i **nie może** obalić hipotezy konfoundu; zostawiam go jako negatywny wynik.

Silniejsze testy (manipulacja, nie korelacja):
- **LSS (warstwa×strona), 2 instancje:** LI i E_ipsi/E_kontra = DATA co do bitu (156 010 / −151 426), ale odpowiedź jak SWS: r(0,50) = 3,0 / 3,0 Hz, amp@33 = 0,5274 / 0,5265, amp@60 = 0,5641 / 0,5642. ⇒ utrata LI/E_ipsi **nie** jest przyczyną deficytu.
- **Rozkład blokowy LC×LC (a14):** LSS z blokiem LC×LC przywróconym z DATA: r(0,50) = 22,0 / 20,3 Hz, amp@33 = 0,5214 / 0,5221, amp@60 = 0,5376 / 0,5480 (DATA 0,5411 ± 0,0031) ⇒ odzyskuje DATA. DATA z blokiem LC×LC podstawionym z LSS: r(0,50) = 3,0 / 3,3 Hz, amp@33 = 0,5264 / 0,5257, amp@60 = 0,5633 / 0,5636 ⇒ odtwarza SWS. Deficyt jest więc w całości zlokalizowany w rekurencyjnym podgrafie wejściowej populacji LC10a (2450 par wzajemnych LC–LC w DATA, 383–460 w SWS, 538–567 w LSS).
- **Kontrola „po prostu mniej pobudzenia na DNa02” (a13):** DATA z dodatnimi wagami wejściowymi DNa02 przeskalowanymi ×0,95 / ×0,9 / ×0,8: amp@60 = 0,5429 / 0,5480 / 0,5603, amp@33 = 0,5216 / 0,5221 / 0,5239, r(0,50) = 24,7 / 23,7 / 22,3 Hz. Skalar ×0,8 odtwarza górny zakres przesunięcia SWS (amp@60 0,5603 vs 0,5631), ale **nie** załamanie przy 0,50 (22 Hz vs ≈1 Hz): w SWS brakuje składnika niskoprogowego (0,48–0,50), który ma rekurencja LC×LC.
Zgodne z V5 (`VALIDATION_PLAN.md`: bez krawędzi LC10a→LC10a odpowiedź na najsłabszy bodziec 58%).

Konsekwencja dla wniosku: deficyt przy słabym bodźcu **jest rzeczywisty i strukturalny** (nie jest artefaktem LI), ale jego przyczyna — rekurencja LC10a×LC10a — nie jest ani „topologią zbieżnej ścieżki do DNa02”, ani „lateralizacją”. SWS miesza oba i nic nie rozdziela.

## 5. Krawędzie niezamienialne i szkielet (zadanie 5)

- 157 krawędzi z unikalnym kluczem (waga, strona, strona) = 10,3% masy |w|; zawsze nieruszone. Są to m.in. wszystkie 6 krawędzi o największym udziale w masie ścieżek 2-skokowych do DNa02 (a6.py): AOTU019 R→DNa02 L (w=−59,4; udział 26,7%), AOTU019 L→DNa02 R (−57,8; 22,6%), AOTU025 R→R (+39,2; 8,6%) i L→L (+41,0; 8,0%), AOTU012 L→L (+43,6; 5,1%) i R→R (+32,8; 4,7%) — razem 75,7%; top 20 krawędzi MID→DN = 87,5% (z 151). Dwie krawędzie AOTU019 (hamowanie kontralateralne) niosą 49% masy.
- `bb_out_to_DN_kept` = 1,0 w 9/9 instancjach; wejścia LC na te 6 neuronów: 71–76% zachowanych krawędzi (z 545), siła wejściowa 5130 → 4769–4901 (−4…−7%) (a12.py). Korelacja wejścia-LC na pośredni DATA vs SWS: r = 0,996–0,997; wyjście-do-DNa02 na pośredni: r = 0,85–0,92 (ale tylko 55–70 pośrednich ma wyjście do DNa02 wobec 147).
- Zachowanie krawędzi z DATA wg rozmiaru grupy (a15.py, 9 instancji): grupy rozmiaru 1: 100%; 2: 83,7%; 3–5: 60,1%; 6–20: 22,7%; 21–100: 8,3%; 101–1000: 3,4%; >1000: 5,6% (dla gęstych bloków to głównie przypadkowe nakładanie, zbliżone do gęstości bloku). Krawędzie zachowane we wszystkich 9 instancjach: 317 z 13 510 (17,5% masy |w|). Ważone masą |w| pozostaje 50–52% masy w pierwotnych pozycjach (najsilniejsze 1% krawędzi — 90–96% zachowanych; top 10% — 57–61% zachowanych) mimo `changed_frac` ≈ 0,72; dla porównania STR: 31–33% masy (top 1%: 67–74%).
- 32 grupy (71 krawędzi) o rozmiarze >1, w których wszystkie krawędzie dzielą pre lub post, nigdy się nie ruszą (zamiana odrzucana przez `a == d or c == b`, `:58`), a `swappable_edges=13353` (`:67`) je liczy; faktycznie zamienialnych jest ≤13 282.
- **Skutek:** SWS jest mocno asymetrycznie „twardy” — szkielet ścieżek niosących lateralizację jest nietykalny. To samo, co dobre dla „zachowaj lateralizację”, jest złe dla „testuj topologię”: SWS nie ma mocy do wykrycia roli tożsamości najsilniejszych krawędzi.

## 6. Mieszanie, determinizm, zaprzeczenia (zadanie 6)

- Zachowane krawędzie vs liczba zamian/krawędź (a7.py, ziarno 1421): 2 → 28,5% (masa 53,4%, LI 0,894), 5 → 28,5% (masa 51,7%, LI 0,842), 10 → 27,4–28,4% (9 instancji, masa 49,8–52,1%). Plateau osiągnięte już przy 2 zamianach/krawędź; 10 jest nadmiarem (wpływ na czas: ~55 s/instancja, `rng.choice(len(groups), p=p)` przeliczane w każdej iteracji, `:55`). n=20 nie zostało ukończone (proces zabity — zasoby CPU systemu), ale dane przy 2→5→10 pokazują plateau.
- Akceptacja zamian ≈ 55% (np. 135 100 zamian / 245 501 prób, ziarno 1401); pętla zatrzymuje się po `3*target` próbach bez błędu (`:53`) — przy trudniejszych sieciach (mało zamienialnych par) wynik byłby cicho niedotasowany; `swaps` jest raportowane, ale nie asercjonowane.
- Determinizm: ten sam seed daje identyczne `W_data` (test `test_side_shuffle.py`), nie sprawdzałem ponownie.
- Stacjonarny rozkład: propozycje są symetryczne w obrębie grupy (para równomiernie), więc łańcuch jest zbieżny do równomiernego rozkładu na grafach z tymi ograniczeniami; ale tempo zamian na krawędź ∝ (|g|−1), więc krawędzie z małych grup mieszają się wolniej (83,7% zachowanych w grupach rozmiaru 2).

## 7. Czy „strona” jest dobrze określona? (zadania 2 i 7)

Dane: wszystkie 424 neurony mają somaSide L (194) / R (230), grupa U pusta w tej sieci (`test_side_shuffle.py:54`) — ścieżka U jest przetestowana tylko syntetycznie.
- LC10a→pośrednie: masa 13 812,4 po tej samej stronie somy vs 0,8 po przeciwnej: soma = strona wyjścia dla wejścia. Wszystkie krawędzie LC–LC są ipsi (frakcja 1,0).
- Pośrednie→DNa02: masa bezwzględna 968,8 do DNa02 po stronie somy vs 235,6 do przeciwnej (19,6%). 122 pośrednie „ipsi-ipsi” (ipsi = 155 932, kontra = −1,76), 25 „ipsi-wejście → kontra-wyjście” (ipsi = 78,4, kontra = −151 425): m.in. AOTU019 (2; −166 698 znakowana masa), AOTU001 (7), AOTU002_a/c (9).
- Ścieżki ipsi: 156 011 przez pośrednie o somie po stronie DNa02, −0,64 przez drugą; ścieżki kontra: −151 426 w całości (−151 425,6) przez pośrednie o somie po przeciwnej stronie niż docelowy DNa02.
- Zachowuje to SWS jako blok L→R (liczbowo), ale w bloku L→R wymienialne są także krawędzie pośrednie→pośrednie i LC→pośrednie kontra (masa 0,8), więc blok „kontra” nie jest strukturalnie utożsamiony z „hamowaniem DNa02”. Zachowane jest ono wyłącznie dzięki unikalnym wagom AOTU019 (§5). Synaptyczna strona (region synaps) nie jest dostępna w pliku danych sieci (zgodnie z nagłówkiem `side_shuffle.py:8-10`); tego nie mogłem sprawdzić.
- Enkoder (`encoder.py:72-75`): prąd `i_max·g_s` jest identyczny dla wszystkich LC10a danej strony ⇒ w pętli tożsamość konkretnych LC10a jest niewidoczna; liczy się tylko suma wejść LC na pośredni (LSS ją zachowuje: LI i E identyczne z DATA, odpowiedź zależna od bloku LC×LC) oraz rekurencja LC×LC. 135 vs 140 LC10a to 3,7% różnicy sumy napędu między stronami w DATA i SWS (bez dodatkowego wniosku). DNa02 to pojedyncze neurony na stronę (idx `DNa02_L/R`: 1 + 1): każda instancja SWS daje 2 realizacje wejścia DNa02, nie ma uśredniania w obrębie instancji; zmienność między instancjami (LI 0,842–0,908) jest wysoka względem efektu.

## 8. Lista problemów

### BLOCKER
**B1. Wniosek „SWS izoluje topologię od lateralizacji” nie wynika z konstrukcji ani z danych.** SWS zmienia architekturę warstw (LC→DNa02 0→78–95, MID→DNa02 151→56–73, MID→LC 310→~1040), wzajemność (3301→~823), widmo (λ_max +34%) i masę ipsi (−17…−29%); deficyt czułości jest w całości w bloku LC×LC (§4). `side_shuffle.py:43` (klucz grupy = (waga, strona_pre, strona_post)) nie zawiera warstwy/typu.
Naprawa: (a) dodać do protokołu kontrolę **LSS = `shuffle_within_side(spec, warstwa+"_"+strona, seed)`** (bez zmiany kodu; wynik w §3: spis warstw, LI, E i widmo zachowane, wejście DNa02 zamrożone); (b) dodać `layer_block` i `reciprocal_pairs` do `properties()` jako niezmienniki dla trybu warstwowego; (c) w protokole V5 v3 zdefiniować hipotezę rozkładem: efekt(DATA−LSS) vs efekt(LSS z blokiem LC×LC z DATA − LSS); nie raportować jednej różnicy DATA−SWS jako „topologii”.

### MAJOR
**M1. Szkielet 6 krawędzi nigdy nie jest ruszany** (`:44` grupy rozmiaru 1 odrzucone; `:67` raportuje 13 353 „wymienialnych”). Zachowana „lateralizacja funkcjonalna” (ipsi 221 / kontra 0) jest przez to przesądzona konstrukcją (kontra = 0 z nieruszonego AOTU019 → DNa02 przy −59,4/−57,8). Zerowy wynik DATA ≈ SWS byłby nieinterpretowalny.
Naprawa: raportować moc — frakcję masy |w| i masy ścieżek w krawędziach, które mogą się ruszyć; dodać wariant z binowaniem wag (np. klasy ±10% wagi) i jawne zmienianie siły wejściowej, albo osobną kontrolę „SWS_bb” (szkielet usunięty/permutowany) — nie przetestowane tu.
**M2. `properties()` słabszy niż deklaracja** (`:85`, `:95`): przypadki A, B, C zwracają wszystkie True. Naprawa: dodać sprawdzenie multizbioru wag per neuron i per strona (jak w a4.py: `np.array_equal(np.sort(W0[i][W0[i]!=0]), np.sort(W1[i][W1[i]!=0]))`), siły z `np.abs`, jawnie `changed_edges>0` jako wymaganie; odrzucać etykiety spoza zbioru znanych (`assert set(sides)<=set("LRU")`).
**M3. Porównanie przy jednym poziomie napędu na stromej krzywej** (`v5v3_control_check.py:32-37`, 3 ziarna): przy 0,5·g różnica 33 vs 0–4 Hz to w dużej mierze szum progu (szum DATA: r(0,50) 8–25 Hz między zestawami 5 ziaren, SD ≈ 7 Hz). Naprawa: krzywa amp 0,44–0,58 (krok 0,02) i wskaźniki „amp@33 Hz”, „amp@60 Hz” z ≥15 ziaren (a10/a16.py).
**M4. Soma ≠ strona działania** (§7): 25 z 147 pośrednich wysyła wyjście kontralateralnie względem somy; nośność lateralizacji = 54% masy. Dane tej sieci nie zawierają regionu synaps, więc kontrola nie może odróżnić strony somy od strony arboryzacji. Naprawa: jeśli dostępne — etykieta „strona wyjścia dominującego” z annotacji ROI; w przeciwnym razie ograniczyć twierdzenie do „blok somaSide×somaSide”.
**M5. Hipoteza pętli zamkniętej V5 v3 nie może rozróżnić tożsamości LC10a** (`encoder.py:74-75` jednorodny prąd na stronę): wszystko, co SWS zmienia w bloku LC→mid, jest niewykrywalne poza sumą wejść; jedyny efekt dynamiczny to rekurencja LC×LC. Przy takim enkoderze „topologia” w tej sieci operacyjnie = „LC×LC + szkielet”.

### MINOR
**m1.** `side_shuffle.py:53` — cichy koniec pętli po `3*target` próbach bez błędu; dodać `assert done == target` lub ostrzeżenie w `rep`.
**m2.** `:55` — `rng.choice(len(groups), p=p)` w pętli ⇒ ~55 s/instancja (np. 135 100 zamian, 245 501 prób); wstępnie policzyć `np.cumsum(p)` i `rng.random()`.
**m3.** `:67` — `swappable_edges` liczy 71 krawędzi w 32 grupach, które nigdy się nie ruszą (wszystkie krawędzie grupy dzielą pre lub post).
**m4.** `:85`, `:88` — stała `"LRU"`; grupa U przetestowana tylko syntetycznie (w tej sieci pusta).
**m5.** `test_side_shuffle.py:63` — `changed_frac > 0.5` to jedyny test siły tasowania; nie testuje szkieletu, spisu warstw, wzajemności.
**m6.** `test_side_shuffle.py` weryfikuje tylko `ziarna 1401–1403`; brak testu mieszania (zachowane krawędzie vs liczba zamian).
**m7.** n=20 zamian/krawędź nie uruchomiono (CPU); wynik plateau wywnioskowany z 2/5/10.
**m8.** SWS1410 nie ukończone (9 z 10 instancji); wnioski o korelacji LI↔odpowiedź oparte na n=9.

## 9. Komendy (wszystkie: `/Users/admin/so101_fly_project/.venv/bin/python -I -B <skrypt>`, katalog skryptów: `.../scratchpad/redteam3/`, `sys.path` zawiera `flymind` i katalog skryptów)

- `a0.py` — rozmiary sieci, 157 kluczy unikalnych, 196 wartości wag.
- `a1.py` — syntetyczne przypadki A–I dla `properties()` (nie wymaga sieci).
- `a2.py` — rozkład wejścia/wyjścia wg strony somy, 25 pośrednich ipsi→kontra.
- `a3.py` — spis warstw (SWS 1401–1405; część STR zakończyła się błędem w moim skrypcie — dane STR wzięte z a4.py).
- `gen.py` — generacja SWS 1401–1409 (+ `a11.py` STR 1411–1413, `a9.py` LSS 1431–1432, `a7.py` n_swaps 2/5).
- `a4.py` — widmo, pary wzajemne, spis warstw, zachowane krawędzie, multizbiory wag (wyjście `a4b.json`).
- `a5.py SWS` / `a10.py` / `a16.py` / `a13.py` / `a14.py` — ALIF: krzywe odpowiedzi, szum DATA, skalowanie wejścia DNa02, rozkład bloku LC×LC.
- `a6.py`, `a12.py`, `a15.py` — koncentracja masy ścieżek i szkielet; zachowanie krawędzi wg rozmiaru grupy.
Stan repozytorium: żadnych zmian w kodzie; jedyny nowy plik to ten raport.

## 10. Ograniczenia tego Red Teamu
- Tylko open-loop ALIF 300 ms z jednorodnym napędem na stronę (jak `v5v3_control_check.py`); wynik w pętli zamkniętej (MuJoCo) nie testowany.
- LSS: tylko 2 instancje; SWS: 9 instancji, nie 10; test blokowy LC×LC: 2 instancje LSS, jedno ziarno ALIF (1001–1005).
- Nie rozstrzygam, która właściwość rekurencji LC×LC (wzajemność, korelacja siły we/wy, klasteryzacja) odpowiada za efekt — tylko że siedzi w tym bloku.
- Hipoteza „kontrola SWS z rozmytym szkieletem” (M1) i „etykieta strony wyjścia” (M4) nie sprawdzone — brak danych/ czasu.
