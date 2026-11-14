# FlyMind F1 — etap 1: ruch czuciowy w pętli zamkniętej (PROJEKT d3 (po red teamie r1 i r2: `redteam/stage1_design_redteam_r1.md`, `_r2.md`), niezatwierdzony, nic nie uruchomiono)

Data: 2026-11-01. Status: **projekt do przeglądu**. Nie ma kodu, przebiegów ani zmian w plikach chronionych. Implementacja i uruchomienie
wymagają osobnej zgody. Etykiety twierdzeń jak w `RAPORT_F1_PL.md`: [KOD] [LIT] [ZAŁ] [HIP] [WYNIK] [NZW]. Wszystko dotyczy MODELU, nie muszki.

## 0. Skąd ten etap i czego NIE testuje
Etap 0 (otwarta pętla) pokazał trzy rzeczy:
- obrót kamery 4° podnosi BSC DATA o +0,10, co odpowiada ≈ 1,4 cm progu odległości, a wynik jest odporny w 4 wariantach;
- ten sam zysk dają sieci tasowane, próg z filtrem dolnoprzepustowym i gładki ruch losowy (F-b, F-c, F-d);
- mechanizm to wzmocnienie enkodera zależne od ekscentryczności × ostry próg **[WYNIK]**.

Reguła §9 protokołu pozwala rozważyć etap 1 **wyłącznie jako test korzyści z wypukłości progu**. Etap 1 jest więc pytaniem
inżynierskim, a nie biologicznym, i nie testuje specyficzności konektomu (to zostało obalone w etapie 0).

**Pytanie etapu 1:** czy mały, sterowany ruch czujnika poprawia w pętli zamkniętej naprowadzanie robota (w symulacji) na słaby cel,
którego kamera stacjonarna często nie wykrywa? Jaki jest koszt w latencji, dokładności końcowej i fałszywych skrętach? Czy ruch
psuje naprowadzanie na cele silne?

## 1. Fakty z kodu, które wyznaczają projekt (audyt tej sesji)
1. **Kamerę w poziomie obraca tylko podstawa (shoulder_pan, staw 0) [WYNIK, sonda FK].** Przy +4° w Q_POSE:
   - pan: Δyaw −4,00°;
   - shoulder_lift, elbow_flex, wrist_flex: tylko pochylenie (Δpitch −4°);
   - wrist_roll: obrót obrazu wokół osi optycznej (Δyaw 0, Δpitch 0).

   Ruchu czuciowego nie da się więc fizycznie oddzielić na inny staw. Ruch czuciowy i ruchowy dzielą ten sam staw.
2. **Paralaksa [WYNIK, sonda FK]:** kamera jest 25,8 cm od osi podstawy. Obrót podstawy o 4° przesuwa kamerę o 1,5 cm i zmienia namiar
   celu (ρ 0,28 m, az 10°) o **7,1°**, a nie o 4°. Wzmocnienie namiaru zależy od ρ. Amplitudę ruchu podstawy trzeba więc dobrać
   do amplitudy namiaru, a nie przepisać 4° z etapu 0.
3. **Pętla V5 [KOD loop.py:96–163]:**
   - obraz → bramka → enkoder → LC10a → sieć → DNa02 → `SteerDecoder` (τ_rate 50 ms, τ 0,1 s, gain 2,5 1/s, w_max 1 rad/s);
   - → `integrate_pan` → `SafetyLayer` → serwo;
   - `pan_t = qt[0]` po warstwie bezpieczeństwa (bez wind-up).
4. **Warstwa bezpieczeństwa [KOD safety.py:39–50, 113–131]:**
   - v_max 1,5 rad/s;
   - max_lead podstawy **0,02 rad (1,15°)** — cel nie może wyprzedzać zmierzonej pozycji o więcej;
   - przy obrazie starszym niż 50 ms staw 0 jest trzymany.

   Ruch czuciowy musi przejść przez tę warstwę bez zmian w niej (plik chroniony). Rzeczywista amplituda będzie mierzona, nie zakładana.
