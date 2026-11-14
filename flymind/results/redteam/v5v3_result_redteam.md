# Red Team wyniku FlyMind V5 v3 (r3, ziarna 3051–3100)

Data: 2026-10-29. Rola: niezależny, adwersaryjny przegląd wyniku potwierdzającego. Nic w repozytorium poza tym plikiem nie zostało zmienione.
Skrypty i surowe wyjścia: `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam_v5v3/` (a1–a7.py, gm.py, sws.py, rerun/).
Wszystkie komendy: `/Users/admin/so101_fly_project/.venv/bin/python -I -B <skrypt>` ze `sys.path.insert(0,'/Users/admin/so101_fly_project/flymind')`. Nie importowano bio2.
Użyte ziarna: tylko 3051–3052 (rerun potwierdzający) oraz 1001–1044 (eksploracja). Żadnych 0–39 ani 300–399.

## 0. Werdykt

**PASS_WITH_LIMITATIONS.**
- Protokół wykonano zgodnie z tekstem (sekcja 2), liczby odtworzone własnym kodem (sekcja 3), przebieg odtwarza się co do bitu (sekcja 4).
- Raportowane zdanie „Hipoteza nie została potwierdzona." jest dokładnie tym, co protokół §7 dopuszcza przy decyzji „równoważne".
- Ograniczenia, których nie wolno zgubić w komunikacie:
  1. „Równoważne" dotyczy wyłącznie średniej łącznej po rozkładzie scen V5 v2, przy SESOI 1° — marginesie zbliżonym do całej różnicy DATA vs TOY_RELAY (1,25°).
  2. 17 z 50 par (34 %) to trywialne zera: wszystkie warunki SNN i TOY dają tam ten sam błąd (martwa strefa enkodera).
  3. H2/H3 mieszają topologię, lateralizację i skalę sygnału. Własny test eksploracyjny pokazuje, że skala sygnału tłumaczy mniej więcej połowę efektu H2 (sekcja 7).

## 1. Najsilniejszy kontrargument

„Równoważne w granicach SESOI" mówi tylko tyle, że średnia różnica na jednym, arbitralnym rozkładzie scen (ρ ~ U[0,16; 0,35] m) leży w ±1°. Nie mówi, że wzorzec połączeń wewnątrz bloków warstwa×strona nie ma znaczenia. Powody:
- **Margines jest hojny.** Najmniejszy symetryczny margines, przy którym CI90 mieściłoby się w nim, to ok. 0,52° (max|CI90| = 0,51–0,52). SESOI = 1° to prawie dwukrotnie więcej. Pełna różnica DATA − TOY_RELAY (przekaźnik zabawkowy, 2 neurony) wynosi 1,25°, a więc tylko trochę ponad SESOI. Test „równoważności" nie odróżniłby więc pełnej connectome-sieci od bardzo prostej, jeśli różnica DATA–TOY byłaby o 20 % mniejsza.
- **Efekt na poziomie próby nie jest zerowy.** |d| > 1° w 13/50 par (26 %: 8 na korzyść DATA, 5 na korzyść kontroli). Średnia |d| = 0,78° (wszystkie), 1,18° (33 pary niezerowe). Równoważność dotyczy średniej, nie zachowania w pojedynczej próbie.
- **Warstwy mają przeciwne znaki** (+0,53 / −1,02 / −0,47) i mechanizm przewidziany w §1 protokołu (znak zależy od napędu g) czyni to wiarygodnym. Pooled ≈ 0 może być częściowo kancelacją. Patrz sekcja 5 — to jednak nie jest dobrze potwierdzone.
- **Kontrola zachowuje niemal wszystko, co ważne dla dynamiki** (stopnie, multizbiory wag per neuron, skład grup partnerów, lateralizacja 1,0000 × DATA, wejścia DNa02). Przy jednakowym prądzie wejściowym na stronę, jedyną różnicą jest układ LC10a×LC10a. Mały wynik jest więc spodziewany i niewiele mówi o „topologii" w ogólności (protokół §3 to wprost przyznaje).

## 2. Zgodność wykonania z protokołem (r3)

