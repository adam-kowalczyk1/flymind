# Errata do raportu końcowego kroku 2 (`reports/step2_final_report_20261114.md`) — 14 XI 2026

Raport końcowy pozostaje bez zmian. Ten plik zbiera poprawki i dopowiedzenia po weryfikacji (decyzja właściciela: wariant (a)).
Log pierwszej części weryfikacji: `audit_log_verification_20261114.md`; log tej części: `audit_log_poster_verif_20261114.md`.
Oznaczenia: VERIFIED / PARTIALLY VERIFIED / REPORTED / INFERRED / HYPOTHESIS / NOT VERIFIED / FAILED / NOT IMPLEMENTED.

**Wniosek ogólny się nie zmienia:** wszystkie stawy i całe ramię — FAILED według kryteriów spisanych przed testami.
Nie znalazłem błędu w kodzie, który zmieniałby te werdykty. Zmieniają się trzy sformułowania i dochodzą dwa ograniczenia.

---

## E1. „Ziarna testowe użyte raz” (raport § 2) — za mocne

**Jest:** „Test: 135 prób (45 scen × 3 pozy), ziarna testowe użyte raz.”
**Powinno być:** „…ziarna testowe użyte raz w teście głównym. Te same sceny (poza 0, tylko sieć z danych) zostały użyte
ponownie w sprawdzeniu kroku 0,1 ms we wszystkich czterech stawach; dla barku 10 z tych scen policzono przy 0,1 ms
dwukrotnie (przerwany przebieg i powtórka).”
**Status:** ujawnione odstępstwo (zapowiedziane w logach przed testem; pominięte w raporcie końcowym). Dowód:
`audit_log_verification_20261114.md` sekcje S2–S3 (pliki `lift_b/test_dt01/`, `elbow_c/dt01/`, `wrist_d/dt01/`, `roll_e/dt01/`).

## E2. Wyniki kroku 0,1 ms — status eksploracyjny

Wszystkie liczby z raportu § 1.7 i § 3 dotyczące 0,1 ms (bark 23/45 kontra 7/45, p = 3·10⁻⁵; łokieć 32 kontra 35; nadgarstek
i obrót bez zmian) są **eksploracyjne**: policzone na scenach już użytych w teście, bez osobnego celu zapisanego z góry.
Nie są kryterium i nie mogą służyć jako potwierdzenie. Wniosek „dla barku krok 1 ms zaniża wynik” = HYPOTHESIS do sprawdzenia
na nowych ziarnach z celem zapisanym przed przebiegiem.

## E3. „Nic nie zostało zacommitowane” (raport § 7, W6 b) — nieaktualne

Prawdziwe o 05:12 (czas raportu). O 09:01:59 powstał commit `19db7eb` (krok 2 + zaległe etapy); 14 XI wypchnięty zwykłym
push na `origin/flymind/fly-first-control` (VERIFIED: `git ls-remote` = `19db7eb808dc…`).

## E4. Łokieć (c): brakujące liczby i wyjaśnienie „unosi 107, odkłada 0”

**Brak w raporcie (§ 3, tabela c):** odłożenia sieci przetasowanych. Z plików `elbow_c/test/c_test_*_g1.json`
(`truth.placed`, 135 prób każda) — VERIFIED:

| Glu +1 | N (dane) | K | R | S1 | S2 | S3 | S4 | S5 | K0 |
|---|---|---|---|---|---|---|---|---|---|
| unosi (`lift`) | 107 | 100 | 87 | 111 | 115 | 113 | 105 | 115 | 99 |
| odkłada (`placed`) | **0** | 90 | 74 | **94** | **98** | **94** | **89** | **97** | 96 |

Zdanie z § 1.1 „sieci z przetasowanymi połączeniami robiły to samo albo lepiej (105–115)” jest prawdziwe dla unoszenia,
ale łagodne: na odkładaniu sieci przetasowane są na poziomie klasycznego sterownika, a sieć z danych ma 0.