5. **Pasmo pętli ruchowej [WYNIK, poprawione po red teamie r1]:** w d1 twierdziłem, że przecięcie wynosi ≈ 0,4 Hz. To było błędne:
   - wzmocnienie pętli to 2,5 × g_b ≈ 4–6 1/s;
   - w zapisanych próbach V5 (delay 0, DATA, 40 prób; `results/v5/v5_confirm_20261028T220223.json`) ω ma dominującą składową
     **2–3 Hz** (rms do 0,34 rad/s) dla bliskich celów (ρ < 0,20 m), czyli cykl graniczny pętli — sprawdzone niezależnie;
   - sukces V5 w tym zakresie: 38/40.

   Pętla sama „skanuje” szybciej niż planowany ruch czuciowy. f nie jest wybierane z argumentu o paśmie, tylko regułą R5 (§8)
   z pomiaru wykonalności F3, spośród {0,5; 1} Hz (w etapie 0 obie dały +0,103).
6. Brak pamięci w enkoderze i brak estymaty namiaru wewnątrz SNN [KOD]. Nie ma czego „korygować” kopią eferentną po stronie czuciowej.
   Separacja odbywa się na poziomie poleceń (§3).

## 2. Hipotezy (kierunek ustalony z góry; d2)
Wszystkie testy liczone na surowym e w oknie 5,5–6,0 s, gdzie θ_s = 0 we wszystkich warunkach (§3), chyba że zaznaczono inaczej.
Δ(X) = sukces(X, sin) − sukces(X, none) na zakresie W.
- **H1-S1 [HIP]:** Δ(DATA) ≥ SESOI 0,10 (10 punktów procentowych).
- **S1 [HIP: równoważność]:** sukces DATA sin − sukces DATA jvel.
- **S2, S3 [HIP: równoważność]:** Δ(DATA) − Δ(B1) i Δ(DATA) − Δ(SWS) (różnica różnic).
- **S4 [HIP: równoważność]:** Δ(DATA) − Δ(TH_LP-ster).
- **S5 (szkoda, zakres S):** non-inferiority — DATA sin nie gorszy od DATA none o więcej niż 0,05 w sukcesie ORAZ o więcej niż 1°
  w średnim |e| końcowym. HARMFUL, jeśli dla którejkolwiek miary dolna granica CI95 szkody > 0 i estymata ≥ margines (poprawka r2);
  „nieszkodliwy”, jeśli obie górne granice < margines; inaczej nierozstrzygnięty. Test nie podlega bramce mierzalności, bo sukces V5 w zakresie S wynosi ≈ 0,95 (sufit).
- **S6 (fałszywe skręty, próby N):** pan_t końcowe |·| > 5° lub Σ|Δpan_t| > 10°. Oczekiwane zero zdarzeń, więc zamiast bootstrapu:
  pary niezgodne b (fałszywy skręt tylko z sin) i c (tylko z none), szkoda = (b − c)/n. CI95 dokładny warunkowy: p_b z przedziału
  Cloppera–Pearsona dla b z (b + c), przeliczony na (b + c)/n·(2p_b − 1). HARMFUL, jeśli dolna granica > 0 i estymata ≥ 0,05;
  „nieszkodliwy”, jeśli górna < 0,05; inaczej nierozstrzygnięty.
- **S7 [HIP: równoważność]:** sukces gated − sukces sin (W). Mniejszy koszt śledzenia (surowe |e| w 3,0–4,75 s) dla gated wynika
  z konstrukcji — po wykryciu ruch ustaje (r2) — więc jest raportowany tylko opisowo. Pytanie testowe: czy wyłączanie ruchu
  po wykryciu nie zabiera korzyści.
- **S8 [HIP]:** Δ(DATA, virtual) − Δ(DATA, sin) — różnica różnic. Czy paralaksa i serwo zmieniają korzyść?
- **S9 [HIP]:** Δ(DATA, mt) − Δ(DATA, sin). Czy ruch świata o tej samej amplitudzie obrazu działa jak ruch własny (etap 0: tak)?
- **S10 (szkoda: oscylacja pętli ruchowej):** §3.
- Holm: S1–S4 i S7–S9 (7 testów; S7 jest teraz testem równoważności sukcesu). Testy szkody S5, S6, S10 są oceniane osobno, bez korekty (konserwatywnie dla bezpieczeństwa).

## 3. Generowanie ruchu i oddzielenie pętli czuciowej od ruchowej
Polecenie dla stawu 0 w takcie k:

    pan_t   ← integrate_pan(pan_t, ω_k, DT)          # pętla RUCHOWA: całkuje wyłącznie ω z dekodera
    q0_cmd  = pan_t + θ_s(k)                          # θ_s: znana trajektoria czuciowa (sterowana w otwartej pętli)
    qt      = SafetyLayer(q0_cmd, …)                  # niezmieniona warstwa bezpieczeństwa
    pan_t   ← qt[0] − θ_s(k)                          # kopia eferentna na poziomie polecenia: integrator nie „widzi” θ_s

