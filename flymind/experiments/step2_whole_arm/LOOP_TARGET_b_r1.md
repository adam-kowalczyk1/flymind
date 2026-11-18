# Cel pętli dla stawu (b) shoulder_lift — wersja r1 (DO ZATWIERDZENIA przez Adama przed 1. iteracją)

Zastępuje `LOOP_TARGET_b_PROPOSAL.md` (zostaje bez zmian jako historia). Status: **PROPOZYCJA, nic nie uruchomiono.**
Obowiązują: `CALIBRATION_k_SIGNS.md` (zatwierdzone), tabela C r1 (zatwierdzona), dt 1 ms w pętli (0,1 ms raz na końcu).

---

## 1. Zadanie stawu (b) — dokładnie

Benchmark etapu czucia (`sensory_manipulation.py` + `object_handling.py`, importowane bez zmian; nowy kod tylko w nowym pliku):
zestaw „base” = 45 przedmiotów (9 kształtów × 5 materiałów). Każda próba to świeża scena z jednym przedmiotem, w pozycji
losowanej z ziarna. Percept przedmiotu (prostokąt z góry + wysokość) to wyrocznia z symulatora, jak w B_fly_search.
Wyzwalacz pierwszego dotyku: `trigger="search"`, jak B_fly_search.

**Faza „podniesienie” = zadanie stawu (b).** Zaczyna się, gdy szczęka „zaciśnięta”: moment szczęki ≥ 0,10 N·m przez 10 taktów
(reguła z `sensory_manipulation.FlyCfg`, bez zmian). W tej fazie:

| Staw | Kto steruje | Co robi |
|---|---|---|
| 1 shoulder_lift | **sieć T1 L + T2 L** (`snn:legT1L`) | `cel₁ += −1 · 0,005 · 0,01 · (r_wymach − r_podpór)`, wymach = Sternal anterior rotator, podpór = Pleural remotor/abductor + Sternal posterior rotator (T1 L) |
| 0, 2, 3, 4 | klasyczny skrypt (`script:hold_grasp_pose`) | trzymają cele z ostatniej pozy chwytu (nie ruszają się) |
| 5 szczęka | sieć nogi T2 L — **ten sam samodzielny `LegJaw` co w B_fly_search** (Glu jak wariant) | moment; utrata zacisku (5 taktów < 0,10 N·m) = porażka „snn_released” jak dziś |

- **Wejście sieci stawu 1 (iteracja 1):** tylko dotyk padów → szczecinki T2 L (40 mV/N, max 40 mV, jak szczęka). Do T1 L sygnał
  dochodzi wyłącznie połączeniami z danych (T2 L → T1 L: 15 929 synaps). Bez pobudzania MN. Bez propriocepcji. Dodanie
  propriocepcji T1 L to możliwa hipoteza późniejszej iteracji, stosowana wtedy też do tasowań.
- Sieć stawu 1 liczy się od początku próby, przez wszystkie fazy (te same wejścia dotyku), ale komenda trafia do stawu 1
  **tylko w fazie podniesienia**. Do tej chwili próby wszystkich ramion są identyczne. Sprawdzę to w iteracji 0, patrz pkt 6.
- **Koniec fazy:**
  - sukces ruchu: punkt `cs_fixed` osiąga wysokość transportu z planu (`z_carry`, z_chwytu + 5,5 cm). Wtedy klasyczne
    rusztowanie planuje transport z bieżącej pozy (IK) i dalej wszystko jak w B_fly_search;
  - porażka: limit 3,0 s → „no_lift” (klasyczne IK unosi o 5,5 cm w < 1 s; 3 s daje sieci 3× zapas). Potem zwykłe
    odzyskanie i druga próba, jak w benchmarku.
- **Bezpiecznik stołu (klasyczny, jawnie NIE decyzja muchy):** jeśli cel stawu 1 dałby `reach.clearance` < 5 mm, cel zostaje
  na poprzedniej wartości. Liczba takich taktów jest raportowana jako „przejęcia bezpiecznika”.
- **Pomiar siły na stół (nowy, w nowym pliku):** w każdym takcie suma sił normalnych kontaktów (pady/ramię) ↔ blat
  (`mujoco.mj_contactForce`). Raportowane maksimum na próbę.

