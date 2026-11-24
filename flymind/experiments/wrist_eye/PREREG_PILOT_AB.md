# Pilotaż A/B — FlyEye v2 w pętli z siecią i ramieniem (24 XI 2026, zapisane PRZED pierwszym przebiegiem)

Tylko MuJoCo, bez treningu, bez strojenia, bez dotyku, bez sekwencji zadania. Pytania (Adam): czy po pierwszym ruchu ramienia obraz na żywo
zmienił następną komendę sieci, a jeśli tak, o ile zmienił się ruch? Jeśli efekt zanika — gdzie? To PILOTAŻ (opis), nie test hipotezy.

## Układ
Sieć `head.HeadLife(glu, "N", eyes=True)` (jak avoid/three_joints), szum 2 mV, czucie łokcia z rzeczywistego kąta, dotyk = 0. Oko `FlyEye` v2 (te same
ustawienia co krok 0: OUT_FULL2, vshs, G0) → `loom` L/P na 380/371 komórek LPLC2/LC4/LPLC1/LC6/LC16 (`avoid.eye_idx`). Ramię: `ArmGrip.tick` + `SafetyLayer` +
fizyka, stawy 1–3 z sieci przez cały czas; podstawa, obrót i szczęka trzymane klasycznie. Glu −1 i +1 osobno.
Kula jak w kroku 0 (r 2 cm, tylko rysowana, tor w świecie wzdłuż osi kamery w pozie startowej, 25 → 6 cm, 0,3 m/s), DWA zbliżenia po tym samym torze:
start 1,000 s → 6 cm w 1,633 s, postój 0,5 s, powrót 0,633 s, postój ok. 1,5 s, drugie zbliżenie od 4,270 s, razem 7,0 s.
1 s osiadania ramienia bez sieci; 2 s adaptacji oka na nieruchomej klatce; potem start sieci (t = 0). Klatka co 10 ms z aktualnego stanu (przed taktem).

## Warunki (to samo ziarno szumu sieci, ta sama poza)
- **A** obraz na żywo z nadgarstka. **B** nagranie tej samej sceny (te same klatki, ramię nieruchome); ramię się rusza, ale obraz tego nie widzi.
- Kontrole: **B1** = B z szumem obrazu σ = 1 poziom (ile zmienia nieistotne zaburzenie); **C** = na żywo, kula stoi w punkcie startowym (ruch własny).
Ziarna szumu sieci 27 501 001–010 (oba Glu), szumu obrazu B1 27 502 001–010. Próba dymna: 27 509 001.

## Miary
- Sprawdzian: A i B identyczne co do bitu do pierwszego ruchu. Szum jest wspólny, więc każda późniejsza różnica ma przyczynę w obrazie.
- Łańcuch: pierwszy takt różnicy A/B w: klatka → sygnał oka → impulsy komórek oka → mózg → DN → rdzeń → neurony ruchowe T1 L → komenda → kąt.
- Okna: W1 = 1,0–3,0 s (pierwsze zbliżenie), W2 = 4,27–6,27 s (drugie). W każdym: suma komend stawu [rad], zmiana rzeczywistego kąta, całka sygnału
  oka, impulsy grup; różnica A − B bezwzględnie i w % B.
- **„Zmienił komendę”**: komendy A i B różnią się po pierwszym ruchu (dokładnie) w ≥ 9/10 par. **„Zauważalnie zmienił ruch”**: w W2 dla stawu |mediana (A − B)|
  zmiany kąta ≥ 0,005 rad, ten sam znak ≥ 9/10 par i |mediana| > 95. percentyl |B1 − B|. Opisowo to samo dla W1.
- Ramię „ruszyło”: kąt odszedł ≥ 0,005 rad. Obrót kamery względem startu (stopnie). Flagi SafetyLayer, strażnik, kontakty.
Po wyniku STOP do przeglądu.