Porównano tekst `validation/v5v3_protocol.md` z `v5v3.py`, `side_shuffle.py`, `loop.py`, `loop_v2.py`.

| Element protokołu | Kod / dane | Zgodne |
|---|---|---|
| sha256 protokołu `a0f09809…cb2a8` | `shasum -a 256 flymind/validation/v5v3_protocol.md` = to samo; runner odmawia przy niezgodności | tak |
| Hashe kodu = manifest (v5v3, side_shuffle, v5v2_topology, loop, loop_v2, visual_path) | `shasum` zgodne z manifestem; `diff v5v3.py validation/v5v3_frozen_code/v5v3.py` puste; `v5v3_run_integrity.txt` PRE/POST bez różnic, Stage 1 28/28 | tak |
| Ziarna 3051–3100, n = 50 | `seeds` w JSON `[3051, 3100]`; 250 prób; brak duplikatów (cond, seed); brak NaN | tak |
| Offsety tasowań 400 000 / 200 000 | `s + 400_000`, `s + 200_000`, `equal_weight=True` + `check_shuffle` | tak |
| Sceny `trial_spec_v2` (az0 U(−30,30), ρ U[0,16; 0,35]) identyczne dla warunków | `trial_spec_v2`; audyt: sceny identyczne w parach | tak |
| 5 warunków, dekoder DATA 496 Hz/rad dla DATA i obu tasowań | `cal["slope_snn"]` z `v4_partB_v2_…json` w `run_trial(..., slope=None)`; TOY ma własny slope | tak |
| Metryka: średnie \|e\| w 2,5–3,0 s | `loop.metrics`: `hold_s=0.5`, TICKS=300 po 10 ms; e z `bearing(sim,…)` (prawda symulatora) | tak |
| Znak d = pierwszy − drugi; d<0 ⇔ pierwszy lepszy | `analyze`: `d = err[a] − err[b]`; DATA 5,951 vs SWS 6,142 → d = −0,191 | tak |
| Test: permutacja zmiany znaku, 100 000, ziarno 3401, zera w danych | `perm_test` | tak |
| CI: bootstrap par 95/90 %, 10 000, ziarno 3402 | `boot_ci` | tak |
| Wilcoxon (Pratt), d_z, zera, \|d\|>1° | `analyze` | tak |
| SESOI 1,0° | `SESOI = 1.0` | tak |
| Reguła decyzji | `decide`: p<α ∧ CI95 → lepszy; CI90 ⊂ (−1,1) → równoważne; inaczej nierozstrzygnięte | tak |
| Rodzina Holma {H2, H3}; H1 bez korekty; D1/D2 opis | `holm([p_H2, p_H3])`, H1 `p_decision = p_perm` | tak |
| Warstwy ρ [0,16;0,24), [0,24;0,30), [0,30;0,35] | `RHO_STRATA` (górna 0,3500001), n = 21/13/16 | tak |
| Wykluczenia / przerwania | błąd symulatora → ziarno wykluczone; > 2 błędy w warunku lub > 5 % ogółu → exit; brak błędów (`error` = 0 wierszy), brak wykluczeń | tak |
| 17 własności kontroli w każdej próbie | `KEYS` ma 17 pozycji, sprawdzane w każdej próbie i `complete` | tak |
| Nachylenia po przebiegu (5 pierwszych instancji) | `post_slopes.txt`: SWS 491,7–494,8; SHUF_STR 59,1–156,5; DATA 495,6 | tak |

Drobne odchylenia (nie wpływają na wynik):
1. Pomocnicze „czas do pierwszego \|e\|<5°" jest zapisywane w JSON, ale nie ma sparowanej analizy w `analysis_summary.txt`. Sam sukces jest raportowany (27/27/24/26/50); własny McNemar DATA vs SWS: 2 vs 2 rozbieżne pary, brak różnicy.
2. Zgodność kodu z manifestem jest sprawdzana zewnętrznym skryptem integralności, nie przez runner (runner tylko liczy hashe). Zgodne w obu punktach.
3. Docstring `v5v3.py` nadal wskazuje `v5v3_protocol_DRAFT.md` (kosmetyka; kod identyczny z zamrożonym).
4. „Niezależny" audyt (`audit_v5v3_independent.py`) jest niezależny implementacyjnie (pandas, inne ziarna, t-CI), ale autor ten sam i to samo definicje decyzji; nie jest niezależny koncepcyjnie. Moje przeliczenie poniżej było pisane od zera.

