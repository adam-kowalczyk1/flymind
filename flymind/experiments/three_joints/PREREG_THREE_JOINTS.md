# Trzy stawy z sieci bez sekwencji zadania — plan (24 XI 2026, zapisany PRZED pierwszym przebiegiem)

**Pytanie (Adam):** czy po zmianie bodźca powtarzalnie zmienia się sposób poruszania ramienia? Tylko MuJoCo.
Nie zakładamy, ile stawów ma ruszyć ani w jakiej kolejności.

## Układ
- Sieć: `head.HeadLife(glu, "N", eyes=True)` (jak `avoid.py`), szum 2 mV w każdym neuronie. Wzrok wyłączony (komórki oka bez prądu).
  Czucie łokcia (FeCO) z RZECZYWISTEGO kąta/prędkości łokcia w MuJoCo (jak `avoid.py`).
- Dotyk hw2: palec 1 = A0 szczęka stała → grupa „udo” (230 receptorów T2 L), palec 2 = A1 szczęka ruchoma → grupa „goleń+stopa” (92).
  Mapa „somato” ma status HIPOTEZA. Dłoń = 0. Czujnik: `touch_map.Feel(level="ideal")` — ten sam tor liczb dla obu (bez losowego wzmocnienia).
- Nacisk = 3 N na wejściu czujnika przez 2 s. Siła NIE jest przykładana mechanicznie do palca (pchnięcie samo zginałoby ramię i nie dałoby
  się go odróżnić od komendy sieci). To ograniczenie próby.
- Ramię: `joint_net.ArmGrip.tick` + `SafetyLayer` + `World.step` (fizyka MuJoCo), scena bez przedmiotów. `attempt()` nieużywane.
  Stawy 1–3 z sieci przez cały czas; podstawa (0), obrót (4) i szczęka trzymane klasycznie w pozie startowej `OHCfg.home`.
- Czas: 1 s osiadania bez sieci; potem 0–3 s spokój, 3–5 s nacisk (albo dalej spokój), 5–8 s po nacisku.
- Trójka = ta sama poza startowa i to samo ziarno szumu. Ziarna 27 301 001–010. Glu −1 = główne; Glu +1 = te same ziarna, raport osobno.
- Dodatkowo (poza głównym pytaniem): „palec 1, 92 receptory” — losowe 92 z 230 (losowanie 27 301 900), żeby zobaczyć wpływ liczby receptorów.

## Miary (kąty rzeczywiste, 3 stawy)
Przesunięcie w oknie 3–5 s (główne), przesunięcie 5–8 s i długość drogi 3–5 s (wtórne).
Sprawdzian: przed naciskiem przebiegi w trójce muszą być identyczne co do bitu.

## Kryterium „powtarzalnie zmienia się”
Dla Glu −1: 9 porównań (nacisk 1 − spokój, nacisk 2 − spokój, nacisk 1 − nacisk 2; × 3 stawy) na przesunięciu 3–5 s; dokładny test zmiany
znaku par, Holm 0,05, i |mediana różnicy| ≥ 0,02 rad. TAK dla danego porównania, gdy choć jeden staw spełnia oba warunki.
Wtórnie: rozpoznanie warunku (3 klasy) z ruchu, najbliższy środek, zostaw-jedno-ziarno, permutacje etykiet w obrębie ziarna (5000).
Opis ruchu przed dotykiem: przesunięcie, droga, udział taktów z komendą > 0,01 rad/s, rozrzut między ziarnami.

## Staw stoi? (|przesunięcie| < 0,005 rad w oknie)
Suma komend sieci w oknie < 0,005 rad → „sieć nie wysłała”; inaczej: takty z flagą SafetyLayer (range/rate/lead) lub strażnika stołu
→ „zatrzymało ograniczenie”; inaczej → „komenda przeszła, fizyka nie ruszyła stawu”.
Przed próbą: autotest bez sieci — sztuczna komenda musi ruszyć każdy staw, a zakres i strażnik stołu muszą zostać wykryte.

## Czego nie wolno
Zmieniać kryteriów, ziaren ani parametrów po zobaczeniu wyników; powtarzać ziaren. Ziarno 27 309 001 = próba dymna (rozwój).
