# P2 — kopia ruchu ramienia dla oka (spisane PRZED testem, 21 XI 2026)

## Pomysł
Mucha (sieć) sama wydaje polecenie ruchu ramienia, więc wie, jak poruszy się kamera. Kopia polecenia (efference copy)
przesuwa stan oka (adaptacja fotoreceptorów + opóźnione sygnały detektorów ruchu) o PRZEWIDZIANY ruch obrazu
(`FlyEye._remap`, `eye.ec = (dx, dy)` px na klatkę). Ruch zgodny z przewidywaniem przestaje być „ruchem”. To nasz analog
inżynierski (u muchy kopia ruchu działa na VS/HS — Kim i in. 2015), nie znany obwód. Kopia zna tylko OBRÓT kamery
(przesunięcie obrazu); zbliżania do powierzchni (przesunięcie kamery do przodu) bez znajomości odległości nie przewidzi.

## Co już wiem (próba na ziarnie 24 105 900, NIE wynik)
Oko v3 bez kopii na scenach syntetycznych: obrót kamery 0,003 × zbliżanie (VS/HS już go gasi), zbliżanie w czasie obrotu 0,81.
Z kopią: obrót 0,027, zbliżanie w obrocie 0,65 — kopia nic nie poprawia, a interpolacja dodaje drobne zakłócenia.
Na prawdziwym nagraniu (oko_r1) najsilniejsze fałszywe sygnały były przy kamerze ZBLIŻAJĄCEJ SIĘ do biurka/ubrania.

## Test (`p2_kopia_ruchu.py --test`, ziarna 24 105 001–010, oko v3 i v2)
Sceny: obrót kamery poziomy/pionowy/skośny 50°/s, zbliżanie w czasie pionowego obrotu 20°/s (jak test 2), plus NOWA
`surface`: kamera jedzie prosto na fakturę (cały obraz się rozszerza, czas do zderzenia 1,5 s od t = 0,5 s, faktura z ziarna).
Kopia: bez; nominalna (g 1, d 0); błędna (g 0,8 i 1,2, opóźnienie 25 ms). Wynik sceny = szczyt / szczyt „loom” tego ziarna.
- **E1:** obroty ≤ 0,25 we wszystkich trzech. **E2:** zbliżanie w obrocie ≥ 0,5.
- **PASS P2 (oko v3):** E1 i E2 w ≥ 9/10 ziaren w każdym warunku z kopią **oraz** kopia poprawia coś względem „bez kopii”
  (mediana obrotów lub zbliżania w obrocie lepsza o ≥ 0,05). Spodziewam się FAILED w części „poprawia” — VS/HS już to robi.
- **Tylko raport:** `surface` (spodziewam się, że oko widzi ją jak zbliżanie — z kopią i bez).
