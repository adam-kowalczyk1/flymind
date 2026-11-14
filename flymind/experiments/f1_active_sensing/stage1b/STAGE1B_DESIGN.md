# FlyMind F1 — etap 1b: „skanuj tylko, gdy nic nie widzisz” (PROJEKT d2 po red teamie r1, niezatwierdzony, nic nie uruchomiono)

Data: 2026-11-02. Wszystko w symulacji MuJoCo. To **MODEL, nie mucha i nie sprzęt**.

Etykiety:
- **[FAKT]** — sprawdzone w kodzie lub danych;
- **[ZAŁ]** — założenie;
- **[HIP]** — hipoteza testowana.

Red team r1: `redteam/design_redteam_r1.md`, werdykt PASS_WITH_FIXES (2 blokery, 5 poważnych, 4 drobne). Wszystkie uwagi uwzględnione (§9).

## 0. Skąd ten etap i czego NIE zmienia

**Werdykt etapu 1 zostaje:** H1 SUPPORTED, G-b zachodzi przez S10 w zakresie S, rekomendacji sprzętu nie ma
(`stage1/RAPORT_ETAP1_PL.md`). Etap 1b to nowy protokół na świeżych ziarnach, nie ponowna analiza etapu 1.

**Pytanie:** czy ruch bramkowany `gated` (θ_s wygaszane przy |ω| > ω_on, wraca po 1 s spokoju; bez zmian względem etapu 1):
- **(a)** powtarza zysk w zakresie W;
- **(b)** średnio nie szkodzi, gdy cel jest widoczny (zakres S);
- **(c)** przetrwa opóźnienie kamery 30 ms;
- **(d)** działa także dla prostego progu TH_LP?

**Charakter testu: to głównie REPLIKACJA i test szkody, nie nowe odkrycie.** Etap 1 zmierzył już gated − none w W:
+0,1225 (SE 0,018), pary niezgodne 53 wobec 4. Nowe są:
- zarejestrowane z góry testy szkody dla gated;
- ramię z opóźnieniem;
- ramię TH gated;
- zapis zmierzonego kąta przegubu q0.

**Ryzyko „szukania miary, aż wyjdzie”:**
- S10 oznaczył szkodę, a etap 1b wprowadza nowe miary szkody. Marginesy kotwiczę w wielkościach niezależnych od danych gated:
  - tolerancja sukcesu 5°;
  - pełna droga skanu.

  Nie kotwiczę ich w wartościach gated i sin z etapu 1.
- **Przewidywania z etapu 1 publikuję z góry (§5), łącznie z tym, że wszystkie testy szkody prawdopodobnie przejdą.**
  Etap 1b jest więc słabym testem: może głównie potwierdzić to, co już widać.
- **Znana z etapu 1 wada bramki** (red team, bloker B1; sprawdzone przeze mnie):
  - bramka reaguje na |ω| (wyjście DNa02), nie na „widzę cel”;
  - przy widocznym, wycentrowanym celu DNa02 milknie, po 1 s skan wraca i zabiera cel ze środka;
  - w S ruch włączył się w 97/400 prób, a w tych próbach koszt śledzenia rósł o +0,81°, wobec −0,03° w pozostałych.

  Średnie testy szkody to rozmywają. Dlatego dodaję Hm7 (droga wstrzykniętego ruchu w S) i raportuję warstwy opisowo.
  **Twierdzenie końcowe będzie brzmiało „średnio nie szkodzi”, nie „bezpieczny przy widocznym celu”.**

## 1. Fakty z kodu i danych etapu 1 (n = 400, DATA; przeliczone niezależnie przez red team)

- **[FAKT] Bramka** (`stage1/cl_sense.py:132–140`):
  - |ω| > 0,10 rad/s wyłącza ruch (rampa 0,25 s);
  - po 1,0 s spokoju ruch wraca;
  - przełączeń w S: 0 w 343 próbach, 2 w 35, 4 w 17.
- **[FAKT]** `run` zwraca zmierzone q0 (`q0_tr`, próbkowane na początku taktu, linia 141), ale `runner1.py` go nie zapisywał.
  Droga zmierzonego q0 = droga komendowanego q0 + ≈ 1 % (red team, ponowna symulacja), więc serwo niczego nie wygładza.
- **[FAKT] Wartości etapu 1:**

  | Miara | gated | none | sin |
  |---|---|---|---|
  | sukces W | 0,390 | 0,268 | 0,395 |
  | koszt śledzenia S (\|e\| 3,0–4,75 s), przyrost vs none | +0,17°, CI [0,12; 0,23] | — | +0,67° |
  | droga wstrzykniętego ruchu Σ\|Δθ_s\|, S, 0,75–4,75 s | 1,81° | — | 31,5° |
  | droga q0, S, przyrost vs none | +3,0°, CI [2,15; 3,86] | — | +6,7° |
  | S10 (lock-in pan_t), S, przyrost vs none | +0,08° | — | +1,79° |

