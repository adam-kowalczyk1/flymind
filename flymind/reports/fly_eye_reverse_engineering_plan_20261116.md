# „Co widzi mucha” — plan inżynierii wstecznej widzenia przez flyvis (16 XI 2026)

Autor: Claude (Opus 5.5), sesja poboczna „oko”. **To jest plan. Niczego nie uruchomiłem, niczego nie zainstalowałem ani nie
kupiłem, nie zrobiłem commita.** Jedyne nowe liczby to odczyt danych MaleCNS (§2, tylko do odczytu, kilka sekund).
Etykiety: VERIFIED · PARTIALLY VERIFIED · REPORTED · INFERRED · HYPOTHESIS · NOT VERIFIED · FAILED · NOT IMPLEMENTED.

Pytanie Adama: *„a da się zobaczyć to, co widzi mucha, to co odbiera z tego obrazu… powinieneś zrobić reverse engineering widzenia muchy”.*

---

## 0. Najkrócej

1. **Tak, da się to pokazać** i mamy już do tego prawie wszystkie części. Dla każdej klatki z kamery robota możemy
   pokazać „film” każdego piętra oka: fotoreceptory → L1/L2 („jaśniej”/„ciemniej”) → T4/T5 (kierunek ruchu, 4 kolory)
   → dalej. Każde piętro to mapa ok. 721 sześciokątnych „pikseli” (kolumn oka).
2. **Uczciwie:** to będzie **przewidywanie modelu**, a nie pomiar z żywej muchy. Model (flyvis, Nature 2024) jest zbudowany
   z mapy połączeń i ma parametry dopasowane przez autorów tak, żeby oko liczyło ruch. Autorzy porównali go z 26
   badaniami na prawdziwych muchach (REPORTED, abstrakt pracy).
3. **Nasze własne próby (bez dopasowania) dziś nie wyszły** (r1, r2, ALIF — DSI ≈ 0). **flyvis wyszedł** na tej samej
   bramce: T4 rozróżniają kierunek (3 z 4 podtypów, mediany DSI 0,40–0,58). Dlatego proponuję flyvis jako „oko”, a MaleCNS od
   T4/T5 w górę. Wyniki flyvis policzyła inna sesja, ja tylko przeczytałem jej pliki: REPORTED.
4. **Gdzie flyvis się kończy:** ma 65 typów neuronów (od fotoreceptorów do T4/T5 i Tm/TmY), ale **nie ma** detektorów
   LC/LPLC ani neuronów zstępujących. To piętro trzeba „dobudować” z połączeń MaleCNS. Właśnie to sprawdza teraz test mostu B1
   (inna sesja, w toku).
5. **Zamiast obecnego detektora kontrastu** (który daje prąd prosto do LC10a — sztuczne pobudzanie) wejście sieci będzie
   liczone tak: obraz → flyvis → aktywność typów, które w danych **naprawdę** łączą się z LPLC2/LC4 → przez **liczby synaps z MaleCNS** → LPLC2/LC4 → DN → noga → ramię.
6. **To jest zarazem odpowiedź na „dopasowanie parametrów”:** rekomenduję **nie trenować** naszych parametrów, tylko użyć
   parametrów dopasowanych przez autorów flyvis i jasno nazwać to **hybrydą** (patrz §5).

---

## 1. Co już jest (stan na 16 XI wieczorem)

| Element | Gdzie | Stan |
|---|---|---|
| Optyka oka: klatka → 296 omatidiów co 5°, jasność „jak Rh1” (prawie ślepa na czerwień), bez neuronów | `experiments/step3_wiring/eye_bench.py`, obraz `results/step3_20261115/fly_view/co_odbiera_mucha_oko.png` | działa; test w toku (inna sesja) — REPORTED |
| flyvis 1.2.0, 50 gotowych modeli, osobne środowisko `envs/flyvis` | `data/flyvis`, instalacja w dzienniku `results/v1_camera/AUDIT_LOG_eye_20261116.md` | VERIFIED przez inną sesję (sumy sha256) — REPORTED dla mnie |
| Bramka kierunku na flyvis: G2-fv i G3-fv PASS (T4a/c/d) | `results/v1_camera/gate_flyvis/GATE_RESULT_flyvis_20261116.md` | REPORTED (przeczytałem, nie powtarzałem). T5 słabe — autor podejrzewa sposób pomiaru (INFERRED) |
| Mapa kolumn flyvis ↔ MaleCNS (obrót 30°); „ramiona” LPLC2 w MaleCNS zgodne z kierunkami T4 we flyvis | `experiments/v1_camera_input/bridge_prep.py`, `PREREG_BRIDGE.md` | REPORTED (VERIFIED wg tamtej sesji) |
| Most B1: flyvis T4/T5 → LPLC2 (MaleCNS) — czy LPLC2 woli zbliżanie od oddalania i przesuwania | `bridge_loom.py`, `results/v1_camera/bridge_b1/` | **w toku** (o 22:02 liczył kontrolę 210°). Autor sam **przewidział porażkę** części z przesuwaniem — czekamy |
| Nasz MaleCNS bez dopasowania: r1, r2, ALIF | `reports/fly_eye_g2_alif_20261116.md` i wyniki r1/r2 | G2 FAILED ×3 — VERIFIED (model) |

