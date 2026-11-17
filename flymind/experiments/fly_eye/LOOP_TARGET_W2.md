# LOOP_TARGET — W2 „detektor zbliżania LC4 z oka flyvis przez synapsy MaleCNS” (zapisane PRZED testem, 17 XI 2026)

Polecenie Adama (17 XI): „zrealizuj ten plan” (`reports/fly_eye_reverse_engineering_plan_20261116.md`).
Stan zastany: W0 i W1 wykonane 16 XI (W1 FAILED, `reports/fly_eye_w0_w1_atlas_20261116.md`). Most B1 (LPLC2 z T4/T5, inna sesja)
= **FAILED** dla ciemnego dysku; ta sama sesja liczy teraz B1b (LPLC2, jasny dysk, modele 010–019). Plan mówi: „B1 FAILED → nie stroić”.
**Nie stroję B1 i nie dotykam LPLC2.** W2 dotyczy **LC4** — drugiego detektora z planu (§3 W2, decyzja 4), którego nikt jeszcze nie testował
i który słucha innych typów niż LPLC2 (T2, TmY3, Tm4, Tm2, Tm3, a nie T4/T5). To nowy, osobny test, a nie poprawka B1.

## Pytanie
Czy LC4 policzony z gotowego oka flyvis **samymi liczbami synaps MaleCNS** odpowiada mocniej na zbliżający się dysk
niż na oddalający się i przesuwany bokiem?

## Dane i mapa (`w2_prep.py`, tylko odczyt MaleCNS; wykonane przed tym celem, bez flyvis)
- 55 komórek LC4 prawej strony; 153 426 synaps wejściowych; z typów obecnych we flyvis (27 typów) 88 723 = 57,8 %;
  w polu oka flyvis (promień 15 kolumn) 50,9 % całego wejścia. Reszta (LC4↔LC4, hamujące Li, mózg) **nie jest modelowana**.
- Położenie komórki wejściowej: własna kolumna, a gdy jej brak (T2, TmY3, Tm3…) środek ważony jej wejść od komórek z kolumną
  (rozrzut 0,7–1,3 kolumny). Obrót MaleCNS → flyvis +30° (ustalony i sprawdzony w `PREREG_BRIDGE.md`, inna sesja).
- Znak: acetylocholina +1, glutaminian −1, GABA −1, nieznany 0 (jak B1). Ujemne: Tm30, Tm5c, TmY15, TmY5a; zero: TmY14 (49 synaps).

## Bodźce
Identyczne jak B1 (`bridge_loom.movies`, kod bez zmian): dysk ciemny (główny) i jasny (raport), 7 środków, zbliżanie l/v = 40 ms,
oddalanie = odwrócone w czasie, przesuwanie dysku r = 4 w 4 kierunkach; 1 s bez ruchu przed ruchem; krok 10 ms.

## Odczyt (`w2_run.py`, ta sama reguła co B1, jedna dla wszystkich komórek)
wydzielanie komórki wejściowej = max(0, aktywność − stan w ostatniej klatce przed ruchem);
LC4 = max(0, Σ znak × liczba synaps × wydzielanie); odpowiedź = szczyt w fazie ruchu.
Komórki: LC4 ze środkiem pola ≤ 4 kolumny od środka bodźca (5–6 komórek na środek; min. 3). Żadnych parametrów dopasowanych.
LI = (Z − max(O, P)) / (Z + max(O, P)); Z/O/P = średnia po komórkach dla zbliżania / oddalania / przesuwania (średnia z 4 kierunków).

## Kryteria (ciemny dysk, modele flyvis `flow/0000/000–009`, 70 przypadków = 10 modeli × 7 środków)
- **K-A:** mediana LI > 0.
- **K-B:** zbliżanie wygrywa z oddalaniem **i** z przesuwaniem w ≥ 80 % przypadków.
- **W2 PASS = K-A i K-B.** (te same progi co B1)
- **K-C (osobna etykieta „zależy od prawdziwych połączeń”):** mediana LI układu prawdziwego > mediany każdej z 23 losowych permutacji
  etykiet typów (liczby synaps typu X podane na aktywność typu Y; ziarna 23 505 001–023). K-C nie wchodzi do W2 PASS,
  ale bez K-C **nie wolno** pisać, że wybiórczość wynika z konektomu — tylko że „taki odczyt oka flyvis ją daje”.
- **K-D (sceny z kamery robota, W0 z 16 XI, krok 20 ms, optyka `w1_atlas.hex_movie`):** komórki LC4, których ≥ 50 % zmapowanych synaps
  leży w kolumnach w polu kamery; odpowiedź = średni szczyt. Model OK, gdy S3 (zbliżanie) > każda z S1 (spokój), S2, S2r (bok), S4 (ruch ramienia).
  **K-D PASS, gdy ≥ 8/10 modeli OK.** Osobna etykieta; mówi, czy detektor odróżnia zbliżanie od własnego ruchu ramienia.
- Opisowo (bez werdyktu): jasny dysk, LI osobno względem oddalania i przesuwania, wyniki na model, miejsce wśród 24 układów,
  K-D bez S4, przebiegi czasowe (obraz `w2_lc4_przebieg.png`, model 000).

## Przewidywanie (przed danymi)
Nie wiem. B1 nie odrzucił przesuwania dla LPLC2, więc K-B może nie przejść także tutaj. K-D prawdopodobnie nie przejdzie przez S4
(obrót ramienia przesuwa cały obraz szachownicy). Próba dymna na modelu 040 (poza zestawem) sprawdziła tylko, że potok działa
(kształty, brak NaN); liczb LI nie oglądałem.

## Zasady
- Jeden przebieg, modele 000–009, najwyżej 2 moje procesy (druga sesja liczy B1b), wątki torch ograniczone do 3.
- Po wyniku nie zmieniam progów, bodźców, mapy ani odczytu.
- **W2 PASS →** piszę osobny cel W3 (LC4 → neurony zstępujące przez synapsy MaleCNS → sieć nogi „pre” → ramię w MuJoCo).
  **W2 FAILED →** stop: raport, bez strojenia, decyzja Adama. W3 wtedy NOT IMPLEMENTED.

## Wyniki
`flymind/results/fly_eye_20261117/w2/`: `map_LC4.npz`, `discs_*.npz`, `cam_*.npz`, `w2_result.json`, `w2_lc4_przebieg.png`, `PRE_W2_HASHES.txt`.
