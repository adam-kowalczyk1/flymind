# Co projekt FlyMind / SO-101 NAPRAWDĘ osiągnął (uczciwe zestawienie do jury i inwestorów)

Źródła: wyłącznie pliki lokalne w `/Users/admin/so101_fly_project` (ścieżki podane przy każdym twierdzeniu) oraz pliki pamięci w `/Users/admin/.claude/projects/-Users-admin-so101-fly-project/memory/`. Stan repozytorium: ostatni commit `bf05cb1`, 2026-11-03 15:40, gałąź `flymind/fly-first-control`. Nie oglądałem filmów z `flymind/demo/` (tylko ich nazwy i kod); wszystkich liczb nie przeliczałem od nowa, cytuję je z raportów projektu (raporty te mają własne red-teamy i niezależne reanalizy, o czym niżej).

**Najważniejsza korekta dla autora zapytania:** projekt NIE używa FlyWire. Dane to **MaleCNS v1.0** (Janelia FlyEM, samiec *Drosophila*, licencja CC-BY 4.0) — `RESULTS.md` s.1 i sekcja "Dane: MaleCNS v1.0"; `reports/Konektom muchy dla SO101.md`. FlyWire (samica) jest tylko źródłem porównawczej literatury (Collie i in.).

**Najważniejsze zdanie, które trzeba powtórzyć wszędzie:** *wszystko, co zmierzono, zmierzono w symulacji komputerowej (MuJoCo). Żaden wynik nie pochodzi z prawdziwego ramienia SO-101. Model to nie jest mózg muchy, tylko wycinek jej połączeń (kilkaset do kilku tysięcy neuronów) w symulacji.* Wprost: `RESULTS.md` s.9 ("Nic nie było sprawdzane na prawdziwym ramieniu"), `bio2/RESULTS.md` s.10 (to samo), `flymind/program_v5v41/FINAL_REPORT.md` (nagłówek: "no physical SO-101 arm was used"), `flymind/VALIDATION_PLAN.md` s.4 ("Sprzęt fizyczny — poza zakresem bez osobnej zgody"), `flymind/V5v4_FINAL_REPORT.md` §3 ("brak fizycznego ramienia").

---

## 1. Czym jest system?

### Takeaway
Ramię SO-101 (5 stawów + chwytak, serwa STS3215) jest w symulacji MuJoCo sterowane impulsową siecią neuronową (ALIF, krok 1 ms), w której połączenia (które neurony, ile synaps, znak przekaźnika) pochodzą z prawdziwego konektomu samca muchy MaleCNS v1.0; dynamika neuronów, kamera, enkodery i dekodery są naszym modelem/inżynierią. Są trzy generacje: (1) `sim/` + `RESULTS.md` (pościg + odruch chwytu), (2) `bio2/` (kamera, pamięć, łapanie rzuconej piłeczki), (3) `flymind/` (odizolowany, rygorystycznie walidowany kontroler "mucha steruje" + eksperymenty FJ1/FJ2).

### Cited Findings
- Sieć: 332 neurony i 53 766 synaps z MaleCNS + 20 neuronów modułu odruchu **modelowych**; wagi `W = sign(nt)·J0·ln(1+N_syn)`; membrana z modelu Shiu i in. 2024 (V_rest −52, V_th −45 mV, τ_m 20 ms, refrakcja 2,2 ms) — `RESULTS.md` (Architektura).
- Obwód pościgu (z danych): LC10a (135 L / 140 P) → AOTU019 (GABA) / AOTU025 (ACh) → DNa02 L/P. Liczby synaps np. LC10a_P→AOTU019_P 7595; AOTU019_P→DNa02_L 297; AOTU025_L→DNa02_L 205 — `RESULTS.md` (Dane); `reports/Konektom muchy dla SO101.md`. Układ "push-pull" z pracy Collie i in. potwierdza się w danych samca — `RESULTS.md`.
- Obwód odruchu nogi T1-L: 20 aferentów, 20 interneuronów, 11 motoneuronów z danych; moduł odruchu RR_assist/RR_gate/RR_and/RR_hold/RR_resist to 20 neuronów **naszego autorstwa** — `RESULTS.md` (Architektura; "Co jest z konektomu, a co nasze").
- Zbiór MaleCNS: 211 577 ciał, 151,9 mln połączeń, 311,8 mln synaps; publiczny, bez tokenu, ~1,1 GB — `RESULTS.md`; `reports/Konektom muchy dla SO101.md` (pomiar własny z 23.10.2026).
- `bio2`: dodano kamerę "oko w dłoni", cyfrową siatkówkę, pierścień kierunku (EPG), DN (DNa01/02, DNp01, DNp09, MDN), 220 neuronów mózgu + 72 VNC — `bio2/RESULTS.md` (Architektura).
- `flymind/` (obecny kierunek): tylko ścieżka wzrokowa LC10a → 147 neuronów pośrednich → DNa02 (424 neurony, 13 510 krawędzi) steruje obrotem podstawy (staw 0); wszystko oznaczone DATA / MODEL / ENGINEERING / CONTROL — `flymind/program_v5v41/FINAL_REPORT.md` (nagłówek); `flymind/REPRODUCE.md` (tabela warstw).
- FlyArm (`flymind/fly_arm.py`, commit 61ec6ed): sieć `vision_leg` (5643 neurony: LC9 → DNp09 → przekaźniki VNC → motoneurony nogi T2 L) steruje **stawami 1–2** ramienia (shoulder_lift ← Pleural remotor − Sternal anterior rotator; elbow ← Tr flexor − Tr extensor) i momentem szczęki (Ti extensor − Ti flexor). Każde przypisanie "mięsień nogi → staw ramienia" to **analogia ustalona przez nas** (mucha nie ma ramienia) — `flymind/fly_arm.py` (docstring); `flymind/experiments/fj2_fly_arm/DESIGN.md`.
- Kluczowy łańcuch naturalny odnaleziony w danych: LC9 (wzrok) → DNp09 (LC9 daje 1977 synaps z 15 940 wejść DNp09) → przekaźniki VNC → motoneurony T2 L; bezpośrednio do motoneuronów nóg tylko 18–24 synaps — memory `flymind-d1-audit-2026-11-03.md`.
- Kluczowe źródła literaturowe (nie z naszych pomiarów): Shiu i in. 2024 (parametry), Collie i in. 2025 (pościg), Azevedo i in. 2020/2024 (klasy motoneuronów), Ribeiro 2018 (pola LC10a) — `RESULTS.md` ("Z literatury").

