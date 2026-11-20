# Plan testu: „oko jak u muchy” (wariant b) — spisany PRZED uruchomieniem, 20 XI 2026

Adam wybrał (b) 20 XI. Oko ma zastąpić klasę `Eye` z `live_avoid.py` (różnica od zapamiętanego tła → wielkość plamy → L = dθ/dt).
To nadal kod, a nie neurony z konektomu: każdy etap naśladuje znany typ komórki oka muchy. Decyzję „uciekać” nadal
podejmuje mózg muchy (wyjście oka pobudza te same komórki zbliżania LPLC2/LC4/LPLC1/LC6/LC16 co dziś, `avoid.eye_idx`).

## Model (wszystkie stałe ustalone tutaj, przed testem; po wyniku nic nie stroję)
| etap | komórki muchy | w kodzie |
|---|---|---|
| ommatidia | ~5° na oko proste | obraz 160×100 uśredniany w bloki 4×4 → siatka 40×25 |
| fotoreceptor + lamina | R1–R6 (odpowiedź ~logarytmiczna, adaptacja), L1/L2 (przejściowe) | x = log(jasność + 8); hp = x − dolnoprzepust(x, τ = 0,25 s) |
| ON / OFF | L1 → Mi1/Tm3 → T4 (ON), L2 → Tm1/Tm2 → T5 (OFF) | on = max(hp, 0), off = max(−hp, 0) |
| detektor ruchu | T4/T5 (model Hassensteina–Reichardta) | dla sąsiadów A, B: LP(A)·B − A·LP(B), opóźnienie LP τ = 0,05 s; osobno ON i OFF, potem suma; poziomo i pionowo |
| 4 kierunki | T4/T5 a–d (4 warstwy płata bocznego) | prawo, lewo, dół, góra = części dodatnie/ujemne sygnałów |
| zbliżanie | LPLC2 (Klapoetke i in. 2017): 4 ramiona na zewnątrz + hamowanie ruchem do środka przez LPi | 32 jednostki (środki x = 6,10,…,34; y = 6,10,14,18 w siatce 40×25, promień 10 pól). Ramię prawe = średnia (prawo − lewo) w prawej połowie pola; lewe, dolne, górne analogicznie; każde ramię ≥ 0; LPLC2 = średnia geometryczna 4 ramion (wszystkie naraz = „i”) |
| strona | lewe/prawe LPLC2 | out_L = max jednostek ze środkiem w lewej połowie kadru, out_R = w prawej (`--flip` zamienia) |
| wejście do mózgu | jak dziś | napęd strony = 40 mV · min(1, out / OUT_FULL) |

OUT_FULL = wyjście modelu w chwili, gdy scena kalibracyjna (zbliżanie na wprost, R/v = 0,1 s, ziarno 24 100 900) osiąga
L = 2 rad/s (θ ≈ 37°) — ta sama definicja „pełnego napędu” co `L_FULL` w `avoid.py`.

## Sceny (syntetyczne, bez sprzętu)
Kadr 160×100 jak w live_avoid; zakładany kąt widzenia w poziomie 100° (prawdziwy niezmierzony); 80 kl./s (zmierzone
19 XI); szum kamery σ = 3 poziomy jasności; tło = rozmyta losowa faktura (średnia 140, odchylenie ~25); 3 s na scenę.
1. **zbliżanie** na wprost: ciemny krążek (40), θ(t) = 2·atan(0,1 / (2,0 − t)) od t = 0,5 s do θ = 80°, potem stoi;
2. **zbliżanie z lewej** (środek na 25 % szerokości) i 3. **z prawej** (75 %);
4. **ręka bokiem**: krążek 30° przesuwa się z lewa na prawo 100°/s;
5. **kamera w bok**: cała faktura przesuwa się poziomo 50°/s; 6. **kamera w górę/dół**: pionowo 50°/s;
7. **obrót kamery** wokół osi obiektywu 90°/s;
8. **oddalanie**: scena 1 odwrócona w czasie;
9. **nieruchoma rzecz**: krążek 40° pojawia się nagle w t = 0,5 s i stoi do końca;
10. **zmiana światła**: w t = 1 s cały obraz jaśnieje ×1,5 (włączenie lampy / automat naświetlania).

10 powtórzeń (ziarna 24 100 001–010: faktura + szum).

## Kryteria (PASS, gdy wszystkie spełnione w ≥ 9 z 10 powtórzeń)
- **K1 wybiórczość:** dla każdej sceny 4–10 szczyt max(out_L, out_R) ≤ 0,25 × szczyt sceny 1.
- **K2 strona:** w scenie 2 out_L > out_R, w scenie 3 out_R > out_L — w chwili szczytu i średnio w klatkach, gdzie
  wyjście > 0,5 szczytu.
- **K3 zapominanie:** w scenie 9 średnie wyjście w t ∈ [2,0; 3,0] s ≤ 0,05 × szczyt sceny 1.

Tylko do raportu (nie kryteria): kiedy oko „odpala” (pierwsze przekroczenie 50 % szczytu, jako θ), czas liczenia
na klatkę, oraz stare oko (`Eye`) na tych samych scenach. Dalej, jeśli PASS: (i) podłączenie do `live_avoid.py` jako
`--eye mucha` i sprawdzenie z mózgiem na nagraniu syntetycznym, (ii) nagrania z prawdziwej kamery (Adam) z tymi samymi
kryteriami. Jeśli FAILED: zapisuję wynik i nie poprawiam stałych pod ten test.