- Ostatni wiersz zastępuje `pan_t = qt[0]` z V5. Bez odjęcia θ_s integrator sumowałby sinusa i dryfował. Red team r1 to potwierdził
  sondą fizyki: bez odjęcia dryf do 37,8° i 444 flagi rate; z odjęciem reszta 1e-15, 0 flag. Śledzenie serwa: max |polecenie − q|
  0,16° przy 1 Hz i A 2,3°. Limit lead 1,15° jest osiągany tylko przy ω w nasyceniu (1,03–1,08°).
- Takt z flagą `vision_stale` lub `cmd_timeout` (warstwa trzyma prev[j], a pan_t pochłonąłby −Δθ_s) **unieważnia próbę**. Takie
  próby są liczone i raportowane; > 1 % prób w etapie → STOP. Jednostka z jakąkolwiek nieważną próbą jest wyłączana ze WSZYSTKICH
  testów (listwise), żeby zachować parowanie.
- Ograniczenia bezpieczeństwa (rate, lead, zakres) działają na sumę.
- Obcięcie przez warstwę bezpieczeństwa trafia do integratora tak samo jak w V5 (bez wind-up).
- Pętla czuciowa jest więc rozdzielona od ruchowej przez znane θ_s.
- Dekoder i SNN nie dostają kopii eferentnej. Model jej nie ma; dodanie jej to osobne pytanie (etap 2).

Trajektorie θ_s:
- `none`: θ_s = 0 — punkt odniesienia; przy braku szumu pikseli bit w bit V5.
- `sin`: A_pan·sin(2πft + φ_u), f z reguły R5. **A_pan liczone osobno dla każdej próby:** A_pan = 4° / g_b(ρ, az0), gdzie g_b to
  pochodna namiaru po kącie podstawy z FK w pozie startowej (różnica skończona ±0,5°, deterministyczna). Amplituda namiaru wynosi
  więc 4° dla każdego celu, jak w `virtual` i `mt`. Poprawka r1: jedna mediana dawała 4,6° przy ρ 0,22 i 3,6° przy ρ 0,36, czyli
  najsłabszym celom najsłabszy bodziec. g_b maleje, gdy podstawa się obraca (1,78 przy pan 0, 1,40 przy 30°); przy |az0| ≤ 16° zmiana
  jest mała. Rzeczywista amplituda namiaru zapisywana w każdej próbie.
- **Wszystkie trajektorie ruchu** (sin, jvel, gated, virtual, mt) są mnożone przez tę samą obwiednię: 1 w 0–4,75 s, rampa cosinusowa
  do zera w 4,75–5,5 s. Okno oceny 5,5–6,0 s ma więc θ_s = 0 we wszystkich warunkach. Dopasowanie RMS jvel (przemieszczenie i prędkość)
  liczone w 0,75–4,75 s przed obwiednią. Bramkowanie `gated` (wyłącz/włącz z rampą 0,25 s) mnożone przez obwiednię.
- `jvel`: gładki ruch losowy jak J_vel w etapie 0 (filtr gaussowski, dopasowane RMS przemieszczenia i prędkości ±20 %, okno = cała próba).
- `gated`: sinus włączony od startu. Gdy |ω| po raz pierwszy przekroczy ω_on, amplituda maleje liniowo do zera w ciągu 0,25 s.
  Faza nie jest dopasowywana, a θ_s jest odejmowane od integratora (§3), więc skok nie trafia do pętli ruchowej. Ponownie włączany
  (rampa 0,25 s), gdy |ω| < ω_on przez 1 s. ω_on z reguły R3.
- `virtual`: ruch kamery jak w etapie 0 (cam_quat w pamięci, obrót wokół pionu przez środek optyczny) o amplitudzie namiaru 4° i f z R5.
  Podstawa sterowana normalnie. Niefizyczne; służy jako pomost do etapu 0.
- `mt` (zewnętrzny ruch o tej samej amplitudzie obrazu): podstawa bez ruchu czuciowego. W każdym takcie piłeczka stoi w odległości
  poziomej, jaką ma pozycja statyczna od BIEŻĄCEJ pozycji kamery, pod kątem świata kierunku do pozycji statycznej + δ(t),
  δ = 4°·sin(2πft + φ_u)·obwiednia. Modulacja namiaru względem bieżącej kamery wynosi więc dokładnie ±4°, a w oknie oceny piłeczka
  jest w pozycji statycznej. Rozróżnia ruch własny od ruchu świata. Piłeczka ma freejoint, a fizyka jest krokowana,
  więc w każdym takcie ustawiane są qpos i qvel = 0 przed `sim.step()`. Wykonalność (F5) sprawdza, że piłeczka nie spada, nie toczy się
  i nie ma kontaktu z chwytakiem.

