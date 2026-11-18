# FLYMIND — kontekst główny (stan na 2026-11-07; AKTUALIZACJA 2026-11-18 poniżej)

## 0. AKTUALIZACJA 2026-11-18 — przeczytaj najpierw (sekcje 1–15 opisują stan z 7 XI i miejscami są nieaktualne)

Wszystko nadal w symulacji MuJoCo; prawdziwe ramię niepodłączone. Źródłem są raporty wskazane w nawiasach; jeśli coś tu
przeczy raportowi, rozstrzyga raport.

- **Kroki 3–6 (15–16 XI): sieć z danych muchy steruje całym ramieniem** (bark, łokieć, nadgarstek, szczęka). Sieć nogi „pre”
  (reguła: wszystkie interneurony VNC z ≥ 5 synapsami do neuronów ruchowych nogi przedniej L). Zdanie „całe ramię 0/135”
  z kroku 2 jest nieaktualne. (`results/step3_20261115/STEP3_REPORT_20261115.md`, `STEP6_REPORT_20261116.md`)
- **„Dwa odruchy” (krok 4 r2, 16 XI):** dotyk dłoni → cofnij, dotyk palców → zaciśnij; sieć z danych lepsza od tasowań F i L
  przy obu Glu. (`REFLEX_R2_REPORT_20261116.md`)
- **Etap 2 (18 XI): tasowania o TEJ SAMEJ aktywności.** Glu +1: sieć z danych 54/80 par, lepsza od każdego z 10 wyrównanych
  tasowań (0–40) — przewaga nie wynika z samej „głośności” [VERIFIED, model]. Glu −1: 27/80, NIE lepsza (jedno tasowanie 45).
  (`LOUD_R1_REPORT_20261118.md`)
- **Krok 6 (16 XI): dotyk „głowy” → dwa szlaki z danych:** BM → DNg15 → łokieć, BM → DNge078 → nadgarstek. Z sondą 26/26;
  wycięcie DNg15 zatrzymuje tylko łokieć, DNge078 tylko nadgarstek (0/27). Zwykły dotyk (r1) FAILED. (`STEP6_REPORT_20261116.md`)
- **Etap 1 (18 XI): zwykły dotyk, odruch wycofania.** Glu +1: sieć sama kończy dotyk 26/26, po wycięciu 4 neuronów 0/26 — PASS.
  Glu −1: 18/26 = 69 % — FAILED (lekki/średni walec jedzie z dłonią). (`TOUCH_R1_REPORT_20261118.md`)
- **Dawka dotyku → siła zacisku: FAILED** (przewaga danych tłumaczona aktywnością). (`DOSE_REPORT_20261116.md`)
- **Oko muchy (flyvis → MaleCNS, 16–17 XI): ZAMROŻONE do po Explory.** Sześć+ testów z celem zapisanym z góry FAILED; test D
  z idealnymi bodźcami pokazał, że winny jest most model oka → mapa połączeń, nie kamera robota.
  (`reports/fly_eye_w2_lc4_20261117.md` §0, §4I)
- **Glu:** znak glutaminianu nieznany z danych — każdy wynik podawany osobno dla Glu +1 i Glu −1; Glu +1 wypada lepiej
  w etapach 1–2, ale nie wybieramy znaku po fakcie.
- **Sprzęt (18 XI, słowa Adama):** ramię złożone i skonfigurowane w lerobot, zasilacz i kabel są; 18 XI przychodzą kamera
  (Amazon) i 2× FSR402; Arduino jest. Testy na prawdziwym ramieniu dopiero na polecenie Adama (nic nie uruchomiono).
- **Plan do 1 XII (ustalony 18 XI):** do 27 XI badania (prawdziwe ramię: odruch wycofania sieci muchy), 28–30 XI materiały
  na prezentację. Explory 1 XII.
- **Git:** gałąź `flymind/fly-first-control`, wypychana na origin zwykłym push; pliki `*.npz` i `raw/` celowo poza repo.


**Do czego służy ten plik:** jedno miejsce, od którego zaczyna każda nowa sesja (Claude, inny chatbot, weryfikator). Streszcza cel, zasady, wyniki, otwarte decyzje i plan. Szczegóły są w plikach, na które wskazuje.