Nie wykryto błędu znaku, pomyłki w kolejności warunków ani przecieku ziaren.

## 3. Przeliczenie kluczowych liczb od zera (surowy JSON, 250 prób)

Komenda: `.venv/bin/python -I -B …/scratchpad/redteam_v5v3/a3.py`, `a5.py`. Własne ziarna RNG, 10^6 permutacji.

| Wielkość | Raport | Mój wynik |
|---|---|---|
| H1 średnia d | −0,191 | −0,1908 |
| H1 CI95 (boot) | −0,579 … +0,158 | −0,582 … +0,162 (inne ziarno); BCa90 −0,562 … +0,080; t95 −0,577 … +0,195 |
| H1 CI90 | −0,512 … +0,103 | −0,516 … +0,111 |
| H1 p (permutacja) | 0,3324 | 0,3330 (10^6 perm.); t-test 0,325; Pratt 0,650 |
| H2 średnia | −2,401 | −2,4008; p = 3·10⁻⁶ (przed Holmem) |
| H3 średnia | −2,210 | −2,2099; p = 1·10⁻⁶ |
| Holm H2/H3 | 2·10⁻⁵ każde (podłoga p przy 10^5 perm. to 1e-5) | 2·10⁻⁶ / 3·10⁻⁶ przy 10^6 perm.; rzędy zgodne |
| Zera | 17 | 17 (dokładnie te same sceny we wszystkich 4 porównaniach SNN/TOY) |
| \|d\|>1° (H1) | 5 gorszych / 8 lepszych | zgodne |
| Średnie błędy | DATA 5,951; SWS 6,142; STR 8,352; TOY 7,202; P 0,314 | zgodne |
| Warstwy H1 | +0,531 / −1,018 / −0,465 | zgodne co do trzech cyfr |

Odtworzenie nie wskazuje różnic powyżej szumu bootstrapu.

## 4. Reprodukowalność (ziarna 3051–3052)

Komenda (TMPDIR = scratch):
`TMPDIR=<scratch> .venv/bin/python -I -B flymind/v5v3.py --seeds 3051-3052 --out <scratch>/rerun --approved-protocol-sha256 a0f098093b707ad9ccd06a9cc5989031d63f3a88fa1d22438144d4f4220cb2a8`
Porównanie `a2.py`: 10/10 prób (5 warunków × 2 ziarna) ma `final_abs_err`, `success`, `t_first_within`, `li_rel` i `changed_frac` identyczne co do pełnej precyzji `float` z plikiem `v5v3_20261029T210706.json` (np. DATA 3051 = 2.7883599999999995; SWS 3051 = 1.22224). Stage 1 po przebiegu OK. Wynik jest deterministyczny.

## 5. Czy „równoważne" jest ważne? (zera, warstwy, kancelacja, TOST)

**Logika TOST.** Dla dwustronnej równoważności przy α = 0,05 wystarczy CI90 ⊂ (−SESOI, +SESOI) — to jest dokładnie ekwiwalent dwóch jednostronnych testów po 0,05, więc reguła jest poprawna. Moje dodatkowe sprawdzenia, że wniosek nie zależy od percentylowego bootstrapu:
- TOST z rozkładem t: p = 0,0001; TOST z zstudentyzowanym bootstrapem przy hipotezach zerowych ±1: p = 0,0026; BCa90 [−0,562; +0,080]; t90 [−0,513; +0,131].
- Sprawdzono wrażliwość na zera (`a3.py`): tylko 33 pary niezerowe: średnia −0,289, CI90 boot [−0,781; +0,167], t90 [−0,782; +0,204], TOST p 0,010 (t) / 0,027 (stud. boot). Tylko ρ < 0,28 (32 pary): średnia −0,074, CI90 [−0,523; +0,334], TOST p 0,0007 / 0,014. Równoważność przy ±1° utrzymuje się także po wycięciu trywialnych zer.
- Rozkład d jest skośny (skośność −1,64, kurtoza 3,1; 5 par z d ≤ −2,4: ziarna 3061 −4,75, 3099 −4,35, 3091 −3,44, 3068 −2,76, 3086 −2,48), ale leave-one-out średnia mieści się w [−0,244; −0,098]; średnia ucięta 10 % wynosi +0,010, mediana 0. Brak pojedynczej próby napędzającej wniosek.

