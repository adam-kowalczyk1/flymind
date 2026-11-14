# FlyMind F1 — etap 1: ruch czuciowy w pętli zamkniętej. Raport końcowy

Data: 2026-11-02. Projekt zamrożony: `STAGE1_DESIGN.md` (d3 + poprawki A1–A7). Wszystkie liczby pochodzą z symulacji MuJoCo.
To **MODEL, nie mucha i nie sprzęt**.

Etykiety twierdzeń:
- **[POTW]** — test zarejestrowany z góry, reguła zamrożona przed potwierdzeniem;
- **[OPIS]** — statystyka opisowa z danych potwierdzenia;
- **[EKSPL]** — analiza post hoc, wymyślona po obejrzeniu wyników (`posthoc1.py`);
- **[ZAŁ]** — założenie.

## 1. Streszczenie

- **H1 [POTW] — SUPPORTED.**
  - Przy celu słabym/dalekim (zakres W) sukces naprowadzenia sterownika z konektomu (DATA) rośnie z 0,268 do 0,395:
    Δ = +0,1275, CI95 [0,093; 0,165], p < 1e-4 (dolna granica bootstrapu).
  - Próg odległości (ρ50) przesuwa się o ≈ 1,8 cm (red team: CI95 [1,3; 2,3] cm).
  - To efekt nieco większy niż w pętli otwartej z etapu 0 (+0,10).
  - **Kontekst inżynierski:** liniowy regulator P ma sukces 100 % w W i w S, z ruchem i bez niego.
    „Słaby cel” to więc właściwość progu ścieżki impulsowej, a kołysanie tylko częściowo go kompensuje (≈ 1,8 cm).
- **Zysk nie jest specyficzny dla konektomu ani dla SNN [POTW].** Testy równoważności dały EQUIVALENT:
  - S2, S3 — sieci przetasowane B1 i SWS;
  - S4 — prosty próg z filtrem TH_LP.
  - Losowy ruch o tej samej prędkości (jvel) jest nominalnie o ≈ 4 punkty lepszy: 0,4375 vs 0,395 (S1, w ±SESOI, ale Holm p 0,017).
    W zakresie S jest nominalnie gorszy: 0,927 vs 0,965.
  - Potwierdza to etap 0: działa wypukłość progu, a nie okablowanie.
- **Fizyka nie psuje efektu [POTW]:**
  - ruch fizyczny ≈ ruch wirtualny z etapu 0 (S8);
  - ruch świata ≈ ruch własny (S9);
  - ruch bramkowany „tylko gdy nic nie widzę” ≈ ruch ciągły (S7).
- **Reguła szkody G-b zadziałała [POTW], ale to flaga zastępcza, nie zaobserwowana strata.**
  - Przy silnym celu (zakres S) składowa 1 Hz w pan_t wynosi +1,79°, CI95 [1,76; 1,81], przy marginesie 1°. Test S10 wypada HARMFUL.
  - Sukces i błąd końcowy przy silnym celu się nie pogarszają (S5 NOT-HARMFUL).
  - Fałszywych skrętów bez celu nie ma: 0/400 (S6).
  - Według zamrożonej reguły **etap 2 (sprzęt) NIE jest rekomendowany**.
- **[EKSPL] Hipoteza, nie naprawa:** ruch bramkowany (gated) zachowuje zysk w W (S7).
  - Brak oscylacji w S wynika z konstrukcji: gated w S prawie się nie włącza (średnie |θ_s| 0,05° wobec 1,26° dla sin).
  - Wymaga nowego, zarejestrowanego testu.

## 2. Pytanie i co ten etap testował

**Pytanie:** czy celowe kołysanie kamery (obrót podstawy SO-101, ±4° namiaru, 1 Hz) pomaga pętli LC10a→DNa02 wykryć i dogonić słaby cel?

Etap 0 pokazał to w pętli otwartej, z kamerą obracaną wirtualnie. Etap 1 sprawdza to w pętli zamkniętej, gdzie ruch:
- idzie przez prawdziwy przegub, serwo i warstwę bezpieczeństwa;
- daje paralaksę, bo kamera jest 25,8 cm od osi;
- miesza się z ruchem sterowanym przez sieć.

Zgodnie z §9 protokołu etapu 0 etap 1 jest **testem inżynierskim** wypukłości progu, nie testem biologii muchy.

## 3. Projekt (skrót)