### Inferences
- Poprawna formuła do jury: "model wycinka rzeczywistego konektomu muchy, ze strukturą połączeń z danych i parametrami z literatury, uruchomiony w symulacji ramienia SO-101" — NIE "ramię sterowane mózgiem muchy" ani "cyfrowa mucha".
- Słowo "FlyWire" w materiałach trzeba zastąpić "MaleCNS (Janelia)" albo usunąć.

### Gaps
- Nie ma w repo jednego pliku "README/pitch"; opis systemu rozproszony po `RESULTS.md`, `bio2/RESULTS.md`, `flymind/*`.

---

## 2. Wyniki z liczbami — podział według poziomu dowodu

### Takeaway
**Zweryfikowane na prawdziwym sprzęcie: nic (0).** Zweryfikowane w symulacji (z kontrolami): pościg wzrokowy LC10a→DNa02 (38/40, ale regulator klasyczny 40/40 i dokładniejszy), odruch chwytu (v4: 26/30 = 87 %, 0 zgnieceń), FJ1 szczęka (12/12, ale bez przewagi nad trywialnym odruchem). Rzeczy najbardziej "ambitne" (FlyArm, sygnał uniesienia z dotyku innej nogi) to **piloty eksploracyjne** bez testu potwierdzającego.

### Cited Findings

#### A. Zweryfikowane na prawdziwym sprzęcie
- **Brak.** Wszystkie raporty mówią to wprost (cytaty w nagłówku). W kodzie `grep` po `lerobot|scservo|feetech|serial` nie znalazł sterownika sprzętowego (sprawdzone `grep` po plikach .py poza `.venv`: jedyne trafienie to `bio2/audit_and_validate.py`, a tam nazwa Feetech występuje tylko w tekstach `print` opisujących serwo — brak sterownika sprzętowego). Czujniki dotyku w szczękach istnieją tylko w modelu — memory `flymind-f1-active-sensing-2026-11-02-closed.md` ("Touch sensors exist only in sim"). Kamera "eye" jest kamerą symulowaną (render MuJoCo) — `flymind/experiments/f1_active_sensing/RAPORT_F1_PL.md` §2.
- Parametry fizyki (tarcie, sztywność serw, szum kamery) to wartości przyjęte, nie zmierzone na sprzęcie — `bio2/RESULTS.md` (Ograniczenia); `RESULTS.md` (Uproszczenia fizyki).