**Autor:** Claude (Opus 5.5) na prośbę właściciela, 2026-11-07. To nie jest niezależna recenzja. Źródła to notatki pamięci Claude, dokumenty w repozytorium i raporty z sesji 2026-11-06/07. Jeśli coś tu przeczy plikowi źródłowemu, rozstrzyga plik źródłowy.

**Poziomy dowodu:**
- **VERIFIED**: sprawdzone w kodzie lub plikach;
- **RECOMPUTED**: przeliczone ponownie;
- **REPORTED**: przepisane z raportu, nie sprawdzane teraz;
- **INFERRED**: wniosek;
- **NOT VERIFIED**: nie sprawdzono.

---

## 1. Cel projektu i zasada nadrzędna

- **Cel:** ramię SO-101 sterowane przez model wycinka mózgu muszki owocowej (*Drosophila*), zbudowany z prawdziwych danych połączeń neuronów (konektom **MaleCNS v1.0**, Janelia; to nie jest FlyWire).
- **Zasada nr 1 (słowa właściciela, 2026-11-03):** „najważniejsze jest to, żeby nie algorytm tym sterował, tylko mucha, nawet jeżeli stracimy na tym jakościowo”.
  - Decyzje ruchowe ma podejmować sieć neuronowa z konektomu (źródło `snn:...`).
  - Kod klasyczny (IK `reach.py`, automat `grip.py`, regulator P, wyuczone polityki ACT/VLA) wolno używać tylko jako:
    - warstwy bezpieczeństwa,
    - punktu odniesienia do porównań,
    - jawnie oznaczonego rusztowania.
  - Gorszy wynik muchy zgłaszamy uczciwie, nie podmieniamy jej algorytmem.
- **Właściciel odrzucił sztuczne pobudzanie neuronów** („wirtualna optogenetyka”). Wejścia mają pochodzić tylko z naturalnych zmysłów: kamery, dotyku i propriocepcji.
- **Etykiety w każdym opisie:**
  - DATA: to, co pochodzi z konektomu;
  - MODEL: dynamika neuronów i parametry przyjęte przez nas;
  - ENGINEERING: kamera, enkoder, dekoder, serwa, bezpieczeństwo.
- **Ograniczenie interpretacji:** „to nie jest mózg muchy, tylko model wycinka połączeń w symulacji”.

## 2. Właściciel i sposób pracy

- Adam Kowalczyk, właściciel nietechniczny. Raporty pisz prostym polskim: najpierw wynik, potem jedna decyzja do podjęcia.
- Uczciwość Claude sprawdza zewnętrzny chatbot (weryfikator). Każdy raport musi więc mieć dowody: komendy, liczby, ścieżki plików, poziom dowodu.
- Claude sam proponuje cele i kolejne kroki, ale nie przekracza zakazów (pkt 11) bez wyraźnej zgody.
- Właściciel często pracuje przez Remote Control. Ostatnia wiadomość musi być zrozumiała bez okienka „następny krok”.

## 3. Terminy (REPORTED z notatek; daty do potwierdzenia przez właściciela)

| Data | Co |
|---|---|
| **16 XI 2026** | Plakat na festiwal Explory (według szablonu szkoły; e-mail z nazwą zespołu i projektu, szkoła drukuje) |
| ok. **17 XI 2026** | Rejestracja projektu (regulamin: ≥ 14 dni przed festiwalem; zweryfikować u p. Maciejczyka) |
| **1 XII 2026** | Festiwal Explory (Fundacja Zaawansowanych Technologii), prawdopodobnie sala 416. Trzech jurorów, 3 kryteria po 0–10. Możliwa obecność ORLEN jako sponsora |

Raport dla inwestorów i jury: `reports/Projekt mózgu muchy dla inwestorów.md`.

## 4. Sprzęt i środowisko (VERIFIED 2026-11-03/07, o ile nie zaznaczono)

- **Komputer:** MacBook Pro M1 Max, 32 GB.
- **Ramię:** jedno SO-101 follower (serwa ID 1–6), skalibrowane na tym Macu 1 X (`~/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json`).
  - **Ramię nigdy nie było podłączone do kodu FlyMind.** W repozytorium nie ma sterownika sprzętu dla FlyMind.
  - Nie ma ramienia leader.