## 2. Ile wejścia detektorów pochodzi z typów, które ma flyvis [FM, VERIFIED odczyt, obie strony razem]

| Neuron docelowy | Wszystkie synapsy wejściowe | Z typów obecnych we flyvis | Najsilniejsze wejścia |
|---|---|---|---|
| **LC4** (szybkie zbliżanie) | 314 772 | **54,9 %** | T2, TmY3, Tm4, Tm2, LC4, Tm3 |
| **LPLC2** (zbliżanie) | 363 497 | **53,5 %** | LPLC2 (same ze sobą), Tm5Y, T5d, T5b, T5c, T4c |
| LPLC4 (droga lądowania) | 262 294 | 26,1 % | Li21, Tm4, Tm3, LC20b, TmY3, T2 |
| LC10a (śledzenie celu) | 258 112 | 16,5 % | LC10a, TuTuA_2, AOTU042, Tm5Y, LC9, LC10c-1 |
| DNp07, DNp01 | 12 402 / 43 478 | 0 % (słuchają LC/LPLC) | DNp07 ← LPLC4; DNp01 ← LC4, LPLC2 |

**Co z tego wynika (INFERRED):** LC4 i LPLC2 dostaną z flyvis ponad połowę swojego wejścia. To najlepszy start.
LPLC4 (droga lądowania do nadgarstka) tylko ćwierć, a LC10a jedną szóstą. Dlatego „śledzenie celu przez prawdziwe oko”
zostaje na później. Reszta wejścia to inne detektory i mózg centralny, których flyvis nie modeluje. Każdy wynik musi to podawać.

---

## 3. Plan krok po kroku [PROP — wszystko NOT IMPLEMENTED]

### W0. Okno muchy (tylko obraz, bez sieci)
Klatki z istniejących scen MuJoCo (kamera nadgarstka) → jasność „jak Rh1” (jak w `eye_bench.py`) → siatka flyvis
(721 kolumn, `BoxEye` z pakietu flyvis). **Decyzja pola widzenia:** kamera ma ok. 70°, oko flyvis ok. 150° (INFERRED: ok. 31 kolumn po ok. 5°). Rekomenduję
wariant (b) z planu 12 XI: obraz trafia tylko do kolumn przednich, a reszta dostaje jednolitą szarość, tą samą regułą dla wszystkich.
Czas: flyvis był trenowany z krokiem 20 ms (VERIFIED, `_meta.yaml`), kamera daje ok. 30 klatek/s, więc klatki powtarzamy/interpolujemy (inżynierskie, oznaczone).
**Wynik dla Adama:** obraz „mozaika oka” obok zwykłej klatki.

### W1. Atlas „co widzi każde piętro” (flyvis, bez ramienia)
3–4 krótkie sceny: (1) nic się nie rusza, (2) przedmiot przesuwa się w bok, (3) przedmiot zbliża się do kamery,
(4) ramię samo się rusza (ruch całego obrazu). Dla każdej sceny film z panelami:
kamera | omatidia | R1–R6 | L1 | L2 | Mi1/Tm3 (ON) | Tm1/Tm2 (OFF) | T4a–d i T5a–d (kierunek kolorem).
**Sprawdzenia zapisane przed uruchomieniem** (przykład progów do zatwierdzenia):
- znak: L1/L2 spadają przy rozjaśnieniu, rosną przy ściemnieniu w ≥ 90 % aktywnych kolumn;
- kierunek: w scenie (2) w kolumnach, przez które przechodzi krawędź, wygrywa podtyp T4/T5 zgodny z kierunkiem ruchu w ≥ 8 z 10 modeli;
- kontrola: ta sama scena odwrócona w czasie musi zamienić zwycięski podtyp na przeciwny.
10 najlepszych modeli flyvis (000–009, bez wybierania), deterministyczne, bez ziaren.
**Wynik dla Adama:** krótkie filmy „tak to widzi oko muchy” + tabela PASS/FAILED.

### W2. Piętro detektorów (LC4, LPLC2) — most do MaleCNS
Aktywność typów flyvis w każdej kolumnie → **przez liczby synaps z MaleCNS** (mapa kolumn z `bridge_prep.py`) → LC4 i LPLC2.
To kontynuacja testu B1 innej sesji. **Najpierw czekamy na jego wynik.**
- B1 PASS → rozszerzyć z samych T4/T5 na wszystkie typy flyvis (np. T2, TmY3, Tm4 to główne wejścia LC4) i dodać LC4.
- B1 FAILED (np. LPLC2 reaguje tak samo na przesuwanie) → nie stroić. Raport i decyzja Adama. Możliwa przyczyna: sam odczyt „suma
  synaps” jest zbyt prosty, a LPLC2 w danych w 13 % słucha samego siebie i innych LPLC2 (HYPOTHESIS).