**Co się dzieje po uniesieniu — VERIFIED (pliki testu + kod + diagnostyka na nowych ziarnach):**

1. To nie szczęka i nie puszczenie. W sieci z danych 107 ze 107 prób z uniesieniem kończy się powodem `no_lift`; powód
   `snn_released` (sieć szczęki puściła) to 28 prób — mniej niż w tasowaniach (41–51) i w K (49).
2. `no_lift` to reguła zapisana w kodzie i w celu przed testem (`joint_net.py` l. 245–262, `ArmCfg.lift_max = 3.0`): faza
   podnoszenia kończy się sukcesem, gdy chwytak osiągnie wysokość transportu (ok. 55 mm), albo porażką po 3 s. „Unosi”
   w ocenie = przedmiot ≥ 20 mm nad blatem.
3. Sieć z danych unosi wolno: pule łokcia 2,6 / 17,8 Hz (różnica ok. 15 Hz × k 0,005 = ok. 0,08 rad/s). Mediana po 3 s:
   31,7 mm (maks. 39,4) — powyżej 20 mm, poniżej 55 mm. Stąd „unosi, ale nie przenosi”.
4. Sieci przetasowane pobudzają pule kilka razy mocniej (pula NEG łokcia 49–93 Hz; także pule barku: podpór 31–56 Hz, wymach 2–99 Hz,
   których sieć z danych prawie nie pobudza: 5,2 i 1,3 Hz) i osiągają 55 mm w ok. 1 s (mediana 103–107 taktów).
5. **Diagnostyka (eksploracyjna, nowe ziarno 20953, wpisane do rejestru przed uruchomieniem; 45 scen × 1 poza, ta sama sieć,
   W `2dfbb84e…`, te same sceny w obu wariantach):**

   | limit fazy podnoszenia | unosi | osiąga 55 mm | odkłada | powody porażki |
   |---|---|---|---|---|
   | 3 s (jak w teście) | 36/45 | 0/45 | **0/45** | `no_lift` 38, `snn_released` 7 |
   | 10 s | 37/45 | 33/45 | **32/45** | `snn_released` 11, `no_lift` 1, `unreachable_after_lift` 1 |

   32 z 38 prób `no_lift` przy 3 s kończy się odłożeniem przy 10 s. Czas dojścia do 55 mm: mediana 4,64 s (zakres 4,04–7,76 s).
   Siła ramię↔blat 0 N, bezpiecznik 0 taktów w obu wariantach. Pliki: `elbow_diag/c_diag_N_g1_liftmax{3,10}.json`.

**Werdykt:** to **wynik sieci przy ustalonej z góry regule (3 s) i stałej k, nie błąd w kodzie**. Szczęka trzyma, łokieć
jedzie w dobrą stronę, tylko ok. 1,5× za wolno na limit 3 s. Werdykt FAILED dla (c) zostaje (C3: tasowania nie gorsze —
niezależnie od limitu czasu). Nie wolno z diagnostyki wnioskować „łokieć działa jak klasyczny”: to inne sceny, jeden wariant
Glu, brak tasowań i odruchu przy 10 s, limit zmieniony po zobaczeniu wyniku.
**Konsekwencja dla opisu:** „0 odłożeń” w (c) i w całym ramieniu (raport § 1.2: „unosi do ~3 cm w 3 s, a trzeba 5,5 cm”)
to w dużej części skutek powolnego napędu i limitu 3 s, a nie braku ruchu. Uczciwe zdanie: „sieć z danych unosi przedmiot
łokciem, ale za wolno, by zmieścić się w limicie zadania”.

## E5. Miernik siły (temat 5) — „0 N” potwierdzone dla kontaktu ramię↔blat; dochodzi ograniczenie

**Co mierzy `ForceWorld` (`lift_b_pin.py` l. 155–172) — VERIFIED z kodu:** sumę sił normalnych kontaktów ramię (z padami)↔blat,
raz na takt sterowania (po 10 krokach fizyki), maksimum w fazie. Pusty słownik `fmax_by_phase = {}` w plikach oznacza „ani
razu siła > 0”, a nie brak pomiaru.