Ruch użyteczny a niekontrolowany — definicja operacyjna (zamrożona; poprawiona po r1, liczona na surowym e, nie na e_m):
- **użyteczny**: H1-S1 SUPPORTED, a S5, S6 i S10 nie HARMFUL;
- **niekontrolowany / szkodliwy**: S5, S6 lub S10 HARMFUL.
  S10 = wzrost amplitudy składowej f w pan_t (pętla ruchowa, bez θ_s) względem sparowanej próby `none`. Estymator (poprawka r2):
  - okno 0,75–4,75 s (4 s = 2 okresy przy 0,5 Hz, 4 przy 1 Hz, bez przecieku);
  - pan_t po usunięciu trendu liniowego;
  - lock-in: amplituda = 2·|mean(pan_t · e^{−i(2πft + φ_u)})|, z tym samym φ_u w próbie `none` tej jednostki.

  Liczone osobno dla W i S. HARMFUL, gdy w którymkolwiek zakresie dolna granica CI95 > 0 i estymata ≥ 1°. Odniesieniem jest `none`,
  więc własny cykl graniczny pętli (2–3 Hz) się nie liczy.

## 4. Zadanie, bodźce, sterowniki
- **Próba:** 6 s (600 taktów po 10 ms, SNN 10 × 1 ms na takt), start z pan 0 w Q_POSE, piłeczka statyczna (poza `mt`).
  Szum pikseli σ 10 jak w etapie 0, wspólny dla wszystkich sterowników (dodawany między `observe` a enkoderem).
- **Zakres słaby (W, główny):** ρ ~ U[0,22; 0,36] m, |az0| ~ U[8°; 16°], strona losowa, faza φ ~ U[0, 2π). Etap 0 dał tu
  BSC DATA stacjonarnie 0,33.
- **Zakres silny (S, kontrola szkody):** zakres V5: ρ ~ U[0,16; 0,24], |az0| ~ U[10°; 30°].
- **Bez celu (N):** piłeczka zaparkowana poza kadrem (jak w etapie 0).
- **Sterowniki:**
  - `DATA` — sieć z danych; dekoder kalibrowany procedurą `v5v4.calibrate` z nowymi ziarnami;
  - `B1`, `SWS` — po 10 świeżych instancji, kalibrowane tak samo;
  - `TH_LP-ster` — sterownik progowy bez SNN, w pełni określony z góry, w **tej samej postaci co TH_LP etapu 0**
    (`systems.py:55–64`; poprawka r2: binarne u ∈ {−1, 0, 1} z d2 było regulatorem ze strefą martwą — przy ρ 0,30 / az 8° oba napędy
    leżą poniżej progu, a przy ρ 0,16 oba powyżej, więc u = 0):
    - y_s = filtr 1. rzędu τ_LP = 20 ms z 12·g_s mV;
    - u = max(0, y_L − θ_LP) − max(0, y_R − θ_LP), θ_LP = 5,93 mV (etap 0) — ciągła różnica nadwyżek nad progiem;
    - u → filtr τ 0,1 s → ω = clip(gain · u_f / slope_TH, ±w_max), gain i w_max jak `classical_p`;
    - slope_TH: nowa funkcja w `stage1/` — ta sama procedura i bodźce syntetyczne co `loop.calibrate_p`, ale na sygnale u
      (`calibrate_p` nie ma miejsca na próg; plik chroniony pozostaje bez zmian).
    - **Bramka pilotażu:** jeśli sukces TH_LP-ster/none w W ∉ [0,1; 0,9], to S4 = „nieprzeprowadzony” (p = 1 w Holmie), a raport
      porównuje go tylko opisowo. Brak zmiany parametrów po obejrzeniu danych.

    Wariant wrażliwości (wtórny, opisowy, poza Holmem): τ_LP = 60 ms, θ dopasowane do BSC DATA w spoczynku na danych etapu 0;
  - `P` — `classical_p` z V5, kontrola liniowa.
- **Macierz (na jednostkę):**