**Wynik dla Adama:** panel „detektor zbliżania” w atlasie z W1.

### W3. Zastąpienie detektora kontrastu w pętli
Dziś: omatidia → |kontrast| > próg → **prąd wprost do LC10a** (sztuczne pobudzanie, decyzja z 12 XI).
Po zmianie: omatidia → flyvis → LC4/LPLC2 (W2) → **DNp01/DNp07 przez synapsy MaleCNS** → istniejąca sieć nogi „pre” → ramię w MuJoCo.
Granica modeli jest jedna i jawna: wyjście flyvis zamieniamy na prąd synaptyczny neuronów MaleCNS **tylko** według liczb synaps z danych,
jedną regułą dla wszystkich komórek. Żaden neuron nie dostaje „ręcznie” wybranego prądu.
Zachowanie: „coś się zbliża → nadgarstek się unosi / ramię staje” (droga lądowania lub stop — patrz decyzja 1).
**Kontrole (jak w krokach 3–6):** bez obrazu, oko wyłączone, przetasowane połączenia mostu, zamienione strony, permutacja podtypów T4/T5,
porównanie z obecnym detektorem kontrastu i z klasycznym odruchem.

### W4. (później, nie przed 1 XII) Śledzenie celu przez LC10a
Tylko 16,5 % wejścia LC10a pochodzi z flyvis. Wymaga dobudowania wielu innych typów z MaleCNS. Osobny plan.

---

## 4. Ile to kosztuje

- **Zakupy: żadne.** Wszystko w symulacji, flyvis i modele już są na dysku (REPORTED).
- **Czas liczenia:** w teście B1 jeden model flyvis liczył 84 filmy po ok. 2 s (ok. 170 s obrazu) w ok. 3,5–4 min, czyli mniej więcej w czasie
  rzeczywistym na procesorze (INFERRED z godzin w logu `bridge_b1/run_rot30.log`). W1 dla 4 scen × 10 modeli to godziny, nie dni.
  Najwyżej 3 procesy naraz (druga sesja liczy).
- **Moja praca (INFERRED):** W0–W1 to 1–2 dni, W2 zależy od B1, W3 to ok. tydzień. Do 1 XII realne są W0–W2 i ewentualnie
  prosta wersja W3.

## 5. Dopasowanie parametrów — trzy drogi

| Droga | Co to znaczy | Plusy | Minusy | Rekomendacja |
|---|---|---|---|---|
| **A. flyvis jak jest** | oko = gotowe parametry autorów (734 dopasowane liczby), konektom samicy z innej mapy | działa dziś (bramka PASS), opublikowane, otwarte | to nie nasz MaleCNS; hybryda dwóch map | **TAK** |
| B. dopasować nasz MaleCNS jak autorzy | trenować stałe czasowe i siły typów na zadaniu „licz ruch” | całe oko z jednej mapy | tygodnie pracy, karta graficzna, ryzyko; nie przed 1 XII | później, osobna decyzja |
| C. zatrzymać oko | zostaje detektor kontrastu, uczciwie opisany | zero pracy | brak „prawdziwego” widzenia | nie |

Na plakat/demo uczciwe zdanie brzmi (PROP): *„Oko: model z mapy połączeń płata wzrokowego (flyvis, Lappalainen i in. 2024) połączony
z mapą połączeń MaleCNS od czujników ruchu w górę. Sama mapa połączeń bez dynamiki neuronów nie liczy kierunku ruchu — sprawdziliśmy to trzy razy.”*

## 6. Decyzje dla Adama

1. **Droga A (flyvis jako oko, hybryda)?** Rekomenduję: **tak**.
2. **Zgoda na W0 + W1 (atlas „co widzi każde piętro”, same symulacje, 10 modeli)?** Rekomenduję: **tak**, to bezpośrednio odpowiada na Twoje pytanie.
3. **Pole widzenia: tylko przednie kolumny (wariant b)?** Rekomenduję: **tak**.
4. **Pierwsze zachowanie w W3: „zbliżanie → stop” (LC4/LPLC2 → DNp01) czy „zbliżanie → lądowanie/nadgarstek” (LPLC4 → DNp07)?**
   Rekomenduję **LC4/LPLC2** na start, bo mają ponad połowę wejścia z flyvis (LPLC4 tylko 26 %). DNp07 dołączyć, gdy LPLC4 zostanie dobudowany.
5. **W2 i W3 dopiero po wyniku B1** (inna sesja). Zgoda na takie uzależnienie? Rekomenduję: **tak**.

**Do czasu odpowiedzi:** niczego nie uruchamiam. Czekam na wynik B1 innej sesji. Po zgodzie zapiszę cel W1 (progi, modele, hasze) przed pierwszym uruchomieniem.