- **Ruch czuciowy θ_s:**
  - dodawany do komendy podstawy: `q0_cmd = pan_t + θ_s`;
  - kopia eferentna na poziomie komendy: `pan_t ← qt[0] − θ_s`;
  - obwiednia: rampa 0–0,25 s (A7), pełna amplituda do 4,75 s, wygaszenie do 5,5 s, ocena w oknie 5,5–6,0 s bez ruchu.
- **Zakresy celów:**
  - W (słaby): ρ 22–36 cm, |az| 8–16°;
  - S (silny): ρ 16–24 cm, |az| 10–30°;
  - N: brak celu.
- **Ruchy:**
  - none;
  - sin — 1 Hz według reguły R5;
  - jvel — losowy, dopasowany prędkością;
  - gated — wyłączany, gdy |ω| > 0,10 rad/s;
  - virtual — obrót samej kamery jak w etapie 0;
  - mt — ruch celu zamiast kamery.
- **Sterowniki:**
  - DATA (konektom);
  - B1 i SWS (przetasowania z zachowanym rozkładem stopni);
  - TH_LP-ster (próg z filtrem dolnoprzepustowym);
  - P (idealny regulator proporcjonalny, sufit).
- **Skala:** 41 prób na jednostkę × 400 jednostek, czyli 16 400 prób. Ziarna 9 112 001–400. Bootstrap hierarchiczny, ziarno 9 115 002.
- **SESOI:** 0,10 sukcesu. Holm nad S1–S4 i S7–S9. Testy szkody S5, S6 i S10 bez korekty.

## 4. Przebieg i integralność

- **Kolejne kroki:**
  - smoke;
  - wykonalność: F1 bit w bit z `loop.run_trial`; po poprawce A7 0 flag bezpieczeństwa i amplituda namiaru 4,0–4,2°;
  - R5 → f = 1 Hz;
  - pilotaż (60 jednostek, eksploracyjny);
  - reguły R1–R3: zakres bez zmian, ω_on = 0,10 rad/s, n = 400;
  - potwierdzenie.
- **Potwierdzenie:** 400/400 jednostek, 0 prób nieważnych, 0 wykluczeń. Hashe wejść były niezmienione przez cały przebieg (`manifest_confirm.json`).
- **Dwa wznowienia** (`results/confirm_stdout.txt`):
  1. Przejście z 4 na 8 procesów.
  2. Wznowienie po samoczynnym wyłączeniu laptopa. Po awarii wszystkie 265 gotowych jednostek wczytano w całości (41 wierszy, 205 tablic): 0 uszkodzeń. Jednostki zapisywane są atomowo (`.part` → `os.replace`); runner przed wznowieniem porównuje hashe.
- **Integralność po zakończeniu:**
  - `integrity_f1.py`: 2402 pliki, 0 zmian;
  - `integrity_v5v41.py --compare`: Stage 1 28/28, manifesty 18/18, 377 plików chronionych, 0 zmian.
- **Ochrona plików:** nie zmieniono plików chronionych, danych konektomu, wag, parametrów ALIF ani dekodera. Bez commitów i bez sprzętu.

## 5. Wyniki — sukces naprowadzenia (zakres W, n = 400) [OPIS]

| Sterownik | none | sin | jvel | gated | virtual | mt |
|---|---|---|---|---|---|---|
| DATA | 0,268 | **0,395** | 0,438 | 0,390 | 0,390 | 0,393 |
| B1 | 0,235 | 0,368 | — | — | — | — |
| SWS | 0,248 | 0,365 | — | — | — | — |
| TH_LP | 0,165 | 0,290 | 0,305 | — | — | — |
| P | 1,000 | 1,000 | — | — | — | — |

- **Przyrost zależy od odległości; sukces spada stromo z ρ** (wykres `success_vs_rho.png`):

  | ρ | Jednostki | none | sin |
  |---|---|---|---|
  | < 26 cm | 113 | 0,86 | 0,99 |
  | 26–30 cm | 113 | 0,09 | 0,41 |
  | ≥ 30 cm | 174 (43,5 % W) | 0 | 0 |

  Wielkość Δ zależy więc od tego, jak dobrano okno W.
- **Ruch zwiększa aktywność sieci:** średnio na próbę spajki LC10a po stronie celu rosną 139 → 323, a DNa02 7,7 → 27,8.
- **Latencja** (mediana tych prób, w których ruch w ogóle się zaczął) zmienia się z 0,08 na 0,09 s, więc ruch jej nie skraca.

## 6. Wyniki — testy zarejestrowane [POTW]

