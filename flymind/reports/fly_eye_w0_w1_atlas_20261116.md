# „Co widzi mucha” — W0 i W1: atlas pięter oka dla kamery robota (16 XI 2026)

Autor: Claude (Opus 5.5), sesja „oko”. Zgoda Adama: „Tak, zacznij W0–W1”. Wszystko w symulacji, bez robota, bez commita.
Etykiety: VERIFIED · PARTIALLY VERIFIED · REPORTED · INFERRED · HYPOTHESIS · NOT VERIFIED · FAILED · NOT IMPLEMENTED.

---

## 0. Najkrócej

1. **Da się zobaczyć, co odbiera oko muchy z obrazu robota.** Są obrazy i filmy dla 5 scen: kamera → mozaika oka →
   fotoreceptor → L1/L2 → Mi1/Tm1 → T4/T5 (kierunek ruchu kolorem). Pliki: `results/fly_eye_20261116/w1/atlas_*.png`,
   `film_*.gif`. Najładniej widać to przy **zbliżaniu** (S3): przy krawędziach rosnącego przedmiotu zapalają się czujniki ruchu
   ustawione w różne strony. VERIFIED (obrazy z modelu).
2. **Zapisany z góry test W1 = FAILED.**
   - K1 (jaśniej/ciemniej): **7/10 modeli** OK, próg 8 → FAILED, o włos.
   - K2 (kierunek odwraca się z ruchem): **1/10** → FAILED.
3. **Dlaczego K2 wypadło tak źle (analiza po fakcie, nie zmienia wyniku, INFERRED):** czujniki „w prawo” (T4b) i „w lewo” (T4a)
   **reagują zgodnie z kierunkiem** w 8–9 z 10 modeli. Mój test kazał jednak, żeby jeden podtyp „wygrał” z pozostałymi,
   a podtypy różnią się ogólną siłą odpowiedzi. Ten sposób liczenia był zły. Poprawny test wymaga nowego, osobno zapisanego celu.
4. To **przewidywanie modelu** (flyvis, Nature 2024, konektom samicy, parametry dopasowane przez autorów), a nie pomiar muchy.

---

## 1. Co zrobiłem

| Krok | Co | Pliki |
|---|---|---|
| W0 | 5 scen z kamery nadgarstka SO-101 w MuJoCo: ciemna kostka 4,5 cm na szachownicy blatu; 125 klatek co 20 ms (1 s bez ruchu, 1 s ruchu, 0,5 s bez ruchu). S1 spokój, S2 kostka w prawo, S2r w lewo, S3 kostka leci do kamery, S4 obrót podstawy ramienia. Ruch ustawiany ręcznie (bez fizyki) | `experiments/fly_eye/w0_render.py`, `results/fly_eye_20261116/w0/` |
| Optyka | jasność „jak Rh1” → rozmycie 5° → 721 kolumn oka flyvis. Kamera (70°) pokrywa środek oka (ok. 150°); reszta kolumn dostaje stałą szarość (wariant b) | `experiments/fly_eye/w1_atlas.py` |
| W1 | 10 najlepszych modeli flyvis (000–009, bez wybierania), jeden przebieg | `results/fly_eye_20261116/w1/model_*.npz` |
| Cel | zapisany przed uruchomieniem flyvis, hasze 22:14:55; próba dymna tylko na modelu 040 (bez oceny) | `experiments/fly_eye/LOOP_TARGET_W1.md`, `results/fly_eye_20261116/PRE_W1_HASHES.txt` |
| Analiza | niezmieniona po wyniku | `experiments/fly_eye/w1_analysis.py` → `w1/w1_result.json`, `w1_analysis.log` |

Żaden neuron poza fotoreceptorami nie dostał bodźca. Bez ziaren (flyvis deterministyczny); świat W0: ziarno 23 504 001.

## 2. Wynik testu (zapisane kryteria)