**Wynik główny (dotyczy tylko stawu b):** `lift` = ewaluator `object_handling.World` uznał przedmiot za podniesiony (środek masy
≥ 2 cm nad spoczynkiem, kontakt tylko z padami). Dziś `truth["lift"]`, kryterium bez zmian. Liczone na przedmiot (po ≤ 2 próbach),
k/135. **Wyniki pomocnicze (bez celu):** `placed`/135 (cały cykl), czas podniesienia, przejęcia bezpiecznika.

## 2. Ramiona porównania (w każdym wariancie Glu osobno, te same ziarna, ta sama szczęka)

| Ramię | Staw 1 w fazie podniesienia |
|---|---|
| **N** — sieć z danych | jak wyżej (`snn:legT1L`) |
| **S1–S5** — tasowania | ta sama sieć T1 L + T2 L po `visual_path.shuffle(equal_weight=True)`, te same pule, k, znak, wejścia |
| **R** — trywialny odruch (zdefiniowany TERAZ, przed iteracją 1) | `cel₁ −= 0,5 rad/s · 0,01 s` w każdym takcie fazy (stałe unoszenie, 0,5 rad/s = v_ref z kalibracji k), te same warunki końca, ten sam bezpiecznik |
| **K** — klasyczny kontroler | obecne rusztowanie: pionowy odcinek IK (stawy 0–3) do `z_carry` (`P["lift"]`), szczęka ta sama |
| **K0** — w pełni klasyczny (odniesienie) | `object_handling.Controller` (szczęka też klasyczna), te same ziarna |

Szczęka we wszystkich ramionach poza K0 = ten sam `LegJaw` T2 L. Dzięki temu różnice w `lift` wynikają tylko ze stawu 1.
Decyzja projektowa do zatwierdzenia. Alternatywa: szczęka z sieci wspólnej, ale wtedy tasowanie zmienia też szczękę i porównanie
miesza dwa stawy.

## 3. Dlaczego taki próg (odpowiedź na „dlaczego 72, skoro klasyczny 98, a sieć 90”)

Odniesienia z plików (VERIFIED, ziarno 100, 135 prób):

| Seria | grasp | **lift** | placed |
|---|---|---|---|
| K0 klasyczny (`object_handling/B_base_v2.json`) | 125 | **99** | 93 |
| szczęka = sieć T2 L, ramię klasyczne, Glu −1 (`B_fly_search_glu-1_v1`) | 108 | **97** | 90 |
| jw., Glu +1 | 110 | **101** | 90 |
| szczęka = odruch (`D_reflex_search_v1`) | 101 | 88 | 80 |

- **98** to wynik etapu wzroku (A_cam_v3, percept z kamery). To inne zadanie, nie ten benchmark. **90 i 93** to `placed`, czyli
  cały cykl łącznie z transportem i puszczaniem, którymi staw (b) nie steruje. Dla stawu (b) właściwe są liczby **lift**:
  97–101 przy klasycznym podnoszeniu.
- **72 z poprzedniej propozycji wycofuję.** Było liczone od `placed` (80 % z 90) i nie miało uzasadnienia statystycznego.
- Zamiast stałej liczby: **próg względny wobec K na tych samych ziarnach testowych** (cel nie zależy od tego, czy nowe ziarna
  są łatwiejsze). Przy liczbach z ziarna 100 (K ≈ 97) próg niegorszości odpowiada ok. **≥ 84/135 podniesień**.
- Margines niegorszości **10 punktów procentowych** (≈ 13–14 przedmiotów) to wybór projektu. Uzasadnienie:
  - jest nieco większy niż połowa szerokości 95 % przedziału dla proporcji ~0,7 przy n = 135 (±7,7 pp), więc mniejszego
    marginesu nie da się rozstrzygnąć tą liczbą prób;
  - jest mniejszy niż różnica K0 vs odruch szczęki (99 vs 88 = 8 pp lift) + zapas. Klasyczne podnoszenie zna geometrię celu,
    a sieć nie.

## 4. Cel (na ziarnach TESTOWYCH, użytych raz, na końcu) — osobno dla Glu −1 i Glu +1

Cel osiągnięty dla wariantu Glu, gdy spełnione są wszystkie warunki:

