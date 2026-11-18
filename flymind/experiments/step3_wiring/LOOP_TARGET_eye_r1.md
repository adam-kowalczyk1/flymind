# Test „widzenie jak oko złożone muchy” (cel zapisany PRZED testem, 16 XI 2026; prośba Adama „Zrób testy z takim widzeniem — muchy”)

## Co się zmienia
Wejście wzrokowe sieci (i regulatora P w ramieniu A) przechodzi przez **model optyki oka złożonego** (`eye_bench.py`):
1. Klatka 96×128 jest przeliczana na jasność widzianą przez R1–R6. Te komórki mają jeden pigment Rh1 (szczyt ok. 480 nm), więc nie widzą koloru. Wagi R, G, B = 0,05 / 0,55 / 0,40 — przybliżenie, prawie ślepe na czerwień.
2. Obraz jest rozmywany do 5° (kąt akceptacji) i próbkowany co 5° na siatce heksagonalnej: 296 omatidiów na polu kamery.
3. Liczy się kontrast względem mediany omatidiów i ten sam napęd LC10a L/P co dotąd.

**Czego to NIE jest:** to nie są neurony płata wzrokowego. Między omatidiami a LC10a nadal działa prosty detektor kontrastu, czyli sztuczne pobudzanie (decyzja Adama z 12 XI). Droga z danych czeka, bo bramka G2 nie przeszła.

Rusztowanie się nie zmienia: klasyczny pomiar położenia do chwytu (sylwetka „chroma” 480×640), dojazd i chwyt jak w benchmarku kolorów.

## Parametry ustalone PRZED testem (eksploracja na scenach rozwojowych 21 990 xxx — uczciwie)
- **Δφ = 5°, FWHM = 5°** — wartości z literatury.
- **Próg C_MIN = 0,17**, czyli 1,5 × największy kontrast pustej sceny. Ten kontrast zmierzyłem: 0,113 (kratka stołu i cienie).
- **Kalibracja skrętu ciemną plamką** (60,60,60) na szarym tle (120). Dotychczasowa zielona plamka ma dla Rh1 kontrast 0,008, czyli jest niewidoczna.
- **E0 = 0,538.** Plamka kalibracyjna na wprost daje g = 0,916, tak samo jak enkoder koloru dla swojej plamki.

**Eksploracja z wagami Rh1:**
- Czerwony przedmiot ma kontrast 0,40–0,64, a żółty 0,12.
- W próbach dymnych (3 przedmioty) czerwony: A 3/3, E 3/3; zielony, niebieski i żółty w E: 0/3; żółty w A: 0/3.
- Pierwsza wersja (średnia RGB, próg 0,20, zła maska chwytaka) nie widziała niczego; poprawiłem ją przed zapisaniem tego celu.

## Test (raz)
- **Sceny:** `--seed 21993`, czyli sceny 21 993 000–440 (45 przedmiotów × 1 poza). Szum drogi wzrokowej: 39 993 000–440.
- **Przebiegi:** E_vis_touch i A_cam × percepcja „eye” × {zielony, czerwony, niebieski, żółty} oraz E_vis_touch i A_cam × „chroma” × czerwony jako para odniesienia. Razem 10 przebiegów po 45 przedmiotów, xargs -P 5 → `results/step3_20261115/eye/`.

## Kryteria (`analyze_eye.py`, osobno dla E i A)
- **H1 (czerwony, kolor widoczny dla Rh1):** „eye” nie gorsze od „chroma” w parach 45 scen. Warunek: różnica co najmniej −10 pp i McNemar nie wskazuje istotnego pogorszenia.
- **H2 (przewidywanie modelu):** zielony, niebieski i żółty, które dla Rh1 są jasne jak stół, dają ≤ 5/45 sukcesów każdy.
- **WERDYKT dla sieci:** H1(E) i H2(E). Przy obu: „sieć steruje z widzeniem o rozdzielczości i czułości oka muchy dla przedmiotów, które mucha widzi; przedmiotów izoluminantnych dla Rh1 nie widzi — jak przewiduje model”.

## Oczekiwania
- H1: raczej tak, ale przy 45 parach niepewność jest duża.
- H2: raczej tak, sądząc po kontrastach z eksploracji.
- Możliwe, że pojedyncze ciemne ściany brył (cienie) zostaną zauważone.

## Granice
- Symulacja.
- Wagi Rh1 to przybliżenie z RGB kamery; brak UV, R7 i R8.
- Pole widzenia 70°, a nie ok. 330° prawdziwej muchy.
- Brak ruchu: oko liczy pojedyncze klatki, a prawdziwa mucha opiera się głównie na ruchu.