- **Kamery widziane:** FaceTime HD i iPhone Continuity Camera („Sigma_Iphone”). Kamera na nadgarstku: nie ma.
  - Rekomendacja z 2026-11-05: OV9281 (mono, global shutter, ok. 50 USD). Nie kupiona.
- **Czujniki dotyku w chwytaku:** istnieją tylko w MuJoCo.
  - Rekomendacja z 2026-11-05: 4× FSR plus prąd i pozycja serwa. Nie kupione.
- **Nieznane, dopóki właściciel nie potwierdzi:** przełożenia serw, zasilacz, adapter, kamera zewnętrzna. **Nie wymyślać części.**
- **Python FlyMind:** `/Users/admin/so101_fly_project/.venv/bin/python -I -B`.
  - Środowisko ma mujoco i scipy, nie ma lerobot ani torch.
  - Okno MuJoCo na macOS wymaga `.venv/bin/mjpython`.
- **LeRobot:** `~/miniforge3/envs/lerobot` (py3.12). Polecenia `lerobot-*` w bazowym miniforge (py3.14) są zepsute.
- **ffmpeg:** `~/miniforge3/bin` (nie ma go w PATH).

## 5. Co jest zbudowane (architektura)

**Główna pętla V5 (`loop.py`, plik chroniony):**
- kamera MuJoCo na chwytaku;
- `encoder.py` (kolorowa plama, ten sam prąd do wszystkich LC10a jednej strony; to heurystyka ENGINEERING, nie siatkówka);
- **424 neurony z danych:** 135 + 140 LC10a → 147 pośrednich → 2 DNa02;
- ALIF (`alif.py`, plik przypięty hashem) z J0 = 0,2 mV/synapsę i szumem σ = 2 mV;
- `decoder.py`: P na DNa02 L−R;
- `safety.py` → `so101.py` (MuJoCo).

Krok 1 ms, takt 10 ms.

**Ważne fakty o sieci (VERIFIED 2026-11-03):**
- 0 bezpośrednich synaps LC10a→DNa02. Droga prowadzi przez pośrednie, a pośrednie dają ok. 12% wejścia DNa02.
- PFL3→DNa01 ma 0 synaps w całym konektomie.

**Inne moduły:**
- `connectome.py`, `snn_interface.py` (DATA oddzielone od krawędzi modelu);
- `sensory.py`, `latency.py`, `epg_ring.py`;
- `alif_sparse.py` (rzadki ALIF);
- `leg_circuit.py`, `vision_leg.py` (LC9→DNp09→VNC→nogi), `six_legs.py`;
- `fly_jaw.py` (FJ1), `fly_arm.py` (FJ2);
- `reach.py` (klasyczne IK, rusztowanie), `grip.py` (klasyczny automat, punkt odniesienia).

**Etap 0 (2026-11-06):** `alif_dt.py`, `v5v41_dt.py`, `test_stage0_dt.py`. Krok czasu dt ≠ 1 ms, tylko otwarta pętla.

**Pokaz:** `demo/demo.py` (okno, prezentacja, nagrania), `demo/demo_snn_vs_p.mp4`, `demo/media/*.png` (31 X).
- `test_demo.py` sprawdza, że trajektoria jest identyczna z `loop.run_trial`.

**Teleoperacja padem:** `pad_so101/` (poza flymind).
- Pad Xbox → `SafetyLayer` → SO-101 → nagrania LeRobot.
- Sprawdzona **tylko offline**. Polityka wyuczona z demonstracji to wyłącznie punkt odniesienia, nigdy wynik muchy.

## 6. Które stawy steruje mucha — stan faktyczny (VERIFIED w kodzie 2026-11-07)

| Staw | Główna pętla V5 i pokaz | Gałąź FJ1/FJ2 (eksperymenty z 2026-11-03) |
|---|---|---|
| 0 obrót podstawy | **SNN** (LC10a→DNa02, `snn:`) | SNN (DNa02) w projekcie FJ2 |
| 1 shoulder_lift | skrypt `script:hold_pose` (`loop.py:145–146`) | **SNN pilot**: sieć wzrok→nogi (LC9→DNp09→VNC), `fly_arm.py` |
| 2 elbow_flex | skrypt | **SNN pilot** jw. |
| 3–4 nadgarstek | skrypt | klasyczne / stałe |
| 5 chwytak | nie sterowany | **SNN**: obwód dotyku nogi T2 L (`fly_jaw.py`, FJ1) |