#### B. Zweryfikowane w symulacji (z kontrolami)
1. **Pościg wzrokowy (obrót podstawy) — potwierdzenie V5, ziarna 2011–2050, n = 40, zamrożony protokół:** sieć z danych 38/40 (95 % CI 0,84–0,99); tasowana sieć 3/40; zamieniona strona 0/40; brak wzroku 0/40; **klasyczny regulator P 40/40 i dokładniejszy (mediana błędu 0,16° vs 1,41°)** — `flymind/VALIDATION_PLAN.md` (sekcja V5); memory `flymind-closed-loop-2026-10-28.md`. Co to znaczy uczciwie: sieć z danych potrafi nakierować kamerę, ale zasługa to w dużej mierze **lateralizacja** (która strona pobudza którą), nie szczegółowa topologia: kontrola z zachowaniem siły ("strength-preserving shuffle") dała 10/10 w wersji wstępnej — memory (Red Team V4/V5); `VALIDATION_PLAN.md` ("Nie wynika: że SNN steruje lepiej").
2. **Szersze zadanie (V5 v2, ziarna 2051–2100, n = 50):** sieć z danych 28/50, tasowanie z zachowaniem siły 20/50 (topologia +16 pp, p = 0,008, na krawędzi czułości), tasowanie DN 9/50, prosty przekaźnik "toy" 22/50, **regulator P 50/50** — memory `flymind-closed-loop-2026-10-28.md`; `VALIDATION_PLAN.md` (tabela poziomów V5).
3. **V5 v4 (ziarna 4001–4450, 2700 prób, 0 błędów, red team 3 rundy, PASS_WITH_LIMITATIONS):** różnica błędu DATA vs losowy wzorzec **zmienia znak zależnie od odległości celu**: bliskie cele +0,51° (losowy lepszy), dalsze −0,52° (dane lepsze), wielkość ≈ granicy istotności praktycznej (0,5°); średnio błąd DATA 2,88° vs regulator P 0,20°, P lepszy w 450/450 par — `flymind/V5v4_FINAL_REPORT.md` §7–8. Cytat do zapamiętania: "wzorzec z danych nie jest jednoznacznie lepszy; nie jest to twierdzenie o mózgu muchy" (§8).
4. **Program V5 v4.1 → V6m3 (wszystkie eksploracyjne, bez puli potwierdzającej):** wzorzec połączeń LC10a×LC10a z danych desynchronizuje populację LC10a i podnosi odpowiedź DNa02 blisko progu (−18,0 Hz vs 50 tasowań), ale w pętli zamkniętej "no robust behavioural advantage of the data-derived wiring was found"; pierwsza interpretacja mechanizmu została **obalona** przez red team — `flymind/program_v5v41/FINAL_REPORT.md` §A.
5. **Odruch chwytu piłeczki (RESULTS.md v4, MuJoCo):** test (ziarna 0–9) 8/10, × 3 ziarna szumu 26/30 = 87 %, **0 zgnieceń**; walidacja 120–139 × 3: 53/60 = 88 %; strojenie 100–119 × 3: 57/60 = 95 %. Czas od kontaktu do pewnego chwytu 981 ± 268 ms; latencja neuronalna 43 ± 6 ms — `RESULTS.md` (Etap 3). Stałe były strojone na zbiorze 100–119, walidowane na 120–139, test 0–9 uruchomiony raz. **Zastrzeżenie:** część logiki to nasza klasyczna reguła (zatrzymanie bazy przy dotyku `CONTACT_STOP` — "reguła warstwy serwa, nie neuron"; wersja w sieci pogorszyła wynik), 20 neuronów odruchu to nasz model, a rozmiar kulki jest "znany" sterownikowi — `RESULTS.md` (v2, v4, "Co jest z konektomu, a co nasze").
6. **Ablacja neuronów (Etap 4, RESULTS.md):** przy 300 z 352 neuronów z kompensacją 90 ± 0 % (jak pełny); poniżej ~150 neuronów sieć przestaje działać (150: 40 %, ≤ 60: ~3 %). Nokauty: bez RR_resist 0 % i 7/10 zgniecionych, bez RR_assist 0 % — czyli kluczowe są **nasze modelowe neurony odruchu**, nie dane — `RESULTS.md` (Etap 4). Test n = 10.
7. **bio2 (Etapy 1–5):** ucieczka przed zbliżającym się obiektem (DNp01) 10/10, ale 100 % fałszywych ucieczek przy własnym obrocie; pamięć obiektu przy zasłonięciu 4/10 (test), 9/20 (walidacja) vs bez pamięci 0/10; chwyt B2 8/10, ale kontrola z zablokowaną bazą 5/10, przedziały się zachodzą — `bio2/RESULTS.md` (Streszczenie, Ograniczenia). Testy autentyczności: wzgórze EPG 100 % → 0 % po rozbiciu struktury (REWIRE/SHUFFLE), ucieczka 0/10 po przepięciu wszystkich krawędzi; "63/64 trafionych przewidywań", ale autorzy sami piszą że wynika to w dużej mierze z szerokich przedziałów — `bio2/RESULTS.md` §5.1.
8. **Łapanie rzuconej piłeczki:** wersja inżynierska (ENG) 94–98 %, wersja "biologiczna" w pełni wcielona (BIO-embodied, aerodynamika + wiatr) **7/20 = 35 %** (CI 18–57 %), 0 zgnieceń; kontrole przyczynowe (lezje, tasowanie, próżnia) 0/20 — `bio2/RESULTS.md` (Streszczenie, wiersz 5.5 i Etap 5.2). "Łapanie zawdzięczamy inżynierii (ENG 94–98 %), a mózg wnosi tylko z modelowymi łatkami i nie poprawia wyniku." Zakres: wąski pas rzutów (24,6 % losowań akceptowane).
9. **FJ1 — szczęka sterowana obwodem dotyku lewej środkowej nogi (commit ccc19d7, 288 prób, red team: VALID WITH ISSUES, niezależny przelicznik MATCH):** obwód z danych **12/12** chwyta i unosi piłeczkę przy obu założeniach o znaku glutaminianu (H1 potwierdzona); **ale** trywialny odruch (jedna linijka) też 12/12, więc brak przewagi nad prostym odruchem; kontrola zerowa 0/12; przy Glu −1 10 przetasowanych obwodów dało: 0, 10, 0, 12, 12, 0, 0, 0, 12, 0 (średnia 4,6) → H2 (znaczenie konkretnych połączeń) **nierozstrzygnięta**; przy Glu +1 wszystkie 10 przetasowanych też 12/12 → H2 **odrzucona** — `flymind/experiments/fj1_fly_jaw/RESULTS.md`. Test jest progowy (wystarcza moment > ~0,14 N·m), mapowanie wyjścia wybrano po pilocie, reszta ramienia to klasyczne rusztowanie.

