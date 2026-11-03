# Pilot: szczęka sterowana obwodem nogi muchy (2026-11-03)

Eksploracja, NIE test potwierdzający: bez protokołu, bez ziaren (szum 0), parametry dobierane w trakcie
(gain 10 → 40 mV/N, prędkość dosuwu). Wyników nie wolno traktować jako dowodu; potwierdzenie wymaga protokołu D3.

1. `touch_pilot.py`: prąd do receptorów szczecinkowych T2 L → częstości puli MN [MODEL].
   - Glu = −1: aktywny tylko prostownik goleni (do 135 Hz) i Fe reductor; zginacze 0 Hz.
   - Glu = +1: aktywne wszystko, prostownik najsilniej (do 250 Hz).
2. `dnp09_pilot.py`: pobudzenie DNp09 (do 114 Hz) w obwodzie T2 L + 119 przekaźnikach.
   - **0 Hz we wszystkich pulach MN** (oba znaki Glu).
   - DNp09 w tym podgrafie nie daje polecenia ruchu nogi.
3. `fly_jaw_sim.py`: schemat ruchu:
   - klasyczne sięganie (rusztowanie) stawia stałą szczękę 4 mm od piłeczki;
   - powolny dosuw boczny (v_max 0,02 rad/s) aż do dotyku;
   - od tej chwili moment szczęki daje wyłącznie `fly_jaw.FlyJaw` (źródło `snn:legT2L`);
   - mapowanie: prostownik → zaciskanie, zginacz → otwieranie (analogia, wybrana po pilocie 1).

   Wyniki (gain 40 mV/N):

   | Piłeczka | Glu = −1 | Glu = +1 |
   |---|---|---|
   | 0,25 / 0,03 | uniesienie 56 mm | uniesienie 55 mm |
   | 0,20 / −0,10 | uniesienie 56 mm | uniesienie 55 mm |
   | 0,22 / 0,10 | **porażka**: kontakt osłabł do 0,1 N, obwód puścił | uniesienie 55 mm |

   Łącznie 5 z 6. Dodatkowo:
   - Przy dosuwie 0,005 rad/s, piłeczka 0,25 / 0,03: Glu = −1 porażka, Glu = +1 sukces.
   - Przy dosuwie z wciskaniem (gap −2 mm) piłeczka toczy się do ruchomej szczęki, która przyciska ją do stołu (0/2).
   - Ramię nie dotknęło stołu w żadnej próbie.

## 4. `lc9_pilot.py`: ścieżka LC9 → DNp09 z danych (2026-11-03)

Skład sieci:
- 104 LC9 L i 115 LC9 R;
- 94 pośredniki (≥ 5 synaps od LC9 i ≥ 5 do DNp09);
- DNp09 L i R.

Wyniki [MODEL]:
- Bodziec na LC9 jednej strony pobudza **tylko DNp09 tej samej strony**:
  - Glu −1: 85–198 Hz;
  - Glu +1: 180–233 Hz;
  - druga strona: 0 Hz.
- Bodziec obustronny przy Glu −1 daje słabsze odpowiedzi niż jednostronny.

Wniosek [HIPOTEZA]: DNp09 L/R to dostępny w danych sygnał „idź w stronę tego, co widzę” (P9 = DNp09 według Bidaye 2020).

Przeszkody w sterowaniu ramieniem przez DNp09:
1. Koder obrazu (`encoder.py`) daje tylko podział lewo/prawo, przypisany do somaSide. Elewacji nie ma, a dodanie jej byłoby wymysłem: brak danych o polu widzenia pojedynczych LC9.
2. Po obróceniu nadgarstka (wrist_roll 0) różnica L/R koduje odległość radialną: g zmienia się z 0,74/0,96 na 0,22/1,0 i na 0/0,02 przy przesunięciu o −4 / 0 / +4 cm. Jednak chwytak skierowany pionowo w dół ma wrist_flex na granicy zakresu, a IK chybia o 18–30 mm.

## 5. `vision_to_leg.py` — wzrok → mięśnie nogi bez sztucznego pobudzania (2026-11-03)
Podgraf z danych, 3663 neurony:
- 219 LC9;
- 94 pośredniki;
- 2 DNp09;
- 1841 przekaźników VNC (do 2 skoków, ≥ 5 synaps na krawędź);
- obwód T2 L (1507 neuronów).

Wejście to wyłącznie prąd 12 mV (amplituda kodera obrazu) do LC9 jednej strony, czyli bodziec wzrokowy. Neuronów motorycznych ani
przedruchowych nie pobudzano sztucznie.

Wyniki [MODEL]:

| | LC9 L → MN lewej nogi | LC9 R → MN lewej nogi |
|---|---|---|
| Glu −1 | ≤ 2,7 Hz | 0 Hz |
| Glu +1 | do 11 Hz (Pleural remotor 10,7; Tr extensor 9,0; Ti flexor 8,0; Sternotrochanter 7,0) | 0 Hz |

Wniosek: istnieje słaby, ale specyficzny co do strony łańcuch od oka do mięśni nogi.