| Test | Pytanie | Estymata | CI95 | p (Holm) | Klasa |
|---|---|---|---|---|---|
| H1-S1 | Δ DATA sin − none | +0,1275 | [0,093; 0,165] | 1e-4 | **SUPPORTED** |
| S1 | sin − jvel | −0,0425 | [−0,070; −0,015] | 0,017 | EQUIVALENT¹ |
| S2 | Δ DATA − Δ B1 | −0,005 | [−0,045; 0,033] | 1,0 | EQUIVALENT |
| S3 | Δ DATA − Δ SWS | +0,010 | [−0,038; 0,053] | 1,0 | EQUIVALENT |
| S4 | Δ DATA − Δ TH_LP | +0,0025 | [−0,043; 0,048] | 1,0 | EQUIVALENT |
| S7 | gated − sin | −0,005 | [−0,020; 0,008] | 1,0 | EQUIVALENT |
| S8 | Δ virtual − Δ sin | −0,005 | [−0,028; 0,015] | 1,0 | EQUIVALENT |
| S9 | Δ mt − Δ sin | −0,0025 | [−0,025; 0,018] | 1,0 | EQUIVALENT |

¹ Zamrożony klasyfikator sprawdza równoważność (CI90 w ±0,10) przed klasą DETECTABLE. Różnica jest mała, ale niezerowa po Holmie:
**losowy ruch o tej samej prędkości jest o ≈ 4 punkty lepszy od sinusa.** Sinus nie ma więc żadnej przewagi.

**Testy szkody** (bez korekty):

| Test | Miara | Estymata | CI95 | Margines | Klasa |
|---|---|---|---|---|---|
| S5 | utrata sukcesu, zakres S | −0,010 | [−0,033; 0,013] | 0,05 | NOT-HARMFUL |
| S5 | wzrost błędu końcowego, zakres S | +0,06° | [−0,005; 0,135] | 1° | NOT-HARMFUL |
| S6 | fałszywe skręty, próby N | 0/400 | [0; 0,009] | 0,05 | NOT-HARMFUL |
| S10 | składowa f w pan_t, zakres W | +0,26° | [0,21; 0,32] | 1° | NOT-HARMFUL |
| S10 | składowa f w pan_t, zakres S | **+1,79°** | [1,76; 1,81] | 1° | **HARMFUL** |

**Warunki niepowodzenia (§9 projektu):**
- G-a nie zachodzi, bo H1 jest SUPPORTED.
- **G-b zachodzi** przez S10 w zakresie S.
- **G-c zachodzi:** S4 EQUIVALENT, zysk jest właściwością progu. Tego się spodziewano.
- G-d nie zachodzi (R5 znalazło f).
- G-e nie zachodzi, bo S8 nie jest SUPPORTED.
- G-f nie zachodzi: sukces DATA/none w W = 0,27 < 0,9.

## 7. Co znaczy szkoda S10 [OPIS + EKSPL]

S10 mierzy, ile składowej o częstotliwości ruchu przecieka do celu pętli ruchowej pan_t w porównaniu z próbą `none`.

**Co się dzieje przy silnym celu:**
- Sieć widzi ruch obrazu wywołany kołysaniem i skręca przeciwnie, żeby utrzymać cel na środku.
- W ścieżce wzrokowej nie ma odejmowania przewidywanego ruchu obrazu (reaferencji). Kopia eferentna działa tylko na poziomie komendy.
- **[OPIS] Nie jest to cecha SNN.** Regulator P ma 1,82°, a TH_LP 1,74°. Każdy dobry regulator ze sprzężeniem zwrotnym „walczy” z własnym kołysaniem.
  - W wariancie mt składowa wynosi 1,82°, ale tam pętla po prostu goni poruszający się cel.
- **[EKSPL] Skutek** (`posthoc1.py`, B): komendowany kąt podstawy (pan_t + θ_s, nie zmierzony kąt przegubu) zawiera przy silnym celu
  ≈ 63 % składowej θ_s, przy słabym ≈ 105 %. To stosunek średnich, bez CI.
- **Faza:** S10 liczy wartość bezwzględną, więc nie widzi fazy. Red team zmierzył odpowiedź pan_t względem θ_s w S ≈ 145°,
  czyli przeciwnie do ruchu (pętla kasuje kołysanie). W W odpowiedzi prawie nie ma.
- **[OPIS] Koszt śledzenia** (średnie |e| w 3,0–4,75 s, zakres S) rośnie z 1,52° (none) do 2,19° (sin). Wariant gated ma 1,69°.