#### C. Piloty eksploracyjne / hipotezy (bez testu potwierdzającego)
- **FJ2 (FlyArm), 2026-11-03, szum 0, bez ziaren potwierdzających:** przy mapowaniu ustalonym z góry i Glu −1 sieć wzrok→nogi zbliża chwytak do piłeczki: 0,30 m — 71 → 17 mm, obie szczęki w kontakcie; 0,34 m — 94 → 80 mm; 0,38 m — 126 → 121 mm. Przy Glu +1 wyniki niespójne (ramię czasem się oddala, czasem uderza w piłeczkę 190–217 mm). Kamera widzi piłeczkę tylko w odległości 0,30–0,40 m. Chwytak wciska się w stół (29–44 N), `safety.py` nie pilnuje stołu — `flymind/experiments/fj2_fly_arm/PILOT_NOTES.md` (Pilot 1–2); memory `flymind-d1-audit-2026-11-03.md`.
- **Brak naturalnego sygnału "unieś" w obwodzie jednej nogi ani w pętli dotyk→neurony wstępujące→mózg→zstępujące:** przy Glu −1 pętla wzmacnia *podpór* (42,5 → 63,5 Hz), wymach bez zmian — `PILOT_NOTES.md` (Szukanie sygnału uniesienia).
- **Kandydat na sygnał uniesienia (najnowszy commit bf05cb1):** dotyk lewej środkowej nogi (T2 L) uruchamia wymach przeciwnej środkowej nogi (T2 R > podpór) przy obu znakach Glu (Glu −1: 27,1/4,2 Hz; Glu +1: 92,9/14,8 Hz), kontrola z odciętymi wyjściami daje 0 — `PILOT_NOTES.md` (Dotyk jednej nogi → inne nogi). **Ostrzeżenie:** kontrola z przetasowanymi połączeniami NIE została jeszcze policzona na poważnie; w pliku smoke `flymind/experiments/fj2_fly_arm/results/shuffle_six_legs_smoke.jsonl` jedno przetasowanie (ziarno 9218001, Glu −1) też daje T2R wymach 13,56 > podpór 5,17 — to test dymny, "nieanalizowany" wg `SEED_REGISTRY.md`, ale sugeruje, że wynik może nie być swoisty dla połączeń z danych. Autorzy zapisali: "[HIPOTEZA] ... W literaturze tego nie sprawdzono" (PILOT_NOTES.md). Nie wolno tego przedstawiać jako wyniku.
- Audyt danych D1–D3 (2026-11-03, wynik "REVISE"): znak sygnału dotyku zależy od założenia o glutaminianie (literatura wspiera tylko Glu −1 przez ekspresję receptorów GluCl, bez fizjologii); nie ma w danych obwodu nacisku/poślizgu (kampaniformowe sensilla: 2L+2R na nerw nogi); T1 (przednia noga) najsłabiej opisana; "No paper supports any leg reflex sign" — memory `flymind-d1-audit-2026-11-03.md`.

#### D. Odrzucone / nie powiodło się / wycofane
- "LC10a→AOTU wyjaśnia 43 % deficytu" — **wycofane** (kontrola dopasowana siłą pogorszyła wynik bardziej) — `flymind/NEXT_SESSION.md` pkt 7; memory `flymind-closed-loop-2026-10-28.md`.
- V5 v3 (ziarna 3051–3100): hipoteza przewagi SWS (tasowania zachowującego stopnie) **niepotwierdzona** (równoważne w ±1°) — memory (V5 v3).
- Pierwsza interpretacja mechanizmu w V6m — **obalona** przez red team — `program_v5v41/FINAL_REPORT.md` §A.
- Aktywne wyczuwanie (F1): ruch kamery podnosi wykrywanie słabych celów o Δ +0,10 (n = 200), **ale nieswoiście** — tyle samo zyskują sieci przetasowane i próg bez SNN; linia **zamknięta przez użytkownika 2026-11-02** — `flymind/experiments/f1_active_sensing/RAPORT_F1_PL.md` §1; memory `flymind-f1-active-sensing-2026-11-02-closed.md`.
- V3.4: dane nie dają czystego odruchu dotyk→zamknięcie szczęki (wtedy chwyt nie był sterowany przez SNN); później poprawione: obwód dotyku nogi istnieje w danych, ale znak to wycofanie, nie chwyt — memory `flymind-closed-loop-2026-10-28.md`, `flymind-f1-active-sensing-2026-11-02-closed.md`.
- Odrzucone warianty w RESULTS.md v4 (np. RR_stop w sieci: 44/60 i 12 zgnieceń vs 53/60 dla obecnej wersji) — `RESULTS.md` (Sprawdzone i odrzucone w v4).
- Opóźnienie klatek: SNN jest wyraźnie bardziej wrażliwa niż regulator P (50 ms: 9/20 vs 20/20; 100 ms: 7/20 vs 20/20, eksploracja) — `VALIDATION_PLAN.md` (V5, opóźnienie). Martwa strefa: dla ρ 0,30 m SNN 0/10 vs P 10/10 — memory (Red Team V4/V5).
- Mapowanie V5 z dużych odległości (ρ ≥ 0,28 m): nietestowane / pętla zawodzi — `V5v4_FINAL_REPORT.md` §8; `FINAL_REPORT.md` (V7).

