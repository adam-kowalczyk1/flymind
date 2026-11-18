# Most B1: oko flyvis → LPLC2 (MaleCNS) — „zbliżający się obiekt”. Zapisane PRZED testem (16 XI 2026)

Cel: sprawdzić, czy wyjście gotowego oka (flyvis, bramka G2-fv/G3-fv PASS) podane na prawdziwe połączenia
T4/T5 → LPLC2 z MaleCNS daje neurony LPLC2 wybiórcze dla zbliżania (warunek wstępny drogi LPLC2/LPLC4 → DNp07/GF → noga).

## Co zostało ustalone przed testem (eksploracja, ujawniona)
- Układ współrzędnych: MaleCNS (sąsiedzi (1,1), test_eye_gate) i flyvis (sąsiedzi (1,−1), `hex_to_pixel`) to sieci
  heksagonalne obrócone o 30°. Obrót MaleCNS → flyvis = **+30°**, dobrany z: kierunki anatomiczne T4 w MaleCNS
  (oś Mi9 → Mi4, 849–883 komórek na podtyp, R ≥ 0,95: a 143°, b −37°, c 46°, d −113°) vs kierunki preferowane T4 modelu
  flyvis 000 zmierzone moimi krawędziami (a 178°, b −9°, c 59°, d −84°). Po obrocie +30° różnice 1–17°.
  Znak (PD ∥ Mi9 → Mi4: Mi9 po stronie preferowanej, Mi4 po stronie zerowej) z literatury (Haag/Borst, Takemura 2017) — REPORTED.
  Odwrotny znak = obrót 210° — liczony jako kontrola (raport).
- Niezależne sprawdzenie (nieużyte do dopasowania): „ramiona” LPLC2 w MaleCNS po tym obrocie wskazują na zewnątrz zgodnie
  z kierunkami flyvis: T4a/T5a 180°, T4b/T5b −11°, T4c/T5c 92°, T4d/T5d −95° (R 0,88–0,97). VERIFIED.
- Próba dymna na modelach 40–41 (poza zestawem testowym) wykazała: (1) nagłe pojawienie się dysku dawało sztuczny skok →
  poprawione: pierwsza klatka nieruchomo 1 s, liczona tylko faza ruchu; (2) odczyt liniowy: zbliżanie ≈ 2× oddalanie,
  ale dysk przesuwany bokiem pobudza tak samo jak zbliżający się, a permutacje podtypów dają to samo co układ prawdziwy;
  hamowanie LPi z danych (9 061 synaps Glu na LPLC2 vs ~63 000 T4/T5) zmienia wynik o 5–10 %.
  **Przewiduję porażkę warunku przesunięcia i permutacji.** Test uruchamiam mimo to, bo to zapisany następny krok
  i modele 000–009 są lepsze niż 40–41.

## Test
- Modele flyvis `flow/0000/000–009` (10 najlepszych wg rankingu autorów, bez wyboru). Bez ziaren (deterministyczne).
- Mapa: `bridge_prep.py 30` (+ `210` jako kontrola). Wejścia T4/T5 prawej strony → 91 LPLC2, 49 LPLC4, 375 LPi;
  położenie T4 = środek wejść Mi1, T5 = środek wejść Tm1/Tm2/Tm4/Tm9; 88,4 % synaps w polu flyvis (promień 15).
- Bodźce (`bridge_loom.py`): dysk ciemny (główny) i jasny (raport) na szarym tle; 7 środków (0 i 6 na promieniu 5 kolumn);
  ZBLIŻANIE: l/v = 40 ms, promień 0,5 → 8 kolumn (5,1°/kol.); ODDALANIE: odwrócone w czasie; PRZESUWANIE: dysk r = 4,
  droga 16 kolumn w tym samym czasie, 4 kierunki. Pierwsza klatka nieruchomo 1 s, potem ruch, 0,2 s przytrzymania.
- Odczyt: pobudzenie T4/T5 = max(0, aktywność − stan po adaptacji); LPLC2 = Σ synapsy × pobudzenie (podtyp i kolumna z mapy);
  wariant GŁÓWNY (1): minus Σ synapsy LPi→LPLC2 × (średnie pobudzenie LPi na synapsę wejściową), znak Glu = −1, potem max(0, ·);
  wariant 0: tylko T4/T5. Odpowiedź = szczyt w fazie ruchu. Komórki: LPLC2 ze środkiem pola ≤ 4 kolumny od środka bodźca (min. 3).
- LI = (Z − max(O, P)) / (Z + max(O, P)), Z/O/P = średnia po komórkach zbliżanie/oddalanie/przesuwanie (średnia z 4 kierunków).
- Kontrola: 23 permutacje podtypów a–d (ta sama dla T4 i T5, w wejściach bezpośrednich i do LPi).

## Kryteria (ciemny dysk, wariant 1, obrót 30°)
**B1 PASS** gdy wszystkie trzy: mediana LI po (10 modeli × środki) > 0; zbliżanie wygrywa z oddalaniem i przesuwaniem
w ≥ 80 % przypadków; mediana LI układu prawdziwego > medianie każdej z 23 permutacji.
Raport bez wpływu na werdykt: dysk jasny, wariant 0, LPLC4, obrót 210°, LI zbliżanie vs samo oddalanie.
Przejdzie → B2: LPLC2/LPLC4 → DNp07 → sieć nogi → nadgarstek w MuJoCo (osobny plan). Nie przejdzie → raport, decyzja Adama.