| Sterownik | Ruch | Zakres |
|---|---|---|
| DATA | none, sin, jvel, gated, virtual, mt | W, S, N |
| B1, SWS | none, sin | W, N |
| TH_LP-ster | none, sin, jvel | W, S, N |
| P | none, sin | W, S, N |

  Daje to 18 + 4 + 4 + 9 + 6 = 41 prób na jednostkę.

## 5. Miary
- **Główna (d2, po r1):** sukces naprowadzenia = |e| < 5° przez ostatnie 0,5 s (5,5–6,0 s), `loop.metrics`, e = surowy namiar
  z prawdy symulatora. W tym oknie θ_s = 0 we wszystkich warunkach (rampa §3), cam_quat jest oryginalny, a piłeczka stoi w pozycji
  statycznej. Miara jest więc identyczna dla wszystkich warunków i nie ukrywa kosztu ruchu.
- Wtórnie: e_m = namiar w pozie ruchowej (FK z q0 − θ_s) w czasie trwania ruchu.
- **Wtórne:**
  - czas do pierwszego |e| < 5°;
  - latencja pierwszej decyzji: pierwsze |ω| > 0,05 rad/s z właściwym znakiem;
  - błąd końcowy (średnie |e| w 5,5–6,0 s);
  - koszt śledzenia (średnie surowe |e| w 3,0–4,75 s, S7);
  - przeregulowanie;
  - amplituda składowej f i 2–3 Hz w pan_t w 2–4,75 s (S10);
  - flagi warstwy bezpieczeństwa (rate, lead) na próbę;
  - osiągnięta amplituda θ_s i namiaru;
  - fałszywy skręt w próbach N (S6): |pan_t(koniec)| > 5° lub Σ_k |pan_t(k) − pan_t(k−1)| > 10° (pan_t = integrator bez θ_s).
- **Neuronowe (opisowe):** impulsy LC10a ipsi, DNa02 L/R, synchronia, fazowe przywiązanie do θ_s.

## 6. Statystyka (d2)
- Jednostka = (bodziec, ziarno ALIF, szum pikseli), parowana między warunkami. Ten sam ciąg szumu ALIF we wszystkich sieciach (CRN).
- Bootstrap sparowany po jednostkach, 10 000 replikacji; dla B1/SWS hierarchiczny (instancje, potem jednostki).
- Klasyfikacja testów H1-S1, S1–S4, S7–S9 jak w §8 protokołu etapu 0:
  - kolejność SUPPORTED → HARMFUL → EQUIVALENT → DETECTABLE-BELOW-SESOI → UNMEASURABLE → INCONCLUSIVE;
  - SESOI jest parametrem: **0,10 dla odsetków sukcesu** (wszędzie, gdzie protokół etapu 0 miał 0,07).
- Testy szkody S5, S6, S10 — własne reguły w §2 i §3 (non-inferiority, dokładne granice), bez bramki mierzalności.
- H1-S1: jeden test, α 0,05 dwustronnie. Holm nad S1–S4, S7–S9 (7). Test nieprzeprowadzony wchodzi z p = 1.
- **Mierzalność (jedna definicja):** ramię ważne, gdy odsetek sukcesu ∈ [0,1; 0,9] (jak etap 0). Dotyczy zakresu W.
  Pilotaż celuje w środek (R1).
- **Moc (poprawki r1, r2):** n z symulacji R2 (§8). Przy niezgodności par ~0,3 SE ≈ 0,039 dla n = 200 (moc ≈ 0,75 przy
  0,10), a ≈ 0,055 dla różnicy różnic. Testy równoważności przy ±0,10 mogą wyjść INCONCLUSIVE nawet przy n = 400 — to jest
  zaakceptowane i będzie raportowane jako ograniczenie, a nie powód do zwiększania n poza 400.

## 7. Etapy
1. **1-F wykonalność** (ziarna smoke, bez analizy wnioskowania):
   - **F1** test równoważności: nowy runner z θ_s = 0 i bez szumu pikseli daje e_deg i ω bit w bit jak `loop.run_trial` (5 ziaren smoke).
   - **F2** śledzenie: rzeczywista amplituda θ_s ≥ 0,9·A_pan; flagi „lead” ≤ 5 % taktów. Jeśli nie, A_pan lub f się NIE zmienia
     po cichu — STOP i decyzja użytkownika.
   - **F3** stabilność i wybór f: zakres S i W, DATA, `none` vs sin przy f = 0,5 i 1 Hz, po 20 prób (ziarna smoke).
     Mierzone: S10 (lock-in) i widmo ω. Diagnostyka: ten sam ruch z ω = 0 (pętla ruchowa wyłączona) — rozdziela
     odpowiedź serwa od sprzężenia z dekoderem.
   - **F4** czas: s/próbę ⇒ budżet.
   - **F5** `mt`: odchylenie pozycji piłeczki od zadanej < 1 mm, brak kontaktów. `virtual`: cam_quat przywracany po każdym renderze,
     a FK oceny liczone z oryginalnym cam_quat.