### Inferences
- Realny, obroniony wynik: **"sieć zbudowana z połączeń konektomu, w zamkniętej pętli z kamerą, nakierowuje symulowane ramię na piłeczkę (38/40) — i przestaje działać, gdy połączenia przetasować (3/40) lub odwrócić (0/40)"**. Ale tej samej rzeczy dokonuje prosty regulator P lepiej, a po wyrównaniu siły sygnału przewaga "prawdziwej topologii muchy" jest mała i zależna od warunków (±0,5°).
- Najmocniejsza "uczciwa" opowieść dla jury to nie "lepsze niż klasyczny algorytm", tylko **"ścisła metodologia falsyfikacji"**: wiele hipotez obalonych lub wycofanych, protokoły zamrażane przed przebiegiem, rejestr ziaren, red-teamy, niezależne reanalizy.

### Gaps
- Brak jakiegokolwiek testu na prawdziwym ramieniu, kamerze czy czujnikach.
- Brak testu potwierdzającego FJ2 (ramię) i kandydata na sygnał uniesienia (brak zarejestrowanej analizowanej kontroli tasowania).
- Nie znalazłem w repo jednego miejsca z "podsumowaniem postępu"; w pamięci jest autorska ocena postępu (D1 audit): inżynieria ~28 %, biologia ~15 %, walidacja ~30 %, gotowość do symulacji ~10 %, sprzęt ~3 % — to ocena autora, nie pomiar.

---

## 3. Jakie kontrole przeprowadzono i co z nich wynikło

### Takeaway
Projekt ma nietypowo dobrą higienę badawczą (zamrożone protokoły z sha256, rejestry ziaren, red-teamy, niezależne reanalizy, kontrole przetasowane/zerowe/trywialne). Kontrole często **obaliły** mocniejsze twierdzenia. To siła, ale tylko jeśli opowie się to uczciwie.

### Cited Findings
- Kontrole: tasowanie krawędzi z zachowaniem stopni (SWS), tasowanie z zachowaniem siły (SHUF_STR), zamiana stron (swap), brak wzroku, prosty przekaźnik ("toy"), regulator P, cięcie LC10a→AOTU, tasowanie bloków, kontrola zerowa (N), trywialny odruch (D), odcięcie wyjść (cut-control) — `flymind/V5v4_FINAL_REPORT.md` §7; `flymind/experiments/fj1_fly_jaw/RESULTS.md`; `PILOT_NOTES.md`.
- Procedury: protokół zamrożony z sha256 przed przebiegiem; manifest haszy kodu; kopia zamrożonego kodu `flymind/validation/…_frozen_code/`; rejestry ziaren (`flymind/program_v5v41/SEED_REGISTRY.md`, `flymind/experiments/fj2_fly_arm/SEED_REGISTRY.md`); kontrola integralności 28/28 — `V5v4_FINAL_REPORT.md` §2–5; `flymind/REPRODUCE.md`.
- Red team = "osobna instancja modelu — ograniczona niezależność, nie recenzja ludzka"; niezależnego red teamu WYNIKÓW V5 v4 nie przeprowadzono, tylko drugą implementację analizy — `V5v4_FINAL_REPORT.md` §4.
- Samokrytyka zapisana w raportach: "(the report) corrected after an independent cross-check of every number — 19 discrepancies and the listed over-claims fixed" — `program_v5v41/FINAL_REPORT.md` (nagłówek).
- W `bio2` poprawka odczytu DN powstała **po obejrzeniu wyników testowych**; wyniki po poprawce "nie są niezależnym sprawdzianem" — `bio2/RESULTS.md` (Ograniczenia).
- Stare pule ziaren są "zużyte" (nie wolno ich użyć ponownie do potwierdzenia): m.in. 2001–2100, 3001–3100, 4001–4450 — `NEXT_SESSION.md`; memory.

### Inferences
- Kontrolę "swoistości połączeń" projekt przeszedł tylko częściowo: sieć z danych vs tasowanie wykazuje różnicę, ale po skorygowaniu o skalę sygnału zostaje mały efekt zależny od reżimu; w FJ1 swoistość nie została wykazana.

### Gaps
- Nie sprawdzałem samodzielnie surowych danych w `results/` (tylko raporty).

---

## 4. Zasada projektu ("mucha ma sterować")

### Takeaway
Zasada nr 1 (Adam, 2026-11-03): sieć z konektomu ma decydować o zachowaniu, kod klasyczny wolno trzymać tylko jako niezależną warstwę bezpieczeństwa, punkt odniesienia/wyrocznię lub wyraźnie opisane rusztowanie do zastąpienia — nawet kosztem jakości, a luki trzeba uczciwie raportować. Obecny stan tej zasady jest **częściowo** spełniony.