- **[FAKT] Zysk w W zależy od pasma odległości:**

  | ρ | Zysk gated |
  |---|---|
  | < 26 cm | 0,133 |
  | 26–30 cm | 0,301 |
  | ≥ 30 cm | 0,000 |

- **[FAKT] Opóźnienie** (red team, ziarna 9 129 010–017): k = 3 i k = 4 dają 0 taktów nieważnych i 0 flag.
  k = 5 daje 288/600 taktów `vision_stale`, bo wiek klatki ≥ `max_age` 0,05 s. Przy k = 3 pierwsze 3 takty są „ślepe”
  (brak klatki; nie liczone jako nieważne).
- **[FAKT] Koszt:** w etapie 1 było ≈ 5,4 s na próbę na proces, a nie 2,1 s.

## 2. Hipotezy i testy (kierunek ustalony z góry)

SESOI = 0,10 sukcesu. Klasyfikator i bootstrap hierarchiczny jak w etapie 1 (`stage1/analysis1.py`; p z bootstrapu).

**Test główny (replikacja):**
- **H1b [HIP]:** Δ = sukces DATA gated − DATA none, zakres W.
  - **REPLICATED**, gdy dolna granica CI95 > 0 i estymata ≥ 0,05 (połowa SESOI).
  - Klasa według klasyfikatora z etapów 0 i 1 (SUPPORTED, gdy estymata ≥ 0,10) raportowana obok.

**Testy szkody gated vs none** (bez korekty):
- HARMFUL, gdy dolna granica CI95 > 0 i estymata ≥ margines;
- NOT-HARMFUL, gdy górna granica CI95 < margines;
- inaczej UNDETERMINED.

| Test | Zakres | Miara | Margines i kotwica |
|---|---|---|---|
| Hm1 | S | utrata sukcesu | 0,05 (jak S5 etapu 1) |
| Hm2 | S | wzrost średniego \|e\| końcowego (5,5–6,0 s) | 1° (jak S5) |
| Hm3 | S | wzrost kosztu śledzenia (średnie \|e\| w 3,0–4,75 s) | 0,5° = 10 % tolerancji sukcesu 5° |
| Hm5 | N | fałszywe skręty (jak S6, McNemar, dokładny CI) | 0,05 |
| Hm7 | S | droga wstrzykniętego ruchu Σ\|Δθ_s\| w 0,75–4,75 s (bez pary; none = 0) | 3,15° = 10 % pełnej drogi skanu (31,5°) |

**Testy drugorzędne** (Holm nad trzema; równoważność: CI90 w ±0,10):
- **T1:** Δ(TH_LP gated) − Δ(DATA gated), W. Bramka mierzalności jak w etapie 1: jeśli TH none w W ∉ [0,1; 0,9],
  test jest nieprzeprowadzony (p = 1).
- **T2:** Δ(DATA gated, k = 3) − Δ(DATA gated, k = 0), W.
- **T3:** sukces gated − sin, W (druga replikacja S7).

**Warunek opóźnienia K-c (osobno, bez Holma):** zysk przy k = 3, czyli sukces gated3 − none3 w W, musi mieć dolną granicę CI95 > 0.

**Opisowo (nie wchodzi w decyzje):**
- S10 (lock-in pan_t) — dla gated jest spełniony z konstrukcji, więc nie jest testem;
- droga zmierzonego q0 — zdominowana przez cykl graniczny V5 (SD ≈ 22°, rozkład dwumodalny);
- **odsetek prób S z włączonym ruchem** (max |θ_s| > 0,05°) i koszt śledzenia w warstwach „włączony / niewłączony”.
  Warstwy wyznacza zmienna po zabiegu, więc to opis, nie test;
- przełączenia bramki;
- `sin` jako kontrola dodatnia miar (Hm3, Hm7, S10);
- sukces w pasmach ρ;
- latencja;
- spajki LC10a i DNa02;
- flagi bezpieczeństwa.

## 3. Macierz (21 prób na jednostkę)

| Sterownik | Ruchy | Zakresy | Próby |
|---|---|---|---|
| DATA (k = 0) | none, sin, gated | W, S, N | 9 |
| DATA (k = 3, 30 ms) | none, gated | W, S, N | 6 |
| TH_LP-ster | none, gated | W, S, N | 6 |

- **Bez zmian względem etapu 1:**
  - zakresy W, S, N;
  - f = 1 Hz, A = 4° namiaru, obwiednia z A7;
  - ω_on = 0,10 rad/s;
  - kalibracje z `stage1/stage1_params.json` (tylko odczyt).
- **Bez B1, SWS i jvel-gated** (§8).
- **Bez pilotażu.**