**Korekta mojej wiadomości z 2026-11-07:** napisałem tam, że sieć steruje dziś tylko obrotem podstawy. To prawda dla głównej pętli i pokazu. **Pominąłem jednak FJ1 (chwytak) i piloty FJ2 (stawy 1–2).** Są one słabiej sprawdzone (pkt 7), ale istnieją.

## 7. Wyniki — co wiemy (wszystko w symulacji MuJoCo)

| Linia | Wynik | Poziom | Gdzie |
|---|---|---|---|
| V3.2 pierścień EPG (CX) | Przy domyślnym hamowaniu brak bąbla aktywności. Przy Delta7 ×16 trwały łuk „przyklejony do bodźca”: dane 65/80, tasowanie 0/80. To stany skwantowane, nie ciągły atraktor | REPORTED | `VALIDATION_PLAN.md`, `results/v32/` |
| V5 orientacja podstawy | SNN 38/40, tasowanie 3/40, P 40/40 i dokładniejszy o 1,2°. Tasowanie zachowujące siłę daje 10/10, więc wynik pokazuje **lateralizację, nie topologię** | REPORTED | `validation/v5_confirm_*` |
| V5 v2 | SNN 28/50, eqshuffle 20/50, P 50/50. Kontrole biegły przy innym wzmocnieniu dekodera; „43% przez AOTU” **wycofane** | REPORTED | `results/audit_shared_decoder_20261029.txt` |
| V5 v3 (pula 3051–3100) | DATA − SWS = −0,19° (równoważne w ±1°). **Hipoteza nie została potwierdzona** | REPORTED | `results/v5v3/` |
| V5 v4 (4001–4450) | Znak DATA−SWS zależy od reżimu (+0,51° / −0,52°). P lepszy o 2,68° | REPORTED | `V5v4_FINAL_REPORT.md` |
| Program V5 v4.1 → V6m3 | W modelu połączenia LC10a×LC10a desynchronizują LC10a, a refrakcja na dwóch etapach zamienia to na silniejszy DNa02. **W pętli zamkniętej brak odpornej przewagi połączeń z danych; regulator P lepszy wszędzie.** „Nic z tego nie jest dowodem o musze” | REPORTED | `program_v5v41/FINAL_REPORT.md` |
| Porównanie z P | P lepszy od SNN w **446/450** parach (nie 450/450) | VERIFIED 2026-11-03 | `reports/Hybrydowe mózgi…` |
| F1 aktywne patrzenie | Oscylacja kamery poprawia wykrywanie słabych celów (0,268→0,395), ale efekt jest ogólny dla progu (kontrole dają to samo) i szkodzi przy silnych celach. **Linia zamknięta 2026-11-02** | REPORTED | `experiments/f1_active_sensing/` |
| D1 audyt danych dotyku | Obwód dotyku nogi istnieje; znak zależy od założenia o glutaminianie (Glu). Brak kanału nacisku (CS) | REPORTED | backup `RAPORT_D1_D2_D3_PL.md` |
| **FJ1 chwytak muchy** | Chwyt 12/12 (H1). **Bez przewagi nad trywialnym odruchem (12/12)** i bez dowodu roli połączeń (H2 nierozstrzygnięta lub odrzucona). Zadanie sprowadza się do progu momentu | REPORTED | `experiments/fj1_fly_jaw/RESULTS.md` |
| **FJ2 ramię muchy (pilot)** | Przy Glu −1 sieć zbliża chwytak do piłeczki (0,30 m: 71→17 mm). Glu +1 niespójne. Chwytak wciska się w stół (brak kontroli stołu w `safety.py`). **Brak naturalnego sygnału „podnieś”**; kandydat T2L→T2R wycofany po red teamie | REPORTED | `experiments/fj2_fly_arm/PILOT_NOTES.md` |
| Czujniki chwytaka (dane) | Propozycja wejść szczęki: FeCO claw/hook (SNpp50/51/39/41). Kanał obciążenia (bCS) porzucony | REPORTED | notatka 2026-11-05 |
| κ (V6.1) | Wartość zależy od estymatora (1,013–1,043). Test „poza próbką” nie odróżnia κ od naiwnego progu. **Nie cytować κ jako stałej** | RECOMPUTED 2026-11-07 | `scratchpad/deep/FLYMIND_DEEP_AUDIT.md` |
| Etap 0 (dt ≠ 1) | Przy dt = 1 wynik bit w bit równy staremu. 8/9 kryteriów z dowodem. f–I przy dt 0,1: błąd 2,5% (limit 2%), przy dt 0,05: 1,3%. Pętla zamknięta przy dt ≠ 1 nie istnieje | VERIFIED | `program_stage0/STAGE0_REPORT.md` |
| Deep Audit | **READY WITH CONDITIONS** dla Etapu N. Warunek główny: szum `hold1` (bez niego **NOT READY**). Błąd Fano w V6 potwierdzony, wnioski się nie odwracają | RECOMPUTED | scratch (pkt 13) |
| Red team zabezpieczeń dt | Propozycja G1–G7 w obecnej formie odrzucona. Poprawiony plan W2′ zatwierdzony warunkowo. Stary kod przyjmuje dt ≠ 1 po cichu | VERIFIED | scratch (pkt 13) |