2. **1-P pilotaż** (60 świeżych jednostek): ustala n, ewentualny zakres W i ω_on. Wyniki eksploracyjne, bez CI wnioskowania.
3. **1-C potwierdzenie** (n z pilotażu, świeże jednostki): testy §2.
4. **Analiza, wykresy, nagranie** (porównanie none vs sin: obraz, θ_s, pan, e(t), raster, ω) i raport PL.
   Potem STOP — sprzęt SO-101 wyłącznie po osobnej zgodzie i osobnym protokole (etap 2).

## 8. Reguły (mechaniczne, zamrożone przed wykonalnością i pilotażem; d2)
- **R5 f (z F3):** spośród {0,5; 1} Hz wybierane jest f o mniejszym średnim przyroście S10 (estymator lock-in) względem `none`,
  uśrednionym po zakresach W i S (po 20 prób na f i zakres, ziarna smoke). Remis (różnica < 0,2°) → 1 Hz. Jeśli oba przyrosty > 1° → G-d,
  STOP. R5 używa wyłącznie ziaren smoke, a jego dane nie wchodzą do żadnego testu.
- **R1 zakres W:** jeśli sukces DATA/none w pilotażu ∉ [0,15; 0,6], W := ρ ~ U[ρ₅₀ − 0,07; ρ₅₀ + 0,07]. ρ₅₀ liczone estymatorem
  Spearmana–Kärbera jak w etapie 0: ρ₅₀ = 0,22 + sukces × 0,14 (zakres jednostajny). Bez dopasowania logistycznego (r1: szum przy n = 60).
- **R2 n (poprawka r2, symulacja):**
  - dla n ∈ {200, 250, 300, 350, 400}: 2000 symulacji (RNG analizy pilotażu 9 115 001), w każdej losowanie n jednostek z pilotażu
    ze zwracaniem — dla B1/SWS hierarchicznie (instancje, potem jednostki), z wariancją między instancjami z pilotażu;
  - w każdej symulacji pełna analiza: bootstrap, Holm nad 7 testami, równoważność jako CI90 w ±0,10 (TOST);
  - n = najmniejsze n z mocą H1-S1 ≥ 0,8 (zakładając efekt = SESOI, gdy efekt pilotażu < SESOI); gdy żadne n ≤ 400 tego nie
    spełnia, n = 400;
  - przed potwierdzeniem raportowana jest moc wszystkich testów przy wybranym n. Przy 5 + 5 instancjach pilotażu wariancja między
    instancjami jest szacowana słabo — ograniczenie raportowane.
- **R3 ω_on:** 99. percentyl |ω| DATA w próbach N z sin (pilotaż), zaokrąglony w górę do 0,01 rad/s, nie mniej niż 0,10 rad/s
  (r1: w d1 dolna granica 0,05 była równa progowi latencji).
- **R4:** TH_LP-ster ustalony z góry (§4), bez dopasowania.
- Brak innych decyzji po obejrzeniu danych.

## 9. Warunki niepowodzenia i interpretacja (opisowe)
- **G-a:** H1-S1 nie SUPPORTED → ruch czuciowy nie pomaga w pętli zamkniętej (np. pętla ruchowa sama „skanuje” albo paralaksa
  i serwo psują efekt).
- **G-b:** S5, S6 lub S10 HARMFUL → ruch szkodzi; wynik negatywny niezależnie od H1.
- **G-c:** S4 EQUIVALENT → zysk jest właściwością progu, nie SNN (oczekiwane; potwierdza etap 0).
- **G-d:** R5 nie znajduje f (oba przyrosty > 1°) → sprzężenie z pętlą ruchową; etap 1 kończy się na wykonalności.
- **G-e:** S8 (różnica różnic virtual − sin) SUPPORTED → korzyść z etapu 0 nie przenosi się w pełni na fizyczny ruch podstawy.
- **G-f:** sukces DATA/none w W > 0,9 mimo R1 → pętla sama skanuje (cykl graniczny); pytanie bezprzedmiotowe w tym zakresie.
- **Rekomendacja testu sprzętowego (etap 2)** tylko gdy: H1-S1 SUPPORTED, nie G-b, nie G-d, F2 OK. Nawet wtedy jako zachowanie
  inżynierskie („skanuj, gdy nic nie widzisz”), z TH_LP-ster jako równoprawną alternatywą.