## 4. Implementacja (po zgodzie) i ochrona plików

- **Nowy katalog `stage1b/`.** Pliki `stage1/` pozostają bez zmian.
- **`runner1b.py`:**
  - importuje `stage1/cl_sense.py`;
  - opóźnienie przez podstawienie `CS.DelayLine = lambda _k, init: DelayLine(k, init)` wewnątrz procesu roboczego, na czas jednej próby,
    z przywróceniem w `finally` (komentarz `ponytail:`: nie edytuję zamrożonego `cl_sense`);
  - zapis npz: e, pan, th, om, cnt jak w etapie 1, plus **q0** (zmierzony).
- **Atomowość, manifest i odmowa wznowienia po zmianie hashy** jak w `runner1.py`. Hashe obejmują `stage1b/*`, `stage1/cl_sense.py`,
  `stage1/analysis1.py`, `stage1/stage1_params.json` i zależności flymind.
- **STOP:**
  - > 1 % jednostek z próbami nieważnymi;
  - **jakakolwiek flaga bezpieczeństwa (lead lub rate) w > 1 % prób.**
- **`analysis1b.py`:** importuje `classify`, `harm`, `holm`, `s6`, `boot_idx`, `stat_boot` z `stage1/analysis1.py`. RNG analizy: 9 123 001.
- **`figures1b.py`:**
  - forest: H1b, T1–T3, Hm, z `sin` opisowo;
  - przebiegi q0 i θ_s dla none / sin / gated w S. Jednostka wybrana regułą zamrożoną tutaj: najniższy numer z sukcesem w trzech
    ramionach S. Podpis mówi, jak ją wybrano.
- **Testy (`tests/test_runner1b.py`):**
  1. k = 0 odtwarza zapisane próby etapu 1 (jednostka 9 112 001, DATA gated W i S; e, pan, θ_s, ω, cnt; porównanie w float32;
     red team już to wykonał). Ziarno zużyte, służy wyłącznie weryfikacji.
  2. k = 3 daje 0 taktów nieważnych na ziarnach smoke.
  3. `DelayLine` jest przywracany po wyjątku.
- **Integralność:** `integrity_f1.py` i `integrity_v5v41.py --compare` przed przebiegiem i po nim.
- **Uruchomienie:** `.venv/bin/python -I -B`, 3 procesy, `nice -n 10`, `caffeinate -i`.

## 5. Statystyka, wielkość próby, przewidywania

- **n = 200 jednostek**, ziarna 9 121 001–200. Pule 9 121 201–400 są zarezerwowane i nieużyte.
- **Uzasadnienie n:** kryterium replikacji (dolna granica > 0 i estymata ≥ 0,05) ma przy n = 200 moc ≈ 1,0 dla Δ ≥ 0,10.
  Testy szkody mają przy n = 200 przewidywane górne granice daleko od marginesów (tabela niżej).
  Dawne kryterium „estymata ≥ SESOI” przypinało moc do ≈ 0,5 przy Δ = SESOI (wada R2 etapu 1). Red team potwierdził moc 0,91 / 0,73 / 0,52
  dla Δ 0,1225 / 0,11 / 0,10 przy n = 400. Dlatego nie jest kryterium decyzyjnym.
- **Przewidywane klasy** (bootstrap danych etapu 1 przy n = 200, ziarno planowania 9 129 100):

  | Test | Etap 1 | CI95 przy n = 200 | Margines | Przewidywanie |
  |---|---|---|---|---|
  | H1b | +0,1225 | ≈ [0,07; 0,17] | — | REPLICATED |
  | Hm1 | −0,0025 | ≈ ±0,03 | 0,05 | NOT-HARMFUL |
  | Hm2 | +0,04° | ≈ [−0,05; 0,15] | 1° | NOT-HARMFUL |
  | Hm3 | +0,17° | [0,09; 0,26] | 0,5° | NOT-HARMFUL |
  | Hm5 | 0 zdarzeń | [0; ≈ 0,02] | 0,05 | NOT-HARMFUL |
  | Hm7 | 1,81° | [1,29; 2,40] | 3,15° | NOT-HARMFUL |
  | T1, T2 | brak danych | — | ±0,10 | nieznane |

  **Łączne prawdopodobieństwo przejścia wszystkich warunków [ZAŁ]: ≈ 0,8**, bo T1, T2 i K-c są nieznane.
  Przy UNDETERMINED blokującym rekomendację ≈ 20 % „czystych” przebiegów może jej nie dostać.
- **Koszt:** 21 prób × ≈ 5,4 s ≈ 113 s na jednostkę na proces. Przy 200 jednostkach i 3 procesach to **≈ 2,1 h**.

## 6. Reguły i warunki niepowodzenia (zamrożone)