## 8. Twierdzenia wycofane lub zakazane (nie używać na plakacie ani w pitchu)

- „Ramię sięga i chwyta piłeczkę dzięki mózgowi muchy” jako całość. **Nie.** Podstawa jest z SNN, stawy 1–2 to tylko pilot, chwytak nie ma przewagi nad odruchem.
- „Sieć muchy jest lepsza od algorytmu.” **Nie.** P wygrywa w 446/450 parach.
- „Wynik pokazuje znaczenie topologii konektomu.” **Nie.** V5 pokazuje lateralizację; V5 v3 to równoważność DATA vs SWS.
- „LC10a→AOTU wyjaśnia 43%” — wycofane.
- „450/450” — poprawnie jest 446/450.
- „Odporny naturalny sygnał uniesienia (T2L→T2R)” — wycofane.
- „κ = 1,035 jako własność sieci” i „8/8 znaków” — niedozwolone.
- „Dane FlyWire” — błąd, to MaleCNS v1.0.
- „Działa na prawdziwym robocie” — nigdy nie testowane na sprzęcie.
- „To jest mózg muchy” — to model wycinka połączeń z ogólną dynamiką ALIF.

## 9. Otwarte decyzje właściciela (stan 2026-11-07)

1. **Pokaz 1 XII:** prawdziwe ramię SO-101 czy tylko symulacja? Wcześniejsza analiza: nowość projektu pojawia się dopiero na prawdziwym ramieniu. Wymaga wyraźnej zgody na sprzęt.
2. **Szum `hold1`** jako definicja szumu w Etapie N (`white` jako analiza wrażliwości). Zewnętrzna ocena pisze „wstępnie rozstrzygnięte”, **ale właściciel tego nie potwierdził Claude'owi**.
3. **Zabezpieczenie starego kodu przed zmianami:** commit w gicie plus archiwum `validation/v5v41_v6_v7_frozen_code/` (rekomendacja) czy samo archiwum?
4. **Zakres dt:** biała lista (np. {1; 0,5; 0,2; 0,1; 0,05}) czy dolna granica?
5. **Zgoda na wdrożenie poprawionego planu zabezpieczeń** (W2′, pkt 10).
6. Zaległa od 2026-11-02: commit ok. 130 nieśledzonych plików `flymind/` (wyniki V5v3 → V6m3, Etap 0). Obecnie są tylko w kopii lokalnej z 2026-11-02 i na dysku.
7. Do rozstrzygnięcia: projekt Stage 1 v3 (E0/E1, audyt 2026-11-04) oraz FJ2 (protokół potwierdzający z nową pulą ziaren).

## 10. Proponowany plan do 1 XII (propozycja Claude; czeka na decyzje z pkt 9)

1. **Plakat do 16 XI**, tylko ze sprawdzonymi twierdzeniami:
   - symulacja;
   - MaleCNS;
   - SNN obraca podstawę;
   - P jest lepszy, a mucha steruje mimo to (zasada nr 1);
   - chwytak FJ1 bez przewagi nad odruchem.