**Zera (17/50).** We wszystkich 17 wierszach błąd końcowy DATA = SWS = SHUF_STR = TOY (≈ \|az0\| — sieć nie wysyła komendy). To ρ 0,238–0,349 (w tym 4 poniżej 0,28). Skutki: (a) test równoważności jest rozcieńczony o 34 % trywialnych par; efektywnie informacyjne jest ~33 z 50; (b) mimo to wniosek się utrzymuje (powyżej); (c) permutacja ze zmianą znaku z zerami jest poprawna (zera nic nie wnoszą); (d) wniosek nie dotyczy trudnych scen, w których pętla w ogóle nie działa.

**Warstwy i kancelacja.**
- Surowe: S1 (ρ<0,24, n=21) +0,53, 15 dodatnich / 5 ujemnych / 1 zero; Wilcoxon (Pratt) p = 0,008; test znaków p = 0,041; TOST ±1° p = 0,008 → w tej warstwie „równoważne", ale z niezerowym znakiem. S2 (n=13, 4 zera) −1,02; CI95 boot [−2,02; −0,19], t95 [−2,08; +0,05], Wilcoxon p = 0,12, TOST ±1° p = 0,51 → NIE da się wykluczyć efektu ≥ 1°. S3 (n=16, 12 zer) −0,47: efektywnie 4 pary; TOST t 0,037, ale studentyzowany bootstrap 0,125 — nierobust.
- Średnia łączna jest tylko ważoną średnią warstw (21·0,531 − 13·1,018 − 16·0,465)/50 = −0,19. Zmiana wag scen (innym rozkładem ρ) zmieniłaby to bez ograniczeń. Spearman(d, ρ) = −0,38, p = 0,0065; Kruskal–Wallis po warstwach p = 0,001 (post hoc, protokół każe tylko opisywać, więc to nie jest test decyzyjny).
- Zasada interpretacji: powyższe nie obala „równoważne", ale protokół i dane nie pozwalają twierdzić „brak efektu we wszystkich warstwach". Dozwolone: „średnia łączna po rozkładzie scen V5 v2 mieści się w ±1° (CI90 −0,51…+0,10); nie wykluczono efektów przeciwnych znaków w warstwach, w ρ 0,24–0,30 nie wykluczono efektu ≥ 1° na korzyść DATA".
- **Eksploracyjna replikacja (ziarna 1001–1044, `sws.py` + `gm.py`, 44 sceny, nie potwierdzenie):** średnia d = −0,230 (zera 9) — **zgodna** ze średnią łączną. Ale struktura warstw NIE replikuje się: S1 −0,013 (9 ujemnych / 11 dodatnich, Wilcoxon p = 0,90), S2 −0,125, S3 −0,653; Spearman(d, ρ) = −0,18, p = 0,24. Wniosek: rozkład znaków w warstwach z V5 v3 (zwłaszcza dodatni S1) jest słabo odtwarzalny i nie wolno go sprzedawać jako ustalonej kancelacji ani jako ustalonej niejednorodności. Poprawny stan wiedzy: średnia łączna jest równoważna (zreplikowana wstępnie); warstwy są niejasne.

**Co protokół pozwala powiedzieć.** §5: równoważność łączna nie wyklucza efektów przeciwnych znaków w warstwach, raportowanych obok bez testów decyzyjnych; §7: przy „równoważne" dosłownie „Hipoteza nie została potwierdzona." z liczbami i warstwami; §3: „Wynik «równoważne» NIE znaczy «topologia nieistotna»". Zdanie raportu zgadza się z tym; wymaga tylko, aby „równoważne w granicach SESOI" nigdy nie występowało bez dopisku „średnia łączna po rozkładzie scen V5 v2, SESOI 1°".