### Cited Findings
- Cytat użytkownika: "najważniejsze jest to, żeby nie algorytm tym sterował, tylko mucha, nawet jeżeli stracimy na tym jakościowo" — memory `fly-must-control.md`.
- Użytkownik odrzucił "wirtualną optogenetykę" (sztuczne pobudzanie neuronów); dopuszczalne wejścia to tylko naturalne zmysły (kamera, dotyk, propriocepcja) — memory `fly-must-control.md`.
- Co faktycznie steruje fly-siecią: obrót podstawy (DNa02, `flymind/loop.py`), w FlyArm stawy 1–2 i szczęka (źródło "snn:vision_leg") — `fly_arm.py`.
- Co NADAL klasyczne: w demo V5 "Stawy 1–4 trzyma skrypt, chwytak nie jest sterowany" — `flymind/demo/demo.py` (docstring); w FJ1 "sięganie jest klasyczne" (IK `reach.py`, dosuw boczny, FSM `grip.py`) — `fj1_fly_jaw/RESULTS.md`, memory; warstwa bezpieczeństwa `flymind/safety.py` (zakresy, prędkość; stół jeszcze nie pilnowany); enkoder obrazu (detektor koloru) i dekodery (L−P → komenda) to inżynieria — `REPRODUCE.md`.
- W starszym `RESULTS.md`: zatrzymanie bazy przy dotyku to reguła klasyczna, nie neuron.

### Inferences
- Poprawne sformułowanie: "w zadaniu nakierowania kamery sieć z konektomu podejmuje decyzję; reszta toru ruchu jest dziś klasyczna lub analogowa; zastępujemy ją krok po kroku (FlyArm jest pierwszym krokiem)".

### Gaps
- Brak testu, że FlyArm (stawy 1–2) działa lepiej niż losowo, na zarejestrowanych ziarnach.

---

## 5. Demo i co można pokazać 1 grudnia

### Takeaway
Istnieje działające demo **w symulacji** (`flymind/demo/`): interaktywne okno MuJoCo na Macu oraz gotowe nagrania. Pokazuje tylko orientowanie podstawy na piłeczkę przez sieć DNa02 (SNN) w porównaniu z klasycznym regulatorem P. Nie pokazuje chwytu, FlyArm ani prawdziwego sprzętu. Nie znalazłem w repo wzmianki o terminie 1 grudnia. Konkurs to E(x)plory (`RESULTS.md` s.3 "Projekt na Explory"; `bio2/MALECNS_DATA_AUDIT.md` §5 "Podział epistemologiczny (Dla Jury Konkursu E(x)plory)" — gotowa tabela poziomów dowodu A: fakty EM, B: predykcje neuroprzekaźników, C: model/sterownik, którą warto wykorzystać; uwaga: wiersz C zawiera zdanie "35% vs 0% w próżni", które jest mylące — w `bio2/RESULTS.md` 0/20 w próżni to kontrola ENG-vacuum, a 35 % to BIO-embodied, więc nie powtarzać tego sformułowania bez sprawdzenia).

### Cited Findings
- `flymind/demo/demo.py`: takt sterowania przepisany 1:1 z `loop.run_trial` na tych samych obiektach; test `test_demo.py` sprawdza identyczność trajektorii. Tryby: "SNN" (komenda obrotu z impulsów DNa02) i "P" (klasyczny, SNN nie liczona). Piłeczkę można przestawiać w oknie interaktywnym. Etykiety DATA / MODEL / ENGINEERING w kodzie. Uruchamianie: `.venv/bin/mjpython flymind/demo/demo.py` (okno), `--present` (prezentacja), `--media` (nagrania) — `flymind/demo/demo.py` (docstring).
- Gotowe pliki: `flymind/demo/demo_snn_vs_p.mp4` (1,5 MB, 30.10), `flymind/demo/media/flymind_presentation.mp4` (13 MB), `flymind_neurons.mp4` (1,2 MB), zrzuty `flymind_01_intro.png … 08_summary.png` (31.10) — `ls -la flymind/demo`.
- Docstring demo: "To nie jest mózg muchy, tylko model wycinka połączeń w symulacji." — `demo.py`.
- Starsze nagrania/podglądy 3D dla `bio2` (łapanie piłeczki) istnieją jako skrypty `bio2/watch.py`, `bio2/watch_embodied.py`, `bio2/render_throw_embodied.py` (nie sprawdzałem, czy działają w tej chwili).
- Demo powstało 30–31.10, **przed** FJ1/FJ2 — nie pokazuje najnowszych prac (szczęka z dotyku, FlyArm).

### Inferences
- Bezpieczne demo na żywo: okno z symulowaną piłeczką, sieć SNN vs regulator P, z podpisem DATA/MODEL/ENGINEERING i uczciwą uwagą "regulator P jest dokładniejszy". Obrazek "neurony/impulsy" z `flymind_neurons.mp4`.
- Demo na prawdziwym ramieniu **nie jest możliwe z obecnego kodu** — nie ma sterownika sprzętowego; trzeba by go dopiero zbudować i zrobić za osobną zgodą (VALIDATION_PLAN: sprzęt "tylko za osobną zgodą").