2. **Jedno powtarzalne zadanie pokazowe:** SNN obraca podstawę w stronę obiektu. Kontrole: sieć tasowana i regulator P. Wiele prób, zmierzone wyniki i opóźnienia, wideo. Materiał startowy: `demo/`.
3. **Minimalne zamknięcie Etapu 0 (ok. 1–2 dni):**
   - archiwum i mapa wersji;
   - walidacja parametrów w `alif_dt.py` razem z `hold1`;
   - blokada dt ≠ 1 na początku `v5v41.simulate`;
   - blokada w `cl_runner.configure` (między liniami 32 i 33);
   - T9 przepięte na mapę wersji;
   - `test_guards_dt.py`;
   - regresja.

   Szczegóły i warunki: raport red teamu, pkt 13.
4. **Prawdziwe ramię tylko po decyzji właściciela.** Kolejność: najpierw pad i bezpieczeństwo (`pad_so101/`), potem obrót podstawy przez SNN.
5. **Etap N (N1 DATA, N2 DATA vs SWS) po pokazie** albo tylko wtedy, gdy zostanie czas. Pokaz go nie potrzebuje: wszystkie wyniki liczono przy dt = 1 ms.
6. **Do grudnia żadnych nowych organizmów** (mrówka, pszczoła).

**Uwaga do zewnętrznego planu „kostka jako główny obiekt”:** w scenie MuJoCo **nie ma kostki** (audyt Stage 1 faza 0, 2026-11-03). Jest tylko piłeczka. Kostkę trzeba by dodać, a enkoder rozpoznaje kolor, nie kształt.

## 11. Zasady techniczne (obowiązują, dopóki właściciel ich nie zniesie)

**Uruchamianie:**
- Zawsze `.venv/bin/python -I -B`.
- Nigdy nie importować `bio2` bez `-B`. Nigdy nie edytować plików zamrożonych Stage 1 (bio2: `brain.py`, `snn.py`, `scene2.py`, `vision.py`, `retina.py`, `circuit_bio2.json`, `assets/so101_upstream.xml` i inne).

**Integralność:** `.venv/bin/python -I -B flymind/integrity_v5v41.py --compare flymind/results/v5v41/integrity_baseline.json`. Wynik z 2026-11-07, już po utworzeniu tego pliku:

```
Stage 1 28/28; manifests v5v3_manifest.json 18/18, v5v4_manifest.json 18/18; protected files 377 tree dfcabd78f1484c96 | vs baseline: changed 0 | INTEGRITY OK
```

**Pliki przypięte lub chronione:**
- **nie zmieniać:** `alif.py`, `loop.py`, `loop_v2.py`, `v4_open_loop.py`;
- **nie zmieniać:** drzewa `flymind/validation/`, `results/v5v3`, `results/v5v4`, `data/`, `assets/`, `bio2/`;
- **zmiana tylko za zgodą:** `v5v41.py`, `cl_runner.py`.

**Bez wyraźnej zgody właściciela nie wolno:**
- commitować;
- uruchamiać Etapu N, porównań DATA vs SWS, eksperymentów LC×LC i synchronii;
- stroić ani trenować;
- sterować sprzętem;
- instalować pakietów;
- usuwać plików ani robić resetów;
- nadpisywać niezapisanych zmian właściciela;
- zmieniać `v5v41.run_network`, `cl_runner.configure`, `loop.py` i skryptów pętli zamkniętej.

Nowe analizy robić w scratchu.

**Metodyka:**
- nie przedstawiać korelacji jako przyczyny;
- nie ukrywać wyników negatywnych;
- nie zmieniać progów po zobaczeniu wyników;
- protokół i ziarna rejestrować **przed** uruchomieniem;
- red team każdego etapu.

**Pracę dzielić na subagentów** (Sonnet do cięższych zadań, Haiku do lekkich), zawsze sprawdzać ich wyniki i odsyłać poprawki.

## 12. Ziarna losowe (szczegóły w rejestrach; przed użyciem zawsze sprawdzić rejestr)

**Rejestry:**
- `program_v5v41/SEED_REGISTRY.md`;
- `experiments/fj1_fly_jaw/SEED_REGISTRY.md`;
- `experiments/fj2_fly_arm/SEED_REGISTRY.md`;
- rejestry w `experiments/f1_active_sensing/`.