## 10. Ziarna (zarezerwowane, nieużyte; skan kolizji 9 111 xxx–9 119 xxx: 0 trafień)
| Pula | Użycie |
|---|---|
| 9 111 001–060 | pilotaż 1-P, jednostki |
| 9 112 001–400 | potwierdzenie 1-C, jednostki (pierwsze n) |
| 9 113 001–010 / 9 113 101–110 | instancje B1 / SWS (potwierdzenie) |
| 9 113 201–205 / 9 113 301–305 | instancje B1 / SWS (pilotaż) |
| 9 114 001–003 | kalibracja dekoderów (wszystkie sieci, ta sama procedura) |
| 9 115 001–003 | RNG analizy (pilotaż, potwierdzenie, zapas) |
| 9 118 001–099 | smoke / testy / wykonalność 1-F |
| 9 119 001–999 | red team |

Strumienie na jednostkę jak w etapie 0: ALIF u; szum pikseli default_rng([u,1]); bodziec default_rng([u,2]) w kolejności
ρ, |az|, strona, φ; jvel default_rng([u,3,crc32(nazwa)]).

## 11. Implementacja (po zgodzie) i ochrona plików
- Nowe pliki wyłącznie w `experiments/f1_active_sensing/stage1/`:
  - `cl_sense.py` — pętla jak `loop.run_trial`, złożona z tych samych zamrożonych modułów (SO101Sim, SensoryGate, TargetEncoder,
    ALIF, SteerDecoder, SafetyLayer, integrate_pan), z θ_s, szumem pikseli, trybami virtual/mt i zapisem miar;
  - `runner1.py`, `analysis1.py`, `figures1.py`, testy.
- `loop.py`, `safety.py`, `decoder.py`, `encoder.py`, `so101.py`, dane, wagi, parametry ALIF — bez zmian.
  Kontrola: integrity_v5v41 i integrity_f1 przed i po każdym etapie. Test F1 wiąże nową pętlę z zamrożoną.
- Manifesty z hashami jak w etapie 0, zapis atomowy, `python -I -B`, brak bio2, brak commitów.

## 12. Budżet (do potwierdzenia w F4) [ZAŁ, poprawione po r1]
Render jest ograniczony przez GL (~240 klatek/s łącznie, niezależnie od liczby procesów; pomiar z etapu 0), a w pętli zamkniętej
nie ma cache. 41 prób × 600 klatek = 24 600 klatek/jednostkę ≈ 100 s/jednostkę.
- pilotaż 60 jednostek ≈ 1,7 h;
- potwierdzenie 200 jednostek ≈ 5,7 h (400 ≈ 11 h);
- wykonalność ≈ 0,5 h.

## 13. Ryzyka i otwarte kwestie
- **Lead 0,02 rad:** sonda r1: śledzenie 0,16°, ale przy ω w nasyceniu + sinus lead dochodzi do 1,03–1,08° z 1,15°. Jeśli przekroczy, warstwa przytnie ruch
  czuciowy (F2). Zmiana limitu = zmiana pliku chronionego → wymaga zgody, nie jest planowana.
- **Paralaksa:** amplituda namiaru zależy od ρ. Raportowana per próba; analiza wtórna wg tercyli ρ.
- **Miara sukcesu:** surowe e w oknie bez ruchu (rampa) — wspólne dla wszystkich warunków. Koszt ruchu w trakcie śledzenia mierzy
  osobno S7 (surowe |e| w 3,0–4,75 s).
- **Cykl graniczny V5 (2–3 Hz) [WYNIK]:** pętla już oscyluje przy bliskich celach. Ruch czuciowy może się z nim sumować (S10)
  albo być zbędny (G-f).
- **Długość próby 6 s vs 3 s w V5:** baseline `none` jest mierzony w tym samym protokole; nie porównujemy z liczbami V5.
- **FA = 0 w etapie 0:** scena bez dystraktorów; S6 sprawdza fałszywe skręty, ale nie dystraktory (poza zakresem).
- **Kalibracja dekodera** nowymi ziarnami może dać inny slope DATA niż V4. Raportowany obok wartości V4; różnica > 10 % → STOP
  i decyzja użytkownika (przy cyklu granicznym 10 % zmiany slope zmienia wzmocnienie pętli o 10 %).