### Gaps
- Nie oglądałem filmów, nie uruchamiałem demo; nie wiem, czy jest już zrobione nagranie FlyArm. Nie wiem, jaki jest wymagany format 1 grudnia ani jaki sprzęt będzie na miejscu.
- Nie znalazłem notatek o zakupie/dostępności fizycznego SO-101 u autora.

---

## 6. Sprzęt, koszt, szybkość

### Takeaway
Wszystko liczone na jednym komputerze z macOS (arm64, 10 rdzeni); pętla V5 działa szybciej niż czas rzeczywisty (mediana ~4,3 ms na takt 10 ms). Kosztu sprzętu **nie ma w plikach projektu** — nie wolno podawać liczby bez zewnętrznego źródła.

### Cited Findings
- Maszyna: "macOS arm64, 10 rdzeni" — `flymind/VALIDATION_PLAN.md` (V6 — czas). Wynik z jednej maszyny nie przenosi się na inny sprzęt — `flymind/latency.py` (komentarz).
- Pętla V5 (40 prób × 300 taktów): cały takt p50 4,3 ms, p99 6,2 ms, max 16,4 ms, 50 z 12 000 taktów > 10 ms (0,4 %); SNN 424 neurony × 10 kroków ≈ 0,43 ms; render kamery ≈ 3,5–8 ms (zależnie od obciążenia); dekoder 0,06 ms — `VALIDATION_PLAN.md` (V6). Cel p99 < 7 ms i 0 przekroczeń z wcześniejszego pomiaru B1 "NIE spełniony".
- RESULTS.md (stary obwód 352 neurony): cykl 0,15 ms (p99 0,27) na krok sceny; SNN ≈ 4 % budżetu 10 ms; ~37× szybciej niż czas rzeczywisty (sama fizyka) — `RESULTS.md` (Etap 1, 4).
- Skalowanie: gęsta macierz — 0,02 ms (272 neurony), 3,2 ms (3000), 14,4 ms (10 000); wersja rzadka `alif_sparse.py`: noga T2 L 1507 neuronów 1,2 ms vs 3,4 ms gęsto na takt 10 ms — `VALIDATION_PLAN.md` (V6 B2); memory `flymind-d1-audit-2026-11-03.md`. Sieć FlyArm ma 5643 neurony, sześć nóg 10 036.
- Reakcja: latencja neuronalna odruchu 43 ± 6 ms, ale pełny chwyt od kontaktu ~1 s (ogranicza go inercja serwa w modelu, nie sieć) — `RESULTS.md`. Reakcja ω na bodziec w pętli wzrokowej ~40 ms (przy 2 Hz) — `VALIDATION_PLAN.md`.
- Serwa: Feetech STS3215; w modelu chwytak w trybie PWM (3,35 N·m); tryb serwa/PID w `bio2/audit_and_validate.py` (Etap 4 audytu — dokumentacja możliwości, nie pomiar).
- Dane: ~1,1 GB do pobrania z publicznego zasobnika (bez opłat, CC-BY 4.0) — `reports/Konektom muchy dla SO101.md`.

### Inferences
- Argument inwestorski "tani, publiczne dane, standardowy laptop" ma podstawę w plikach (dane darmowe i publiczne, symulacja na laptopie). Koszt samego ramienia SO-101 i kamery NIE jest udokumentowany w projekcie — jeśli ma paść w prezentacji, trzeba go sprawdzić osobno (np. w sklepie producenta).
- Prędkość "w czasie rzeczywistym" to wynik symulacji na jednym komputerze, nie na robocie.

### Gaps
- Brak: koszt sprzętu, zużycie energii, liczba neuronów, którą wytrzyma docelowy komputer, test na innym komputerze (np. mini PC), test z prawdziwą kamerą (opóźnienie USB, szum).

---

## 7. Uczciwa lista ograniczeń oraz zdania "wolno / nie wolno"

### Takeaway
Główne ograniczenie: wszystko jest w symulacji, a tam, gdzie sieć z konektomu steruje, prosty klasyczny regulator robi to lepiej. Wiele elementów "mózgu" to model autorów, nie dane.

