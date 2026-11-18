# Propozycja celu liczbowego dla stawu (b) shoulder_lift — tryb pętli (DO ZATWIERDZENIA przez Adama przed 1. iteracją)

Status: **PROPOZYCJA**. Żadna iteracja nie została uruchomiona.

## Zadanie (to samo co w etapie czucia, `sensory_manipulation.py`, zestaw „base”, 135 prób = przedmioty × 3 pozy)

- Szczęka: obwód T2 L (jak B_fly_search, 90/135 przy klasycznym ramieniu — VERIFIED w audycie).
- **Staw 1 (shoulder_lift) w fazach chwyt → podniesienie → transport: z sieci T1 L + T2 L** (pule wymach/podpór, k i znaki
  z `CALIBRATION_k_SIGNS.md`). Pozostałe stawy i pozostałe fazy: klasyczne rusztowanie (jak dziś).
- Wejścia sieci: dotyk padów → szczecinki T2 L; propriocepcja stawu 1 → receptory T1 L (typ do ustalenia w danych w iteracji 0,
  przed pierwszym przebiegiem z wynikiem). Bez pobudzania MN.
- Strażnik stołu (nowy plik, klasyczny bezpiecznik): komenda stawu 1, która obniżyłaby najniższy punkt padów poniżej 5 mm nad
  blatem (`reach.clearance`), jest zatrzymywana; liczba interwencji raportowana jako „przejęcia bezpiecznika”, nie „decyzje muchy”.

## Ramiona porównania (każda zmiana w iteracji stosowana też do kontroli)

1. **sieć z danych** (Glu −1 i Glu +1 osobno);
2. **5 tasowań** (`visual_path.shuffle(equal_weight=True)`), ziarna tasowań z 20 1xx xxx;
3. **trywialny odruch** dla stawu 1: po zaciśnięciu (oba pady > 0,2 N) unoszenie ze stałą prędkością 0,5 rad/s do wysokości transportu;
4. **klasyczny kontroler** (obecny plan IK) — punkt odniesienia.

## Cel (proponowany)

Na ziarnach **testowych** (użytych raz, na końcu):
- sieć ≥ **72/135** (= 80 % wyniku klasycznego ramienia przy tej samej szczęce, 90/135), **i**
- sieć > **najlepsze z 5 tasowań**, **i**
- sieć > **trywialny odruch** (różnica ≥ 5 prób), **i**
- **maksymalna siła pad–blat ≤ 5 N** w każdej próbie (FJ2: 29–44 N było nie do przyjęcia) oraz przejęcia bezpiecznika ≤ 10 % taktów stawu 1.

Uwaga uczciwości [INFERRED z danych]: przy Glu −1 dotyk pobudza pule podporu (docisk w dół, FJ2), więc spodziewam się, że sieć
z danych NIE uniesie przedmiotu. Wynik „cel nieosiągnięty” jest dopuszczalnym i raportowanym wynikiem.

## Ziarna

- treningowe (strojenie dozwolone tylko tu): `--seed 20101` → ziarna scen 20 101 000–20 101 999; tasowania 20 110 001–005;
- testowe (raz, na końcu): `--seed 20201` → 20 201 000–20 201 999; tasowania 20 210 001–005.
Wpis do SEED_REGISTRY.md przed pierwszym przebiegiem.

## Limity pętli (z polecenia Adama)

maks. 10 iteracji albo 3 godziny; natychmiastowy STOP przy: zmianie wspólnego modułu, zmianie zasady „mucha ma sterować”,
sile na stół > 5 N, braku sensownej hipotezy. Nieudane iteracje zostają w logu jako FAILED.