**Niezależny pomiar w każdym kroku fizyki** (`v05_force_substep.py`, dopięty w pamięci, bez zmian w plikach projektu):

| Sprawdzenie | Wynik | Plik |
|---|---|---|
| Kontrola pozytywna: ramię celowo opuszczane na blat | pomiar co takt 66,95 / 41,23 / 41,20 N; co krok fizyki 68,78 / 41,23 / 41,20 N — różnica ≤ 3 % | `v05_force_substep.json` → `positive_control` |
| 16 prób całego ramienia z siecią z danych (8 przedmiotów × Glu ±1, ziarno 20954, ok. 290 tys. kroków fizyki) | ramię↔blat: **0 N w każdym kroku**, 0 kroków z kontaktem; bezpiecznik 0 | `v05_force_substep.json` → `trials` |
| 85 plików testu głównego | `fmax` = 0, `arm_table` = 0 we wszystkich ramionach N/K/R/S | `STATUS_20261114` krok 10 |

**Werdykt:** twierdzenie „siła ramię↔blat 0 N w próbach z siecią z danych” — **VERIFIED** (próbkowanie co 10 ms nie
ukrywa uderzeń: kontaktu nie ma w żadnym kroku 1 ms). Zastrzeżenie: 16 prób diagnostycznych, nie pełne 135.

**Nowe ograniczenie (nie było w raporcie):** miernik i kryterium C4 obejmują tylko bezpośredni kontakt ramię↔blat.
**Nie obejmują siły przenoszonej na blat przez trzymany przedmiot.** W tych samych próbach kontakt przedmiot↔blat w czasie,
gdy przedmiot dotyka padów, sięga **0,05–26,8 N** (sieć z danych) i **0,05–16,7 N** w ramieniu K (klasyczne podniesienie,
ta sama sieć szczęki; `v05b_force_substep_K.json`, 8 prób). Występuje więc także bez sieci ramienia — najpewniej docisk
przy chwycie i ciężar [HYPOTHESIS; przyczyny nie rozdzielałem]. W 5 z 8 scen wartość dla sieci jest wyższa niż dla K
(np. 25,2 kontra 16,7 N; 20,2 kontra 7,5 N), ale próby z siecią trwają dłużej i mają powtórne podejścia — z 8 scen nie da
się tego przypisać sieci [NOT VERIFIED]. Zdanie raportu § 1.4 „Bezpieczeństwo: siła ramię↔stół 0,0 N” jest prawdziwe, ale
nie znaczy „robot niczego nie dociska do stołu”. Przed sprzętem: miernik powinien liczyć także tę drogę.

## E6. „Przyczyna jest w danych, nie w kodzie” (raport § 1.3, § 7 W1, W5) — sformułowanie za mocne

**Co się potwierdza — VERIFIED (`v07_data_paths.py` → `v07_data_paths.json`, bez robota i bez ziaren):**
- Cisza pul: przy dotyku 1 N na oba pady przez 0,5 s pula wymachu barku 0,0 Hz, pule stępu 0,0 / 0,0 Hz (oba Glu); łokieć
  0 / 8,9 Hz (Glu −1) i 0,9 / 32,1 Hz (Glu +1). Zgodne z raportem.
- To nie martwy kod: ten sam kod z przetasowanymi połączeniami pobudza te same pule w próbach testowych (wymach barku
  1,8–98,8 Hz we wszystkich 30 seriach tasowań; dźwigacz stępu do 31,3 Hz, 0 Hz w 5 z 30 serii; część C pliku). Cisza jest więc własnością **schematu połączeń z danych w tym modelu**.
- Bezpośrednich synaps z pobudzanych receptorów do pul wymachu i stępu nie ma (0); do prostownika goleni jest 70.