- **`mt`:** w każdym takcie qpos piłeczki oraz jej qvel (liniowe i kątowe) = 0; podstawa nadal jest sterowana, więc kamera się porusza
  (to zamierzone — ruch własny = tylko pętla ruchowa).

## 14. Poprawki implementacyjne d3.1 (przed jakimkolwiek przebiegiem poza ziarnami smoke; 2026-11-01)
- **A1:** pilotaż uruchamia `gated` z ω_on = 0,10 rad/s (dolna granica R3), bo R3 potrzebuje danych z pilotażu. Potwierdzenie używa ω_on z R3.
- **A2:** R2 w każdej z 2000 symulacji używa przedziału normalnego (SE z danych symulowanych) zamiast zagnieżdżonego bootstrapu
  (koszt). Test „rozstrzygający” w symulacji to SUPPORTED/HARMFUL przy α/7 albo EQUIVALENT (CI90 w ±0,10).
- **A3:** dekoder SNN ma offset 0 (jak V5), slope z `v5v4.calibrate` (ziarna 9 114 001–003). DATA: 501,33 Hz/rad, +1,2 % względem V4 →
  poniżej progu STOP 10 %.
- **A4:** bootstrap: `default_rng([ziarno z puli 9 115 00x, crc32(nazwa testu)])` — jedno zarejestrowane ziarno, osobny strumień na test.
- **A5:** parametry: `stage1_params.json` (przed pilotażem: f, kalibracje, zakresy) i `stage1_confirm_params.json` (reguły pilotażu,
  tryb x). Manifest każdego etapu zawiera sha256 obu plików, kodu stage1 i zależności; runner odmawia wznowienia po zmianie hashy.
- **A6:** latencja = pierwszy takt z |ω| > 0,05 rad/s w kierunku celu. Koszt śledzenia = średnie |e| w taktach 300–474 (3,0–4,75 s).
- **A7 (z wykonalności F2, przed pilotażem):** ruch startował skokiem θ_s(0) = A·sin φ. Warstwa bezpieczeństwa ucinała go limitem
  prędkości (1 flaga „rate” na próbę), a ucięta część zostawała w integratorze jako stałe przesunięcie podstawy (np. TH sin 17,09° vs
  TH none 14,58° przy braku ruchu). Poprawka: obwiednia ma też rampę cosinusową na starcie, 0–0,25 s. Wykonalność powtórzona
  (`results/feasibility2.json`); R5 stosowane do powtórzonych danych.
- **Wynik wykonalności (`results/feasibility2.json`, ziarna smoke, nie do wnioskowania):**
  - F1: bit w bit z `loop.run_trial` (SNN i P);
  - F2: amplituda namiaru 4,0–4,2°, śledzenie serwa ≤ 0,31°, 0 flag lead/rate, 0 prób nieważnych;
  - F5: mt — maks. odchylenie piłeczki 0,08 mm;
  - F4: ≈ 2,1 s na próbę (4 procesy), ≈ 90 s na jednostkę;
  - **R5:** przyrost S10 vs none — 0,5 Hz: W 0,29°, S 1,51° (śr. 0,90°); 1 Hz: W 0,14°, S 1,76° (śr. 0,95°). Różnica < 0,2° → **f = 1 Hz**;
    oba < 1° → G-d nie zachodzi.
- **Reguły pilotażu (mechanicznie, `results/analysis_pilot.json`, `stage1_confirm_params.json`):**
  - R1: sukces DATA/none w W = 0,317 ∈ [0,15; 0,6] → zakres bez zmian;
  - R3: ω_on = 0,10 rad/s (dolna granica; brak fałszywych skrętów w pilotażu);
  - R2: **n = 400** (maksimum). Moc H1 przy n 200–400 = 0,49–0,51; moc S1–S9 przy 400 = 0,80–0,97.
- **Wada R2 (wykryta po zastosowaniu; reguły nie zmieniam):** pilotaż dał Δ H1 = 0,100 = SESOI, więc symulacja zakłada efekt
  równy SESOI. Klasa SUPPORTED wymaga estymaty ≥ SESOI, a wtedy moc jest z konstrukcji ≈ 0,5 dla każdego n. Reguła powinna liczyć moc
  przy efekcie większym od SESOI albo kryterium „dolna granica > 0” — ograniczenie raportowane; H1 ma ~50 % szans na SUPPORTED nawet
  przy prawdziwym efekcie równym SESOI.