1. **Niegorszość wobec K:** dolna granica 95 % przedziału (bootstrap sparowany po przedmiotach, 10 000 losowań) różnicy
   lift(N) − lift(K) ≥ −0,10.
2. **Lepiej niż odruch R:** dokładny test McNemara jednostronny (N > R), p < 0,05, oraz 95 % przedział różnicy lift(N) − lift(R)
   w całości > 0.
3. **Lepiej niż każde tasowanie S1–S5:** McNemar jednostronny N > Sᵢ dla każdego i, z korektą Holma dla 5 porównań
   (rodzina α = 0,05).
4. **Siła na stół:** maksymalna siła normalna ramię↔blat ≤ **5 N** w każdej próbie ramienia N. Przekroczenie w jakiejkolwiek
   próbie (także treningowej) = natychmiastowy STOP pętli. Przejęcia bezpiecznika ≤ 10 % taktów fazy podniesienia
   (raportowane także dla R i S).
5. Wyniki pomocnicze (`placed`, K0) raportowane bez progu.

Moc testu, uczciwie [INFERRED]: przy 135 parach różnice rzędu kilku przedmiotów nie przejdą testu McNemara. Spełnienie warunku 2
wymaga wyraźnej przewagi nad odruchem, a odruch R robi dokładnie to, czego wymaga zadanie (stałe unoszenie). Dlatego **spodziewam
się, że cel 2 będzie trudny**. Przy Glu −1 dotyk pobudza podpór (docisk, FJ2), więc spodziewam się „no_lift” i przejęć
bezpiecznika. Taki wynik raportuję jako wynik, bez strojenia pod niego (pkt 5 polecenia Adama).

## 5. Ziarna i budżet (do wpisania w SEED_REGISTRY.md po zatwierdzeniu)

| Zbiór | Ziarno benchmarku | Próby | Tasowania | Użycie |
|---|---|---|---|---|
| treningowy | `--seed 20101` (sceny 20 101 000–20 101 449), `--poses 1` | 45 (1 poza / przedmiot) | S1–S2: 20 110 001–002 | strojenie dozwolone |
| testowy | `--seed 20201` (sceny 20 201 000–20 201 449), `--poses 3` | 135 | S1–S5: 20 210 001–005 | **raz, na końcu** |
| bootstrap | 20 299 999 | — | — | przedziały ufności |

Uproszczenie treningu (2 tasowania zamiast 5, 45 prób zamiast 135) ma zmieścić iteracje w limicie 3 h: ~2,5 min na serię 45 prób,
do 10 serii na iterację (N, S1, S2 × 2 Glu + R, K), 4 procesy naraz na 10 rdzeniach → ok. 7–10 min na iterację [INFERRED,
do sprawdzenia w iteracji 0]. Zmiana iteracji obejmuje każde ramię, którego dotyczy (sieć → N i S; rusztowanie → wszystkie).
Ramiona bez zmiany kodu nie są przeliczane, a ich hashe są zapisywane.

Test końcowy (raz): 2 Glu × (N + S1–S5) + R + K + K0 = 15 serii × 135 prób ≈ 1,5–2 h.
Plus jednorazowe sprawdzenie najlepszej wersji przy dt 0,1 ms (tylko N, oba Glu; ~1 h na serię).

## 6. Iteracja 0 (nie liczy się do 10; bez strojenia i bez wyników zadania)

1. Pierwsze 3 przedmioty treningowe: trajektorie do początku fazy podniesienia identyczne co do bitu we wszystkich ramionach.
2. Pomiar siły na stół na ramieniu K (sanity check: spodziewane ~0 N w podnoszeniu).
3. Pomiar czasu serii.

Jeśli 1 nie wyjdzie, STOP i pytanie do Adama.

## 7. Zasady pętli (z polecenia Adama, bez zmian)

Każda iteracja: hipoteza → zmiana (nowe pliki) → przebieg na ziarnach treningowych (wszystkie objęte ramiona) → wynik → wpis
w logu z etykietą dowodu. Maks. 10 iteracji albo 3 h. Natychmiastowy STOP przy:
- potrzebie zmiany wspólnego modułu,
- zmianie zasady „mucha ma sterować”,
- sile > 5 N,
- braku sensownej hipotezy.

Nieudane iteracje zostają jako FAILED.