## 6. Potencjalny błąd implementacji

Nie znaleziono błędu wpływającego na wynik. Sprawdzone i bez zastrzeżeń: kolejność par (d = pierwszy − drugi), indeksowanie warstw przez `rho` z wiersza DATA, `RHO_STRATA`, Holm (rząd i monotoniczność), `decide`, asercja 17 własności w każdej próbie, hashe, stała wartość slope w dekoderze, brak wykluczeń. Ryzyka resztkowe:
1. Wspólny szum ALIF `ALIF(spec, P, seed)` jest ten sam w parach (dobrze dla sparowania), ale oznacza, że d zawiera deterministyczną zależność od ziarna; przy zerach 17/17 jest to dokładnie 0.
2. Każda próba ma inną realizację tasowania (ziarno + 400 000), a DATA jest jednym grafem; wnioskowanie dotyczy więc „DATA vs rozkład grafów kontrolnych" × sceny. To zgodne z protokołem, ale wariancja realizacji tasowania jest wchłonięta w σ_d i nie da się jej rozdzielić od wariancji scen.
3. Dekoder DATA (496 Hz/rad) jest nałożony na wszystkie sieci SNN, więc nachylenie własne SHUF_STR (59–157) = zaniżone wzmocnienie pętli o 3–8×. To znane i opisane w protokole (H2/H3 jako zestaw), ale ma konsekwencje interpretacyjne (sekcja 7).
4. Docstring/komentarze wskazują `DRAFT.md`; kosmetyka.

## 7. Statystyczne i interpretacyjne uwagi dot. H2/H3 (skala sygnału)

- H2 (−2,40) i H3 (−2,21) są niemal identyczne, korelacja par H2–H3 = 0,93. DATA ≈ SWS, więc cała różnica względem SHUF_STR jest niesiona przez to, co SHUF_STR niszczy: lateralizację (LI 0,15–0,32 ×DATA), wejścia DNa02, układ warstw ORAZ skalę sygnału (nachylenie 59–157 vs 496 Hz/rad).
- Protokół sam grupuje to w „lateralizacja + warstwy + wejścia + skala", więc H3 nie jest czystym testem topologii. Poprawna interpretacja H2/H3: „zachowanie pakietu własności makro zmniejsza błąd o ~2,2–2,4°".
- **Własny test eksploracyjny (ziarna 1001–1044, 44 sceny; `gm.py`, `a6.py`):** SHUF_STR z dekoderem skalibrowanym na własne nachylenie danej instancji (mediana 127, zakres 29–204 Hz/rad) vs. wspólny dekoder 496:
  - DATA − SHUF_STR (wspólny 496): −1,99 (CI95 −2,77…−1,24), replikuje kierunek H2;
  - SHUF_STR z własnym nachyleniem − SHUF_STR wspólny: −1,01 (CI95 −1,52…−0,54) — sama skala sygnału poprawia błąd o ok. 1°;
  - DATA − SHUF_STR (własne nachylenie): **−0,98** (CI95 −1,52…−0,47, p = 0,0007) — ok. połowa efektu H2 zostaje po wyrównaniu wzmocnienia.
  Sukces: DATA 25/44, SHUF_STR 17/44, SHUF_STR_OWN 20/44. To eksploracja (ziarna dev, n = 44, offset dekodera nie wyrównany), ale pokazuje, że H2/H3 w formie z V5 v3 przeszacowują wpływ „topologii/lateralizacji" co najmniej ~2×.
- Statystycznie H2/H3 są silne (p ≪ 0,001, Holm); błąd leży w przypisaniu przyczyny, nie w teście. Dodatkowo H1 jest poza rodziną Holma — nie jest to błąd, bo H1 jest jedyną główną; wynik H1 nie zależy od tej decyzji.

## 8. Alternatywne wyjaśnienia wyniku (H1: d = −0,19°)