- **Wykonalność** (ziarna smoke 9 128 001–020):
  - test bit w bit k = 0 nie przejdzie → STOP;
  - k = 3 z taktami nieważnymi lub flagami → ramię opóźnienia wypada, T2 = nieprzeprowadzony (p = 1), K-c = NIEOCENIONY.
- **K-a:** H1b nie REPLICATED → zysku nie da się powtórzyć.
- **K-b:** którykolwiek z Hm1, Hm2, Hm3, Hm5, Hm7 HARMFUL lub UNDETERMINED → nie można twierdzić „średnio nie szkodzi”.
- **K-c:** zysk przy k = 3 bez dolnej granicy > 0 (albo NIEOCENIONY) → zysk nie jest odporny na opóźnienie kamery.
- **K-e:** flagi bezpieczeństwa lub próby nieważne powyżej progu STOP → przebieg nieważny.
- **W zakresie W szkody nie testuję:** ruch jest tam celem. Opisowo raportuję koszt śledzenia i flagi.
- **Rekomendacja etapu 2 (sprzęt)** tylko gdy nie zachodzi żaden z warunków K-a, K-b, K-c, K-e. Raport musi też podać odsetek prób S
  z włączonym skanem i koszt w tej warstwie. Nawet wtedy:
  - jako zachowanie inżynierskie „skanuj, gdy DNa02 milczy”, z TH_LP jako alternatywą;
  - z zastrzeżeniem, że zysk występuje tylko dla ρ < 30 cm;
  - z osobnym protokołem etapu 2 i Twoją zgodą.

## 7. Ziarna

Rezerwacja wpisana do `SEED_REGISTRY.md` przed manifestem. Skan kolizji 9 121–9 129 xxx w flymind/ i bio2/ (*.py, *.md):
0 trafień jako ziarno; red team potwierdził.

| Pula | Użycie |
|---|---|
| 9 121 001 – 9 121 200 | jednostki: szum ALIF u, `pixel_noise(u)`, `draw(u)`, jvel jak w etapie 1 |
| 9 121 201 – 9 121 400 | zarezerwowane, nieużyte |
| 9 123 001 | RNG analizy; 9 123 002 zapas |
| 9 128 001 – 9 128 099 | smoke, testy, wykonalność |
| 9 129 001, 002, 100 | ZUŻYTE: planowanie mocy i przewidywań |
| 9 129 003, 010–017 | ZUŻYTE: red team r1 |
| 9 129 018 – 9 129 999 | kolejne red teamy |

## 8. Ograniczenia znane z góry

1. **Słaby test** (§0, §5): wynik jest w dużej mierze przewidywalny z etapu 1. Marginesy są zakotwiczone, ale wybrane przez autora po obejrzeniu danych.
2. **Bramka reaguje na |ω|, nie na wykrycie.** W ≈ ¼ prób S skan wraca mimo widocznego celu. Warianty z zatrzaskiem
   albo z dłuższym czasem spokoju to osobny projekt (nowy tryb w kopii `cl_sense`).
3. **Opóźnienie 30 ms to dolna granica dla kamery USB** (50–100 ms). k ≥ 5 koliduje z `max_age` 0,05 s w zamrożonym kodzie.
4. **Bez rozmycia ruchu, luzów serw i dystraktorów** (dystraktor w `so101.py` to identyczna zielona kula).
5. **Bez jvel-gated:** jvel jest w W nominalnie lepszy, w S gorszy.
6. **Wynik nie mówi nic o biologii muchy.**

## 9. Odpowiedź na red team r1

- **B1** (średnie rozmywają szkodę): sprawdzone (97/400, +0,81°). Dodano Hm7 i warstwy opisowe; twierdzenie końcowe osłabione do
  „średnio”; ograniczenie 2.
- **B2** (koszt i opóźnienie): koszt poprawiony na 5,4 s na próbę, a k = 5 opisane jako nieważne (288/600).
- **M1** (kotwice marginesów i pusty Hm6):
  - Hm3 zakotwiczony w tolerancji 5°;
  - Hm4 zastąpiony przez Hm7, zakotwiczony w pełnej drodze skanu;
  - Hm6 i K-d przeniesione do opisu;
  - dodane przewidywania i łączne P ≈ 0,8.
- **M2** (H1b to replikacja): nazwane wprost, kryterium REPLICATED, n = 200.
- **M3** (Hm4 bez nowej informacji): przeniesione do opisu.
- **M4** (opóźnienie): K-c wymaga zysku z dolną granicą > 0 przy k = 3; łatka opóźnienia stosowana w procesie roboczym.
- **M5:** rezerwacja wpisana do `SEED_REGISTRY.md`.
- **Drobne:**
  - przełączenia bramki opisowo;
  - reguła dla W;
  - STOP na flagach bezpieczeństwa;
  - bramka mierzalności dla TH;
  - Holm na p z bootstrapu;
  - słowo UNDETERMINED.
