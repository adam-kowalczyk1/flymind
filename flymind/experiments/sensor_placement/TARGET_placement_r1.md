# Cel testu: gdzie dać DWA czujniki FSR402 na chwytaku SO-101 (r1, 20 XI 2026) — spisany PRZED liczeniem

Pytanie Adama (20 XI): jeden czujnik na „dłoni” (spód serwa) nie poczuje długiego przedmiotu trzymanego czubkami;
nie zgadywać — literatura + symulacja. Metoda za Kim i in. 2026 (arXiv 2611.10647, „Which taxels, not how many”):
miejsca wybiera statystyka kontaktów w symulowanych sytuacjach (top-contact / contact-cover), nie intuicja.

## Czujnik (karta katalogowa Interlink FSR402; z prawdziwymi sztukami NIE porównane — Adam ma zmierzyć)
- pole czynne: koło Ø 12,7 mm (r = 6,35 mm); folia Ø 18,3 mm; grubość 0,45 mm.
- dopuszczam, że folia wystaje poza ścianę (jak w README chwytaka), ale **pole czynne musi leżeć płasko w całości**:
  ≥ 95 % koła Ø 12,7 mm pokryte powierzchnią siatki w płaszczyźnie (±0,3 mm, normalne zgodne cos ≥ 0,95), odsłoniętą
  (żadnej innej części chwytaka 0,5–8 mm nad środkiem, w promieniu 3 mm).
- czujnik podnosi powierzchnię o t: główny wariant t = 0,45 mm (sama folia); wariant 2: t = 1,45 mm (folia + krążek 1 mm).

## Geometria
Prawdziwe siatki producenta (assets/so101_meshes: sts3215_03a_v1, wrist_roll_follower_so101_v1, moving_jaw_so101_v1)
w układzie ciała `gripper`, szczęka ruchoma obracana wokół zawiasu modelu (oś −y). Bez uproszczonych płytek z so101.py.
Punkty powierzchni co ~0,5 mm (losowanie równomierne po trójkątach, ziarno 2011200).

## Sytuacje (zdarzenia) — ziarno 2011201
- **S1 ręka się zbliża:** kula R = 40 mm (pięść) i R = 150 mm (płaska dłoń), kierunki z półkuli przodu i boków
  (nie zza nadgarstka), przesunięcie boczne ±45 mm, szczęka otwarta q ∈ {0,0; 0,6; 1,2} rad. Zdarzenie = pierwszy
  punkt kontaktu. Wykryte, gdy leży w polu czynnym któregoś czujnika (≤ 6,35 mm od środka, ta sama ściana).
- **S2 chwyt pudełka:** ślad na ścianach szczęk: wysokość h ∈ {10, 20, 30} mm, długość L ∈ {10, 20, 30, 50} mm,
  głębokość od czubka d ∈ [0, 45] mm, szerokość W ∈ {10, 20, 30} mm. Szczęka ruchoma zamyka się do przedmiotu.
  Kontakt = najbardziej wystające punkty śladu (±0,3 mm). Czujnik czuje, gdy jego pole czynne (podniesione o t)
  jest wśród najbardziej wystających w śladzie.
- **S3 długi przedmiot czubkami:** pręt w poprzek szczęk (przez całą ich wysokość), średnica D ∈ {8, 15, 25} mm,
  głębokość d ∈ [0, 12] mm od czubka, W = D. Reszta jak S2.

## Miary
- pokrycie S1, S2, S3 = odsetek zdarzeń wykrytych przez ≥ 1 z 2 czujników.
- **wynik pary = średnia (S1, S2, S3), wagi równe** — tym wybieram najlepszą parę (wyczerpująco po kandydatach co ~3 mm).
- „gdzie” (S2+S3): trafność rozpoznania czubek (d < 15 mm) / nasada (d ≥ 15 mm) z samego wzoru, który czujnik czuł
  (najlepsza tablica wzór → klasa), tylko zdarzenia wykryte.
- porównanie: obecny układ hw2p (A0 szczęka stała 30 mm od czubka + „dłoń”), pierwotny (A0 + szczęka ruchoma 22 mm),
  top-contact i contact-cover (Kim 2026).

## Kryteria (zapisane przed liczeniem)
- **P1:** najlepsza para ma pokrycie S3 ≥ 0,8 (długi przedmiot czubkami jest czuty).
- **P2:** najlepsza para ma wynik ≥ wynik hw2p + 0,10.
- **P3:** wynik najlepszej pary przy t = 1,45 mm różni się o ≤ 0,05 (miejsce nie zależy od grubości krążka).
- **P4 (opis, bez progu):** czy jest para, która ma S1 ≥ 0,5 i S3 ≥ 0,8 naraz; „gdzie” podane uczciwie.
- Poślizg (c): geometria go nie liczy — osobny krok w MuJoCo dla 2–3 najlepszych par, zapisany przed uruchomieniem.

Mózg muchy w tym kroku NIE jest używany (to jest pytanie o fizyczne miejsce czujnika). Przypisanie czujników do
receptorów — osobny krok, według miejsca, nie pod wynik.