1. **Kancelacja efektów o przeciwnych znakach** (przewidziana, mechanizm: próg odpowiedzi DNa02 z bloku LC10a×LC10a przesuwa się różnie zależnie od napędu g). Częściowo wiarygodna, ale słabo odtwarzalna (sekcja 5).
2. **Kontrola zbyt „blisko" danych**: ok. 67 % krawędzi zmienionych (changed_frac 0,665–0,679), 57–58 % masy |w| na miejscu, 97–99 % najsilniejszych 1 % krawędzi na miejscu; lateralizacja 1,0000. Nie testuje roli najsilniejszych synaps ani tożsamości LC10a, więc „brak różnicy" = brak wpływu drobnej struktury wewnątrz bloków, nie „topologia nieistotna".
3. **Martwa strefa enkodera** (34 % par bez żadnej odpowiedzi SNN) — pętla nie sprawdza tam żadnej sieci; zastosowanie „równoważne" ograniczone do scen, w których odpowiedź w ogóle występuje.
4. **Kompensacja w pętli zamkniętej**: integrator pozycji + sprzężenie zwrotne wyrównują różnice wzmocnienia; błąd końcowy zależy głównie od szerokości strefy martwej wokół progu, a nie od przebiegu — małe przesunięcie progu (≲ 0,014 g wg `v6_stability`) daje ułamki stopnia.
5. **Zmienność realizacji tasowania w σ_d** (σ_d = 1,36° dla H1) rozcieńcza efekt systematyczny; protokół §1 sam szacował P(„równoważne”) tylko na 0,38 dla prawdziwego d = −0,5°, czyli test ma ograniczoną czułość na efekty rzędu 0,5°.

## 9. Test rozstrzygający (co zrobić, żeby naprawdę domknąć sprawę)

Kolejność według wartości:
1. **Potwierdzenie pooled-vs-warstwy na nowej, zarejestrowanej puli ziaren** (nie 3001–3100, np. 3101–3200 po rejestracji): ten sam protokół, ale (a) scenami zrównoważonymi po ρ w obszarze, gdzie sieć odpowiada (ρ < 0,28, bez martwej strefy), (b) H1 jako model d ~ warstwa (lub ρ ciągłe) z testem interakcji i TOST ±0,5° w każdej warstwie; n ≥ 30 par w każdej z dwóch warstw (przy σ ≈ 1,7 i efekcie 1° moc 0,8 wymaga ok. 24 par niezerowych).
2. **Test mechanizmu bez konfundowania scen**: pętla zamknięta ze stałym napędem g (skalowanie prądu enkodera tak, by wszystkie sceny leżały przy g = 0,5, potem przy g = 0,7): jeśli kancelacja jest prawdziwa, d zmienia znak (DATA lepsza przy 0,5, gorsza przy 0,7); jeśli efekt to zero, d ≈ 0 w obu. Nie wymaga pooled-ów i omija martwą strefę.
3. **H2/H3 rozdzielone**: dodać warunek SHUF_STR z kalibracją własną (i/lub SWS z sztucznie obniżonym wzmocnieniem do 100–150 Hz/rad). Mój eksploracyjny wynik (sekcja 7) sugeruje, że ok. połowa efektu H2 to skala; potwierdzenie wymaga zarejestrowanego protokołu i świeżych ziaren.

## 10. Podsumowanie (PASS_WITH_LIMITATIONS)

Protokół wykonany wiernie, kod = manifest, liczby odtworzone, rerun 3051–3052 identyczny co do bitu. Wniosek „równoważne w granicach 1°, hipoteza niepotwierdzona" jest poprawny formalnie i odporny na wybór CI (t, BCa, studentyzowany bootstrap) oraz wycięcie zer. Słabość nie leży w rachunkach, lecz w interpretacji: SESOI 1° jest hojny, 34 % par to zera, wynik dotyczy średniej po arbitralnym rozkładzie scen, a struktura warstw (± znaki) nie replikuje się na ziarnach dev, więc nie wolno ani twierdzić kancelacji, ani pełnej równoważności „w każdej warstwie". H2/H3 są istotne, ale skala sygnału odpowiada za ok. połowę efektu.