**Zakazane i zużyte (REPORTED):**
- bio2: 0–39 (odłożone), 300–399 (300–323 zarezerwowane na fazę 2 CX, nieuruchomione), 200–235 (dev);
- flymind dev: 1001–1999 (zakaz ponownego użycia);
- 2001–2005, 2011–2050, 2051–2100, 3001–3100, 4001–4450 (z przesunięciami +100 000, +200 000, +400 000);
- 5001–5003, 6001–6002;
- RNG 7001, 7002, 7101, 9401, 9402, 9501;
- program: 8 410–8 446, 8 490–8 499, 8 600–8 700;
- F1: 910 xxxx – 912 xxxx (część jako rezerwacje);
- FJ1: 9 201 xxx, 9 208 xxx, 9 209 xxx;
- FJ2: 9 211 001–020, 9 218 xxx, 9 219 xxx;
- kamera: 15 5xx xxx (zarezerwowane, nieużyte).

## 13. Mapa dokumentów

| Co | Gdzie |
|---|---|
| Plan walidacji i dziennik | `flymind/VALIDATION_PLAN.md`, `flymind/AUTONOMOUS_RESEARCH_LOG.md` |
| Odtwarzanie | `flymind/REPRODUCE.md`; `flymind/NEXT_SESSION.md` (**nieaktualny, stan z 2026-10-29/30**) |
| Program V5v4.1 → V6m3 | `flymind/program_v5v41/FINAL_REPORT.md` |
| Etap 0 | `flymind/program_stage0/STAGE0_PROTOCOL.md`, `STAGE0_REPORT.md`, `results/stage0/` |
| FJ1 / FJ2 | `flymind/experiments/fj1_fly_jaw/`, `flymind/experiments/fj2_fly_arm/` |
| Pokaz | `flymind/demo/` |
| Teleoperacja | `pad_so101/NAGRYWANIE.md`, `pad_so101/PLAN.md` |
| Raporty ogólne | `reports/` (inwestorzy, hybrydowe mózgi, VLA, konektom dla SO101) |
| Kopia zapasowa (2026-11-02) | `/Users/Shared/FlyMind_backups.noindex/2026-11-02/`. Zawiera też raporty D1–D3 i Stage 1 fazy 0 |
| Deep Audit 2026-11-07 | `/private/tmp/claude-501/-Users-admin-so101-fly-project/db874248-72f1-4c43-9d3a-4f817520f8ff/scratchpad/deep/FLYMIND_DEEP_AUDIT.md` |
| Red team zabezpieczeń 2026-11-07 | `/private/tmp/claude-501/-Users-admin-so101-fly-project/db874248-72f1-4c43-9d3a-4f817520f8ff/scratchpad/redteam/FLYMIND_GUARDS_REDTEAM.md` |

**Uwaga:** dwa ostatnie raporty leżą w katalogu tymczasowym `/private/tmp`. **Mogą zniknąć po restarcie komputera.** Nie ma ich w repozytorium ani w kopii zapasowej.

## 14. Stan gita (VERIFIED 2026-11-07)

- Gałąź `flymind/fly-first-control`. Ostatni commit `54155d4` (2026-11-03, red team T2L→T2R).
- Niezapisane zmiany śledzonych plików: `flymind/REPRODUCE.md`, `flymind/VALIDATION_PLAN.md`.
- `git status` w `flymind/`: 126 wpisów, w tym 2 zmienione pliki; reszta to wpisy nieśledzone, m.in., m.in. wszystkie skrypty i wyniki V5v3 → V6m3, Etap 0, `demo/`, `cl_runner.py`, `integrity_v5v41.py`. Do tego `pad_so101/` i ten plik.
- Brak zdalnego repozytorium. Kopia poza komputerem nie istnieje (właściciel odmówił 2026-11-02, „może GitHub później”).

## 15. Szacunki postępu (tylko orientacyjnie; to nie pomiar)

- Zewnętrzna ocena z 2026-11-07: ok. **40%** planu grudniowego.
  - Konektom 75%, SNN 60%, synchronia, κ i szum 65%, Etap 0 50%, MuJoCo 45%, dotyk 20%, walidacja 25%, gotowość pokazu 20%.
- Szacunek autora z 2026-11-03 (inne wagi): inżynieria ok. 28%, biologia ok. 15%, walidacja ok. 30%, gotowość symulacji ok. 10%, sprzęt ok. 3%.
- Obie liczby to oceny, nie wynik testu. Nie da się ich zweryfikować.