**Co się NIE potwierdza:**
- „Sygnał dotyku nie dociera”, „w danych brakuje drogi od dotyku do tych mięśni” (W5). **Droga anatomiczna istnieje:**
  od pobudzanych receptorów do każdej z ośmiu pul prowadzą 2 kroki po połączeniach ≥ 5 synaps — i w sieci kroku 2, i w całych
  danych. Neurony odległe o 1 krok od dotyku dają pulom 17–25 % wszystkich ich synaps wejściowych (wymach barku: 3702
  z 16 068; w tym, przy Glu −1, 1951 pobudzających i 1744 hamujących).
- „Dane” jako jedyna przyczyna. Sieć kroku 2 zawiera tylko **36–55 % synaps wejściowych** tych pul (wymach barku 36 %,
  stęp 40–44 %, łokieć 55 %); reszta wejścia pochodzi od neuronów, których do sieci nie włączono (reguła wyboru podgrafu to
  decyzja modelu). O tym, czy pula odpowie, decydują też parametry modelu: waga J0 = 0,2 mV na synapsę, próg i adaptacja
  neuronu, brak szumu i aktywności tła, znak Glu, oraz krok czasu (E2: dla barku 0,1 ms zmienia wynik).

**Poprawne sformułowanie:** „W tym modelu (podgraf 2593 neuronów obejmujący 36–55 % wejścia pul, neurony ALIF bez szumu
i tła, J0 0,2) dotyk nie pobudza pul wymachu barku ani stępu, choć połączenia pośrednie w danych istnieją; pobudzenie
i hamowanie od neuronów pierwszego kroku są zbliżone. Czy żywa muszka poruszyłaby tymi mięśniami po takim dotyku — tego
model nie rozstrzyga.”
**Werdykt:** „nie błąd w kodzie” — PARTIALLY VERIFIED (odtworzone niezależnie, kod działa na tasowaniach; pełnego przeglądu
kodu sieci nie robiłem). „Przyczyna w danych” — **NOT VERIFIED w brzmieniu raportu**; poprawnie: przyczyna w połączeniu
danych **i** założeń modelu. Zdanie „w muszce sterują nimi najpewniej ośrodki wyższe” pozostaje INFERRED.
**Konsekwencja:** propozycja W1 (dodać neurony zstępujące) nadal ma sens, ale równie uzasadnione jest sprawdzenie, czy cisza
nie wynika z obciętego podgrafu i braku aktywności tła — bez dokładania czegokolwiek „z góry”.

## E7. Drobne

- Raport § 4: „okno interaktywne: NOT VERIFIED” — nadal aktualne.
- Raport § 3 (b), log T.8 kontra T.10: liczba prób przerwanego przebiegu 0,1 ms to 4 i 6 (pliki), nie „2 i 5”.
- Log § 5.18: godzina wpisu 01:36:43, nie „ok. 01:55” (kolejność zgodna).

## Czego weryfikacja nadal NIE objęła

Tematy pierwotnej listy poza 1, 2 (częściowo), 3 (przeliczenie liczb — zrobione w `STATUS_20261114`), 5 i 7: liczba neuronów
2593 / 2916 / 4100 (częściowo: 2593 + 1507 = 4100 potwierdzone testem pokazu), reguła i liczby kroku 7, zasady wejść
i etykiet [BIOLOGIA]/[ANALOGIA], pełny przegląd kodu sieci. Zgodnie z decyzją właściciela nie były kontynuowane.

## Ziarna użyte w tej części (wszystkie spoza zakresów testowych, wpisane do `SEED_REGISTRY.md` przed uruchomieniem)

- 20 953 000–449: łokieć, sieć z danych Glu +1, limit 3 s i 10 s (te same sceny — porównanie parami).
- 20 954 000–449 (8 przedmiotów, poza 0): miernik siły — całe ramię N Glu ±1 oraz K Glu −1.
Ziaren testowych (20201, 20401, 20601, 20801, 20901, 20971) nie użyto.