**Wniosek:** G-b zachodzi według zamrożonej reguły przez S10 w S. Sukces i błąd końcowy nie wykazują jednak straty.
To szkoda w sensie definicji („ruch niekontrolowany”): ramię oscyluje ±1,8° przy celu, który już widzi.
Na sukces nie wpływa, bo ruch wygasa przed oknem oceny.

**Szkodę dało się przewidzieć.** Wykonalność (R5) pokazała już +1,76° w S przy 1 Hz. Reguła R5 wymagała jednak tylko, by przyrost
uśredniony po W i S był < 1°. To słabość projektu: reguła R5 i test S10 używały różnych kryteriów.

## 8. Analizy eksploracyjne [EKSPL] (`results/posthoc_confirm.json`, ziarno bootstrapu 9 115 003)

- **A. Kierunek pierwszego ruchu** (pierwsze 0,3 s θ_s w stronę celu lub od niego) **nie modyfikuje zysku:**

  | Kierunek | Jednostki | Δ | CI95 |
  |---|---|---|---|
  | do celu | 183 | 0,109 | [0,066; 0,158] |
  | od celu | 217 | 0,143 | [0,092; 0,198] |

  Różnica wynosi −0,034, CI95 [−0,100; 0,037]. Nie ma więc dowodu, że zysk daje „wybuch startowy” z odtworzenia pilotażu.
  To nie jest obalenie: test ma małą moc, a CI dopuszcza efekt do −SESOI.
- **B.** Patrz §7: kamera wykonuje 63 % zadanego ruchu przy celu silnym i 105 % przy słabym.
- **C. Ruch bramkowany:** składowa f w pan_t względem `none` wynosi +0,08° w S i +0,09° w W. Jest to jednak **prawie tautologia**:
  w S ruch gated jest praktycznie wyłączony (średnie |θ_s| 0,05° wobec 1,26° dla sin). W W zostaje ≈ 77 % ruchu (1,13° wobec 1,46°).
  Prawdziwe dowody to S7 (zysk w W jak przy sin) i sukces w S 0,9525.
  „Skanuj tylko, gdy nic nie widzisz” to hipoteza do nowego, zarejestrowanego testu, nie naprawa.
- **Mechanizm w odtworzeniu** (`figures/confirm/replay_*`). Jednostkę 9 112 003 **wybrano po wyniku**, regułą z `figures1.py`:
  pierwsza, w której none przegrywa, a sin wygrywa. Takich jednostek jest 55/400, odwrotnych 4/400. Ilustracja, nie dowód.
  - bez ruchu cel na −8,7° nigdy nie uruchamia DNa02;
  - z ruchem około 1 s namiar dochodzi do ≈ −12,5°, czyli większej mimośrodowości z większym wzmocnieniem enkodera;
  - DNa02 R daje 13 spajków, podstawa skacze o ≈ 3,6°, a cel trafia w okno ±5°.

  To ten sam mechanizm co w etapie 0: wzmocnienie mimośrodowości × ostry próg.

## 9. Red team wyników

Werdykt (Sonnet, zweryfikowany przeze mnie): **PASS_WITH_ISSUES**, bez blokerów. Raport: `redteam/results_redteam.md`.

- **Niezależne przeliczenie z surowych danych zgadza się:**
  - H1 = 0,1275; górna granica CI 0,1625 przy innym strumieniu bootstrapu;
  - S10 S = 1,786; gated S = 0,084;
  - 0 niezgodności sukcesu przeliczonego z e(t).
- **Analiza zgodna z projektem:** estymatory, okna, Holm, kolejność klas, S6 i strumienie RNG.
- **Awaria i wznowienia bez śladu:**
  - 400/400 npz przechodzi CRC, hashe są zgodne z manifestem;
  - 3 fazy przebiegu (225 / 40 / 135 jednostek) nie różnią się systematycznie;
  - ponowna symulacja prób z każdej fazy jest identyczna bit w bit (ω, pan_t), a e różni się o ≈ 5e-7° przez zapis float32.
- **Poprawki wniesione do tego raportu:**
  1. kontekst regulatora P;
  2. S10 opisane jako flaga zastępcza;
  3. gated jako tautologia, nie naprawa;
  4. „brak dowodu” zamiast „obalona”;
  5. 63 % to wielkość komendowana;
  6. jvel nominalnie +4 punkty;
  7. tabela stromego spadku z ρ i CI przesunięcia ρ50;
  8. odtworzenie oznaczone jako wybrane po wyniku.