### Cited Findings (ograniczenia)
1. Symulacja, nie sprzęt (zob. nagłówek).
2. Model, nie mucha: dynamika neuronów (ALIF), J0, szum, znak glutaminianu, enkoder obrazu, dekoder, 20 neuronów odruchu to MODEL — `flymind/REPRODUCE.md`, `RESULTS.md` ("Co jest z konektomu, a co nasze").
3. Klasyczny regulator P jest lepszy: V5 40/40 vs 38/40; v4 błąd 0,20° vs 2,88°; V2 50/50 vs 28/50; SNN wrażliwa na opóźnienia i ma martwą strefę — źródła w §2B.
4. Swoistość połączeń niewykazana lub zależna od reżimu (V5 v3, V5 v4, FJ1) — `V5v4_FINAL_REPORT.md` §8; `fj1_fly_jaw/RESULTS.md`.
5. Znak glutaminianu (hamujący −1 vs pobudzający +1) nierozstrzygnięty; wyniki zależą od niego — `fj1_fly_jaw/RESULTS.md`; `PILOT_NOTES.md`.
6. Brak obwodu nacisku/poślizgu chwytu w danych (campaniform ≈ 4 na nerw nogi); T1 słabo opisana — memory `flymind-d1-audit-2026-11-03.md`.
7. Próby małe: n = 10–12 w wielu testach, 12 pozycji FJ1 to pseudo-powtórzenia; przedziały ufności szerokie (np. B2 49–94 %) — `bio2/RESULTS.md`; `fj1_fly_jaw/RESULTS.md`.
8. Zakres sceny wąski (cele ρ 0,16–0,28 m, azymut ±30°; kamera widzi piłeczkę z pozy startowej tylko w 0,30–0,40 m w FlyArm; łapanie rzutów: 24,6 % losowań) — `V5v4_FINAL_REPORT.md` §8; `PILOT_NOTES.md`; `bio2/RESULTS.md` §5.2.
9. Gotowość: ok. 5303 starych plików nieskomitowanych; zdalna kopia nie istnieje (tylko lokalny backup, kopię zdalną użytkownik anulował) — memory `flymind-d1-audit-2026-11-03.md`, `flymind-backup-2026-11-02.md`. (Wiele z `?? flymind/…` w git status jest nadal niezaśledzonych.)
10. Red team wykonywały instancje modelu AI, nie ludzie — `V5v4_FINAL_REPORT.md` §4. Analizy i kod w dużej mierze napisane z pomocą AI (Claude); właściciel projektu jest nietechniczny i polega na weryfikacji zewnętrznym chatbotem — memory `user-non-technical-owner.md`.

### Zdania BEZPIECZNE (poparte plikami)
- "Zbudowaliśmy w symulacji model sterownika ramienia SO-101 oparty o prawdziwe połączenia konektomu samca muchy (MaleCNS v1.0)." — `RESULTS.md`
- "W symulacji sieć z danych nakierowała kamerę na piłeczkę w 38/40 prób; przetasowana sieć w 3/40, z odwróconymi stronami 0/40." — `VALIDATION_PLAN.md` (V5)
- "Prosty regulator klasyczny robi to dokładniej — nasz wynik dotyczy zachowania sieci, nie przewagi nad algorytmem." — jw.
- "W symulacji odruch nogi z danych (z naszym modułem odruchu) chwytał piłeczkę w 87 % prób bez zgnieceń (26/30 test, 53/60 walidacja)." — `RESULTS.md`
- "Wiele hipotez sprawdziliśmy kontrolami; kilka mocniejszych twierdzeń obaliliśmy lub wycofaliśmy." — `FINAL_REPORT.md`, `NEXT_SESSION.md`
- "Pierwszy pilot: sieć wzrok→nogi muchy w symulacji przybliża chwytak do piłeczki (71 → 17 mm z 0,30 m) — wstępny, eksploracyjny." — `PILOT_NOTES.md`

### Zdania, których NIE wolno wypowiedzieć
- "Prawdziwe ramię jest sterowane mózgiem muchy" / "działa na sprzęcie" (brak jakiegokolwiek testu).
- "Cyfrowa mucha", "skopiowaliśmy mózg muchy", "to zachowuje się jak mucha" (`FINAL_REPORT.md`: "Nothing here is a statement about Drosophila").
- "Konektom jest lepszy niż klasyczny algorytm" (odwrotnie: P lepszy).
- "Wykazaliśmy, że liczą się konkretne połączenia" (FJ1 H2 nierozstrzygnięta/odrzucona; V5 v4 znak zależny od reżimu).
- "Mucha unosi nogę/ramię po dotyku" lub "znaleźliśmy odruch uniesienia" (hipoteza; brak kontroli tasowania; wynik dymny sugeruje nieswoistość).
- "Używa FlyWire" (używa MaleCNS).
- "Mózg łapie rzuconą piłeczkę" (ENG 94–98 % to inżynieria, BIO-embodied 7/20, mózg nie poprawia wyniku).
- "Ramię ma pełną 6-DOF sterowanie z mózgu" (staw 0 przez DNa02; stawy 1–2 pilotowo przez analogię; 3–4 skrypt; chwytak w FJ1/FJ2 sterowany dotykiem w analogii).
- Jakiekolwiek liczby o koszcie, mocy, czasie reakcji na robocie — nie ma ich w projekcie.

### Inferences
- Sensowna wartość dla jury: (a) metoda — otwarte dane + falsyfikacja + raportowanie negatywów, (b) działające demo symulacyjne, (c) jasno opisany plan dojścia do sprzętu. Wartość inwestorska "dziś" jest przede wszystkim badawcza/edukacyjna; produkt jest daleko (autorska ocena gotowości sprzętowej ~3 %).

### Gaps
- Nie sprawdzałem, czy wszystkie liczby w raportach zgadzają się z surowymi danymi (poza tym, że raporty same deklarują niezależne przeliczenia).