| Model | K1: znaki L1, L2, Mi1, Tm3, Tm1, Tm2 (oczek. − − + + − −) | K1 | K2: zwycięzca T4 →/← | T5 →/← | K2 |
|---|---|---|---|---|---|
| 000 | −0,22 −0,24 +0,57 +0,49 −0,29 −0,36 | 6/6 ✔ | c / a | a / d | ✘ |
| 001 | −0,37 +0,06 +0,76 +0,27 −0,63 −0,01 | 5/6 ✔ | b / a | b / a | ✔ |
| 002 | −0,33 +0,01 +0,54 +0,42 +0,04 −0,06 | 4/6 ✘ | b / b | c / c | ✘ |
| 003 | −0,55 −0,30 +0,57 +0,55 −0,29 −0,13 | 6/6 ✔ | b / a | b / b | ✘ |
| 004 | −0,21 −0,30 +0,49 +0,47 −0,25 +0,28 | 5/6 ✔ | a / a | a / a | ✘ |
| 005 | −0,59 −0,20 +0,76 +0,66 −0,08 −0,36 | 6/6 ✔ | a / b | c / c | ✘ |
| 006 | −0,37 +0,02 +0,46 +0,35 +0,18 −0,04 | 4/6 ✘ | b / b | a / a | ✘ |
| 007 | −0,81 −0,04 +0,46 +0,67 −0,01 +0,06 | 5/6 ✔ | b / a | c / c | ✘ |
| 008 | −0,47 −0,24 +0,45 +0,58 +0,07 −0,03 | 5/6 ✔ | c / c | c / c | ✘ |
| 009 | −0,50 +0,03 +0,50 +0,50 +0,06 −0,04 | 4/6 ✘ | b / b | d / d | ✘ |
| **Razem** | | **7/10 → FAILED** (próg 8) | | | **1/10 → FAILED** |

**W1 = FAILED** (VERIFIED: jeden przebieg według zapisanego celu).

Co jest pewne mimo porażki:
- **L1, Mi1 i Tm3 mają prawidłowy znak we wszystkich 10 modelach** (L1 ciemnieje przy rozjaśnieniu, Mi1/Tm3 rosną). VERIFIED.
- Słabe ogniwa to **L2, Tm1, Tm2**. Ich korelacje są bliskie zeru w połowie modeli. Możliwa przyczyna: to komórki „przejściowe”,
  a mój wskaźnik (kontrast z 200 ms) do nich nie pasuje (HYPOTHESIS, nie sprawdzone).
- **Bez ruchu oko prawie milczy:** aktywność T4+T5 w scenie S1 to 0,3–38 % aktywności przy ruchu (D1, opisowo). VERIFIED.

## 3. Analiza po fakcie (opisowo; NIE zmienia werdyktu)

Zamiast „który podtyp wygrywa” porównałem **ten sam podtyp** przy ruchu w prawo i w lewo:
indeks = (prawo − lewo)/(prawo + lewo).

| | Zgodnie z oczekiwaniem (T4b „w prawo” > 0, T4a „w lewo” < 0) |
|---|---|
| T4b | **8/10 modeli** dodatni (do +0,31) |
| T4a | **9/10 modeli** ujemny (do −0,18) |
| T5a | 8/10 ujemny |
| T5b | 7/10 dodatni |

Wniosek (INFERRED): czujniki kierunku **działają na obrazie z kamery robota**, ale słabiej niż na bodźcach z pracy.
Wyjątkiem jest model 005, który ma odwrotnie. Mój pierwotny test był źle pomyślany, bo porównywał podtypy o różnej sile.
Nowego testu nie uruchamiam bez Twojej zgody: zmiana miary po zobaczeniu wyniku to dokładnie to, czego mamy unikać.

## 4. Jak oglądać atlas

- **`atlas_S3_zblizanie.png`** (najczytelniejszy): kolumny od lewej to kamera → mozaika oka → R1 → L1 → L2 → Mi1 → Tm1 → T4 → T5.
  Czerwony = wzrost, niebieski = spadek względem chwili przed ruchem. W T4/T5 barwa = który kierunek wygrywa
  (czerwony a, niebieski b, zielony c, pomarańczowy d). Przy zbliżaniu każdy bok kwadratu świeci innym kolorem: oko „widzi”
  rozszerzanie się w 4 strony. Przy ciemnym przedmiocie krawędzie T5 (OFF) wskazują na zewnątrz w modelu 000 (D2 = +0,33, opisowo).
- **`film_S2_bok.gif`, `film_S3_zblizanie.gif`, `film_S4_ramie.gif`**: to samo w ruchu (kamera, oko, L1, Mi1, T4, T5).
- Szary obszar wokół mozaiki to część oka, której kamera nie widzi (oko muchy patrzy prawie dookoła).

## 5. Decyzje dla Adama

1. **Nowy, osobno zapisany test kierunku W1b** z miarą „ten sam podtyp, ruch w prawo vs w lewo” (+ ruch góra/dół dla c/d),
   na nowych scenach (inne położenie i kolor przedmiotu), żeby nie liczyć na tych samych danych. **Rekomenduję: tak.**
2. **Dalej W2 (most do LC4/LPLC2)** — zgodnie z planem dopiero po wyniku B1 innej sesji. **Rekomenduję: czekać na B1.**
3. **Atlas na plakat/demo?** S3 (zbliżanie) dobrze pokazuje „co widzi oko”. **Rekomenduję: tak**, z podpisem
   „przewidywanie modelu flyvis na obrazie z kamery robota; test zapisany z góry nie przeszedł w całości”.

Do czasu odpowiedzi niczego więcej nie uruchamiam.