- **Zostawione jako ograniczenia:**
  - Holm jest raportowany, ale klasy liczono z nieskorygowanych CI; po Holmie żadna klasa się nie zmienia.
  - Tytuł samego filmu nie mówi o wyborze po wyniku.
  - `posthoc1.py` i `figures1.py` nie są w manifeście.
  - Walidacja 265 jednostek po awarii nie ma zapisanego logu. Red team powtórzył ją jednak na wszystkich 400.

## 10. Ograniczenia

1. **Wszystko jest w modelu MuJoCo.** Nie modelowano opóźnień kamery USB, rozmycia ruchu ani luzów serw.
2. **Moc H1 w regule R2 była przypięta do ≈ 0,5** (wada opisana przed potwierdzeniem). Wynik SUPPORTED padł mimo to; estymata 0,1275 > SESOI.
3. **Słabość projektu R5 i S10** (§7): szkodę S10 dało się przewidzieć z wykonalności.
4. **Zakres W jest wąski:** zysk występuje tylko w paśmie ρ ≈ 24–29 cm, a dalej sukces wynosi 0 niezależnie od ruchu.
5. **Bez dystraktorów.** Fałszywe alarmy wynoszą 0, ale nie testowano scen z innymi obiektami.
6. **Wynik nie mówi nic o biologii muchy:** G-c, zysk taki sam dla przetasowań i dla progu.

## 11. Rekomendacja (według zamrożonej reguły §9)

Według §9 projektu rekomendacja etapu 2 wymaga trzech warunków: H1 SUPPORTED, braku G-b i braku G-d.
**G-b zachodzi, więc etap 2 (test na SO-101) NIE jest rekomendowany** dla ruchu `sin` w tej postaci.

**Co uczciwie można powiedzieć:**
- Kołysanie kamery zwiększa zasięg wykrywania ścieżki impulsowej w modelu o ≈ 1,8 cm.
  Zwykły regulator liniowy P nie ma tego problemu wcale (100 % w W).
- Działa tak samo dla każdego sterownika z ostrym progiem.
- Bez bramkowania wywołuje oscylację przy widocznym celu.

**Możliwa droga dalej (wymaga Twojej zgody; nic nie uruchomiono):**
- **Etap 1b w symulacji:** zarejestrowany z góry test ruchu gated z S10 zdefiniowanym dla gated, jvel jako alternatywą i świeżymi ziarnami.
- Dopiero potem ewentualny etap 2 na sprzęcie, jako zachowanie inżynierskie „skanuj, gdy nic nie widzisz”, z TH_LP jako równoprawnym sterownikiem.

## 12. Czego potrzeba do sprzętu (gdyby etap 2 kiedyś ruszył)

1. **Sterownik SO-101 w kodzie:** adapter `RealSO101` z tym samym interfejsem co `SO101Sim`. Dziś repozytorium nie ma sterownika Feetech, pyserial ani lerobot.
2. **Elektronika:** płytka serw STS3215 i zasilacz.
3. **Kolorowa kamera** w pozycji „oka” z symulacji. Enkoder jest chromatyczny, więc monochromatyczna OV9281 się nie nada; zamiast niej OV9782 (kolor, global shutter).
4. **Kalibracja** kamery i przegubu oraz pomiar opóźnień (kamera → SNN → serwo).
5. **Stopniowe uruchamianie z warstwą bezpieczeństwa:** bez celu, potem cel statyczny, potem ruch.
6. **Osobny protokół etapu 2** i Twoja wyraźna zgoda.

## 13. Pliki

- **Kod:** `cl_sense.py`, `runner1.py`, `analysis1.py`, `figures1.py`, `feasibility.py`, `posthoc1.py` (nowy, eksploracyjny).
- **Testy:** `tests/test_cl_sense.py`, `tests/test_analysis1.py`.
- **Wyniki:** `results/analysis_confirm.json`, `results/posthoc_confirm.json`, `results/confirm/` (400 × json + npz), `results/confirm_stdout.txt`.
- **Wykresy** (`figures/confirm/`): `success_by_condition.png`, `tests_forest.png`, `success_vs_rho.png`, `replay_frame_{000,300,599}.png`, `replay_none_vs_sin.mp4`.
  - Film wymaga ffmpeg z `~/miniforge3/bin` na PATH.
- **Zużyte ziarna:** 9 112 001–400, 9 113 001–010, 9 113 101–110, 9 115 002–003 oraz te z pilotażu i wykonalności (`SEED_REGISTRY.md`).
