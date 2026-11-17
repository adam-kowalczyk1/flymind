# LOOP_TARGET — D „idealne bodźce: zbliżanie czy własny ruch?” (zapisane PRZED testem, 17 XI 2026; Adam: „możesz commitować i zacząć coś już robić”)

## Pytanie
W8 i E2: na obrazie z kamery robota obrót ramienia pobudza LPLC2 ok. 2× mocniej niż zbliżanie. Czyja to wina —
**mostu** (flyvis + połączenia MaleCNS) czy **kamery robota** (wąski kadr 160×120 na nadgarstku, sceny MuJoCo)?
Test D usuwa kamerę: bodźce rysowane wprost na 721 kolumnach oka flyvis.

## Bodźce (wszystkie DT 0,01 s, 1 s bez ruchu przed, ten sam czas ruchu co dysk z B1, kontrast jak dysk)
- **Zbliżanie:** dysk w środku pola (`bridge_loom.movies`, `loom_0`), ciemny (0) i jasny (1) na szarym (0,5).
- **Własny ruch** (to, co widzi oko, gdy obraca się samo): losowa czarno-biała tekstura na **całym** polu (plamy ok. 2 kolumny, `d_ideal.texture`),
  przesuwana sztywno o 16 kolumn w 4 kierunkach (0°, 90°, 180°, 270° — obrót oka w poziomie/pionie) oraz obracana wokół środka o ±2 rad
  (obrót wokół osi patrzenia). 3 tekstury (ziarna 23 506 001–003). Razem 18 bodźców „własnego ruchu”.
- Modele flyvis 000–049; przypisanie kierunków T4/T5 z pomiaru w każdym modelu (`w7_run.align`), odczyt AND (`w5_and.readout`, układ prawdziwy),
  opisowo także z hamowaniem LPi (`e2_lpi.readout_lpi`) i regułą LIN. Mapa `results/v1_camera/bridge_b1/map_rot30.npz`.
- Komórki: LPLC2 ze środkiem pola recepcyjnego ≤ 4 kolumny od środka (reguła `w5_analysis.discs`), średnia szczytów.

## Kryterium
Model OK (dla danej jasności dysku), gdy szczyt AND przy zbliżaniu > szczyt AND przy **każdym** z 18 bodźców własnego ruchu.
- **D PASS:** ≥ 80 % modeli OK (≥ 40/50) dla dysku ciemnego **lub** jasnego.
- PASS → most potrafi odróżnić zbliżanie od własnego ruchu; porażka W8 bierze się z kamery/sceny → dalsza praca nad geometrią kamery.
- FAILED → sam most tego nie potrafi; rekomenduję zamrozić linię oka do czasu po Explory (1 XII).
- Opisowo: wariant z LPi, LIN, mediana stosunku zbliżanie / najsilniejszy własny ruch, który rodzaj ruchu jest najgroźniejszy.

## Zasady
Jeden przebieg; najwyżej 3 procesy; ziarna tylko 23 506 001–003. Po wyniku nic nie zmieniam (bodźców, komórek, reguł, progów).
Wyniki: `flymind/results/fly_eye_20261117/d/` (`d_*.npz`, `d_result.json`, sumy przed/po).

Próba dymna przed testem: model 000 do katalogu tymczasowego (sprawdzenie, że kod działa; wyników nie oglądałem). Sprawdzenie bodźców `test_d.py` OK.
