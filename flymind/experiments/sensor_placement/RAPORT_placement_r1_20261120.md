# Gdzie dać 2 czujniki FSR402 na chwytaku — raport r1 (20 XI 2026)

Cel spisany przed liczeniem: `TARGET_placement_r1.md` (sha256 `e59159e0…fccf`, commit 20f4d7d).
Kod: `placement.py` (sprawdzian `--check`), rysunki: `draw.py`. Wyniki: `results/placement_r1b*.json`, rysunki w `results/`.

## Krótko (dla Adama)
- **Miałeś rację.** Obecny układ (szczęka stała 30 mm od czubka + „dłoń”) **nie czuje żadnego** długiego przedmiotu
  trzymanego czubkami (0 z 39 sytuacji) i tylko 24 % chwytów pudełek.
- Powód leży w kształcie szczęki, a nie w samym miejscu czujnika.
  - Wewnętrzna strona szczęki ma **schodki**: najbardziej wystaje sam czubek, czyli ostatnie ~10 mm.
  - Tam szczęka ma tylko **6–10 mm** szerokości.
  - Pole czynne FSR402 (Ø 12,7 mm) się na czubku nie mieści, więc wszystkie „płaskie” miejsca są cofnięte o 2–5 mm za czubek.
  - Przedmiot trzymany czubkami w ogóle ich nie dotyka.
- **Zgodnie z planem (czujnik cały płasko): kryteria P1, P2, P3 = NIE ZDANE.** Najlepsza para to dwa czujniki na szczęce
  ruchomej (32 i 50 mm od czubka). Łapie 38 % chwytów pudełek i tylko 10 % długich przedmiotów przy czubkach.
- **Wariant dodatkowy (spoza planu):** czujnik **na samym czubku szczęki stałej, środek ~7 mm od czubka**, folia
  wystaje 2–3 mm za boki czubka. Drugi czujnik zostaje w obecnym miejscu A0 (30 mm od czubka).
  - W symulacji para łapie **92–100 % długich przedmiotów przy czubkach** i 49–69 % chwytów pudełek.
  - Z samego wzoru, który czujnik czuł, rozpoznaje „czubek czy nasada” w 85–92 % przypadków.
  - Oba czujniki są na szczęce stałej, więc kabelki się nie ruszają.
  - **Tego nie było w planie i nie jest sprawdzone na sprzęcie:** nie wiadomo, jak FSR402 reaguje, gdy połowa pola
    czynnego wisi w powietrzu. Trzeba to zmierzyć ciężarkami.
- **Ręka:** zbliżająca się ręka pierwsza dotyka czubków i krawędzi (ok. 40 % to czubki), prawie nigdy płaskich ścian.
  - Dla pierwszego dotyku żaden układ nie ma więcej niż 1 %.
  - Przy miękkiej dłoni (2 mm wgniecenia, spoza planu) najlepiej wypada czubek: ~20 %.
  - Dotyk na szczękach to więc **zapasowy** zmysł unikania; główny jest wzrok.

## Liczby (cel r1: folia t = 0,45 mm; S1 = ręka, S2 = pudełka, S3 = długi pręt czubkami; wynik = średnia)
| układ | S1 | S2 | S3 | wynik | „gdzie” |
|---|---|---|---|---|---|
| obecny hw2p (A0 + dłoń) | 0,000 | 0,236 | 0,000 | 0,079 | 1,00 (z 349 wykrytych) |
| pierwotny (A0 + szczęka ruchoma 22 mm) | 0,000 | 0,289 | 0,026 | 0,105 | 0,89 |
| **najlepsza para r1** (ruchoma 32 + 50 mm od czubka) | 0,001 | 0,384 | 0,103 | **0,163** | 0,84 |
| ta sama analiza, t = 1,45 mm: najlepsza (A0 ~27 mm + ruchoma 32 mm) | 0,001 | 0,511 | 0,385 | 0,299 | 0,75 |
| *dodatkowy: czubek ~5–7 mm + A0 (t = 1,45)* | 0,006 | 0,693 | 0,923 | 0,541 | 0,92 |
| *dodatkowy: czubek ~5 mm + schodek 16 mm (t = 0,45)* | 0,007 | 0,493 | **1,000** | 0,500 | 0,85 |

Kryteria (cel):
- **P1** S3 ≥ 0,8 → 0,103 **NIE ZDANE**.
- **P2** wynik ≥ hw2p + 0,10 = 0,179 → 0,163 **NIE ZDANE**.
- **P3** różnica przy t = 1,45 ≤ 0,05 → 0,136, czyli **NIE ZDANE**: miejsce zależy od grubości krążka.
- **P4** para z S1 ≥ 0,5 i S3 ≥ 0,8: **brak**.

## Literatura (skrót; szczegóły w raporcie podagenta, część NIEZWERYFIKOWANA w pełnym tekście)
- **Kim i in. 2026**, arXiv 2611.10647 (NAVER LABS): miejsca czujników wybiera statystyka kontaktów. 10 dobrze
  postawionych daje więcej niż 50 rozłożonych równo, a czujniki w „martwych strefach” niczego nie wnoszą.
  To jest metoda tego raportu.
- **Mucha:**
  - szczecinki dotyku są najgęściej na **końcu** nogi; ich wejście do brzusznego zwoju ma mapę miejsca, więc mucha „wie, gdzie”
    (Tuthill & Wilson 2016, Cell 164:1046; El-Abbady i in. 2025/26, preprint);
  - dotyk końca nogi wywołuje unikanie przez sam zwój brzuszny (Medeiros i in. 2024, Curr Biol; Ramdya i in. 2015, Nature);
  - obciążenie i poślizg czują czujniki pancerza (campaniform sensilla) **przy stawach, bliżej nasady**, a reagują na
    **spadek** siły (Dinges i in. 2021, J Comp Neurol; Harris i in. 2022, J Neurophysiol).

  Wynik symulacji („czubek + bliżej nasady”) zgadza się z tym podziałem: czubek odpowiada dotykowi i unikaniu,
  a miejsce A0 obciążeniu i poślizgowi.
- **Poślizg na FSR:** wykrywanie drgań wymaga szybkich czujników (akcelerometr 8 kHz), FSR jest na to za wolny.
  Realnie da się wykryć **spadek siły** na czujniku, który jest pod kontaktem.

## Ograniczenia (uczciwie)
- Kontakt liczony **sztywno** (najbardziej wystające punkty ±0,3 mm). Prawdziwe przedmioty i plastik szczęki trochę się
  uginają, więc kontakt jest szerszy niż w modelu. Wyniki S2/S3 są raczej dolną granicą.
- Kształty to siatki producenta. Wydruk Adama może się różnić, a schodki trzeba sprawdzić suwmiarką.
- Wymiary FSR są z karty katalogowej. **Ogłoszenie Allegro mówiło „4 mm”. Zmierzyć prawdziwe sztuki:** średnicę folii i pola.
- Przedmioty: pudełka i pręty ustawione prosto. Ręka: kula R 40 / 150 mm. Poślizgu (c) tu nie liczono.
- **r1 miał błąd** (zewnętrzna ściana serwa liczona jako szczęka, przedmiot mógł wejść za dłoń). Poprawione w r1b;
  wnioski r1 i r1b są te same, liczby r1b w tabeli.

## Dopisek 1 (20 XI, przed południem): grubszy krążek, spoza planu
Krążek 2,5 / 3,5 / 4,5 mm podnosi pokrycie pudełek (S2 do 0,80), ale długie przedmioty przy czubkach dalej tylko 0,41–0,51.
Plik: `results/placement_r1b_t2.5-3.5-4.5.json`. Wariant „czubek” pozostaje najlepszy dla twojego przykładu.

## Dopisek 2: poślizg w MuJoCo (cel `TARGET_slip_r1.md`, sha256 `61265b0e…a4d1`, kod `slip.py`)
- Model:
  - szczęki = schody co 1 mm z prawdziwych siatek;
  - przegub szczęki z modelu producenta (bezwładność przekładni 0,028, tłumienie 0,6, tarcie 0,052);
  - czujniki = krążki Ø12,7 × 0,45 mm;
  - przedmiot w poprzek szczęk, szczęki w dół, siła ciągnąca 0 → 20 N w 4 s.
- Sprawdziany przed liczeniem:
  - szczęka ruchoma w modelu leży dokładnie tam, gdzie siatka;
  - pręt Ø15 przy czubku daje 19,6 N na czujniku czubka, a szczęka zamyka się do q = −0,007 (zgodnie z geometrią).
- **Poprawki zrobione przed wynikami** (błędy w ustawieniu, nie w kryteriach):
  - MJCF czytał kąty w stopniach, więc szczęka przechodziła przez limit;
  - brakowało bezwładności przekładni;
  - start z q = 1,0: słaby chwyt nie zamykał się w 1 s, teraz start z q = 0,4.
- **Unieważnione po wynikach:** 4 próby na układ, w których pudełko przesunięte o 60 mm nie leżało między szczękami
  (błąd projektu próby). Liczby poniżej są bez nich. Z nimi wynik jest w nawiasie.

| układ | M1 czuje trzymanie | M2 ostrzega PRZED poślizgiem | M3 czuje wypadanie (≤ 200 ms) |
|---|---|---|---|
| **T** czubek + A0 | **0,75** (0,68) — pręty 28 / 36 | 0,16 | 0,55 |
| H obecny (A0 + dłoń) | 0,05 — pręty 0 / 36 | 0,03 | 0,03 |
| R najlepsza para r1 (szczęka ruchoma) | 0,05 — pręty 0 / 36 | 0,06 | 0,03 |

- **Q1** (T: M1 ≥ 0,8 i ≥ H + 0,3): **NIE ZDANE** (0,75 < 0,8; druga część spełniona: 0,75 vs 0,05).
- **Q2** (T: M3 ≥ 0,8): **NIE ZDANE** (0,55).
- **Q3** (opis): żaden układ nie ostrzega przed poślizgiem (M2 ≤ 0,16). Siła normalna na FSR prawie się nie zmienia,
  zanim przedmiot ruszy; zmienia się dopiero, gdy już się przesuwa. Zgadza się to z literaturą: poślizg widać jako spadek
  siły, a FSR jest za wolny na drgania.
- **Ważna poprawka do analizy geometrii:** okrągły pręt dotyka ściany tylko wzdłuż linii na wysokości swojej osi.
  - Czujnik na czubku czuje pręty, których oś jest ≤ ~15 mm od czubka: wszystkie 12 / 12 przy osi ≤ 10 mm.
  - Grubsze pręty trzymane głębiej (oś ~17–23 mm od czubka) nie trafiają w żaden czujnik.
  - Wynik „S3 = 0,92–1,00” z geometrii był więc za optymistyczny, bo pręty traktowano tam jak płaskie.
    Realnie jest ok. 0,75–0,80 dla czubka, a 0 dla obecnego układu.
- Pole `q_hold` w `slip_r1.json` to kąt szczęki na KOŃCU próby, a nie w chwili trzymania (zła nazwa; na metryki nie wpływa).

## Dopisek 3: „mucha wie, gdzie czuje” — mapa szczecinek
- W danych MaleCNS (pole type/subclass/entryNerve) nie ma miejsca szczecinki na nodze. Obecny podział „udo / goleń”
  w `touch_map.json` to HIPOTEZA: grupy z połączeń, a przypisanie grupy do części nogi jest arbitralne.
- Literatura podaje regułę: **Elabbady i in. 2026, Current Biology**, doi:10.1016/j.cub.2026.03.045, dane
  github.com/tuthill-lab/elabbady_bristles_2026.
  - Szczecinki z KOŃCA nogi kończą się w **środku** ośrodka nogi w zwoju brzusznym, a z nasady przy jego **brzegu**
    (koncentryczne pierścienie).
  - Miara: średnia odległość synaps aksonu od środka ośrodka.
  - Zrobione na samicy (FANC), przednia noga. Brak gotowej tabeli typ → część nogi dla MANC/MaleCNS.
- Żeby to zastosować do naszych 322 szczecinek T2 L, potrzebne są **położenia synaps** z neuPrint, a tych lokalnie
  nie mamy. Mapa wyjdzie wtedy jako „wyprowadzona tą regułą”, a nie „opublikowana”.

## Dopisek 4: mapa koniec nogi / nasada policzona (cel `TARGET_bristle_map_r1.md`, kod `bristle_map.py`)
- Dane: 321 z 322 szkieletów SWC MaleCNS v1.0 (publiczne, CC-BY), pobrane za zgodą Adama, 3,6 MB w
  `data/malecns/skeletons_T2L_bristle/` (poza repo). 310 neuronów miało ≥ 3 zakończenia.
- Miara: odległość środka zakończeń aksonu od środka populacji. Małe = koniec nogi (reguła Elabbady 2026).
  Synaps nie było, więc użyłem zakończeń szkieletu (przybliżenie).
- **Sprawdzian: ZDANY.**
  - Typ SNta wyjaśnia η² = **0,78** zmienności. Przy potasowanych typach η² = 0,08 (1000×), p < 0,001.
  - Odporność: z medianą zamiast średniej η² = 0,81.
  - Typy mają więc spójne miejsce: od końca nogi SNta21, SNta29, SNta19, SNta26, SNta30… do nasady SNta35, SNta34, SNta22/33.
- **Obecna hipoteza `touch_map.json` jest ODWROTNIE.** Grupa „femur” (udo) leży bliżej środka niż „tibia_tarsus”
  (mediana 3 613 vs 4 476 jedn., Mann-Whitney p = 7·10⁻¹⁷), czyli według reguły jest bliżej KOŃCA nogi.
  Arbitralne przypisanie z 19 XI trafiło na odwrót. Mapowanie „swap” było tym właściwym.
- Przypisanie do czujników według celu:
  - **czubek → 84 neurony** z rang u ≤ 0,27 (typy SNta21, SNta29 i część SNta19/26/30);
  - **A0 → 93 neurony** z u 0,31–0,61.
  - Lista w `results/bristle_map_r1.json`.
- Ograniczenia:
  - środek populacji, a nie zmierzony środek ośrodka;
  - zakończenia szkieletu, a nie synapsy;
  - reguła pochodzi z nogi przedniej samicy (FANC), a my mamy środkową nogę samca (MaleCNS).

  Mapa jest **wyprowadzona tą regułą, nie opublikowana**.

## Dopisek 5: „mucha wie, gdzie czuje” w całym mózgu (cel `TARGET_where_r1.md`, kod `where_test.py`)
Ten sam mózg co na żywo (`live_avoid.build`, glu −1, hamulec hub). Czubek → 84 szczecinki „końca nogi”, A0 → 93 „środkowe”.
1 N przez 1 s, 5 ziaren szumu, ramię nieruchome, oko wyłączone.

| warunek | MDN (cofanie) [Hz] | staw 2 (cofanie ramienia) | szczęka (zaciskanie) | DN ucieczki, DNg15, DNge078 |
|---|---|---|---|---|
| nic | 0 | 0 | 0 | 0 |
| **czubek** | **16,1 ± 2,1** | −1,99 | 0,04 | 0 |
| **A0** | 10,2 ± 2,6 | −1,09 | **0,40** | 0 |
| oba | 25,9 | −3,47 | 0,44 | 0 |

- **W1** (MDN czubek > A0 w ≥ 4/5 ziaren): **ZDANE, 5/5.** Dotyk końca „nogi” mocniej uruchamia cofanie. Zgadza się
  z literaturą: dotyk końca nogi wywołuje unikanie (Medeiros 2024).
- **W2** (rozróżnienie czubek / A0 ≥ 0,9): **ZDANE, 1,00.** Mózg odpowiada jakościowo inaczej:
  - **czubek → cofanie** (MDN, staw 2), szczęka się prawie nie zaciska;
  - **A0 → zaciśnięcie szczęki** (0,40), słabsze cofanie.
- **W3** (opis): różnica czubek–A0 jest **przeciętna** na tle 100 losowych podziałów tych samych szczecinek (percentyl 0,55).
  - Każde dwie różne grupy szczecinek dają w tym mózgu jakąś różnicę; samo „wie, gdzie” nie jest więc wyjątkowe dla tej mapy.
  - Uczciwie: miara W3 była źle skonstruowana. Wymiary, które w próbach czubek / A0 były stale zerowe, dostały
    znikome odchylenie i wyolbrzymiły odległości losowych podziałów. Do powtórzenia na samych MDN / staw 2 / szczęka.
- Co zostaje: kierunek W1 i podział ról (czubek = cofanie, środek szczęki = zaciskanie) wynikają z mapy z danych, a nie z doboru.
  Nie wiadomo jeszcze, czy losowe podziały dają TEN SAM podział ról. To jest następny sprawdzian.

## Dopisek 6: czy podział ról wynika z mapy? (cel `TARGET_where_r2.md`, kod `where_r2.py`)
- **G1 gradient** (5 przedziałów po ~62 szczecinki, od końca nogi do nasady): **NIE ZDANE**, bo gradientu nie ma.
  - MDN: 4,2 / 6,7 / 0 / 0 / 4,3 Hz.
  - Zaciskanie szczęki: 0,01 / 0,18 / **0,30** / 0,22 / 0,02.
  - Obraz to „**środek nogi → zaciskanie, oba końce → cofanie**”, a nie płynna zmiana.
- **G2 losowe grupy:** **ZDANE.** 0 z 200 losowych par daje tak duży podział ról jak mapa z danych.
  - Zaciskanie ≥ 0,36 nie wyszło ani razu; 95. percentyl losowych to 0,16.
  - Podział „czubek → cofanie, A0 → zaciskanie” jest więc **swoisty dla mapy wyprowadzonej z danych**, a nie przypadkiem.
- Uczciwie: to są własności modelu (konektom + nasza sieć ALIF + nasze wejście 40 mV/N). Nie twierdzę, że prawdziwa
  mucha tak robi. Twierdzę tylko, że w tym mózgu miejsce dotyku ma znaczenie, a nadaje mu je anatomia, nie nasz dobór.

## Wieczorny test na sprzęcie (bez ramienia, tylko Arduino) — instrukcja
1. **Suwmiarka:**
   - czujnik: średnica folii, średnica pola czynnego (jaśniejszy krąg), grubość;
   - szczęka stała: szerokość czubka 5 mm i 10 mm od czubka, długość wystającego „schodka” czubka.
   - Model mówi: 6–10 mm szerokości, schodek ~10 mm. Jeśli wydruk się różni, policzę od nowa.
2. **Czujnik na stole, cały podparty:** położyć na krążek kolejno telefon (~200 g), szklankę z wodą, butelkę 0,5 l
   (~520 g). Strona testu czujników zapisuje odczyty.
3. **Ten sam czujnik na krawędzi stołu,** tak żeby ~połowa pola czynnego wisiała w powietrzu (jak na czubku szczęki).
   Te same ciężarki, kładzione na podpartą część.
4. Porównanie 2 vs 3 mówi, czy czujnik na czubku z wystającą folią czuje tak samo, słabiej czy wcale.
   Od tego zależy decyzja, czy przenosimy czujnik na czubek.

## Następne kroki (propozycja, nic nie uruchomione)
0. **Dostęp do neuPrint (Adam):** zalogować się na neuprint.janelia.org (konto Google) i skopiować swój token API.
   Wtedy policzę mapę czubek / nasada regułą Elabbady i podłączę czujnik czubka do „końca nogi”.
1. Adam mierzy czujnik i szczękę (suwmiarka: szerokość czubka, schodki).
2. Test na sprzęcie bez ramienia: FSR na czubku z wystającą folią, ciężarki 50–500 g w środku czubka. Czy odczyt rośnie
   tak samo jak przy całym polu podpartym?
3. Poślizg w MuJoCo dla układu „czubek + A0”: czy spadek siły wyprzedza wypadnięcie pręta.
4. Przypisanie w mózgu **według miejsca**: czubek → szczecinki końca nogi, A0 → bliżej nasady / obciążenie.
   Bez dobierania pod wynik.

## Dodatek 7 — dlaczego czubek prawie nie rusza ramienia (why r1, cel c01bf58, 20 XI)

Ramię (bark, łokieć, nadgarstek) w modelu = różnica pul ruchowych **nogi przedniej T1 L**. Czubek wchodzi w szczecinki **nogi środkowej T2 L**.
3,3 N, 1 s, ramię nieruchome, 5 ziaren (2011230–34), `why_r1.py` → `results/why_r1.json`.

| warunek | pule T1 (Hz, stawy 1–3, POS/NEG) | ramię Δ° w 1 s |
|---|---|---|
| nic | 0/0, 0/0, 0/0 | 0, 0, 0 |
| czubek | 0,1/0,2, 0,1/1,9, 0/0 | 0, −0,5, 0 |
| A0 | 0/0,4, 0/1,6, 0/0 | 0,1, −0,5, 0 |
| dłoń (BM, głowa) | 143/0, 0,6/27, 26/0 | −40, −7, −7 |
| czubek bez MDN | 0/0,3, 0,1/1,4, 0/0 | 0,1, −0,4, 0 |
| dłoń bez MDN | 144/0, 0,6/26, 25/0 | −40, −7, −7 |

- **D1: „nie dochodzi”** — pobudzenie pul T1 z czubka to 1,2 % tego z dłoni (S = 0,012, K = 0,010; próg 0,2).
- **D2:** wyciszenie MDN prawie nic nie zmienia ani dla czubka (K 1,9 → 1,6), ani dla dłoni. MDN nie jest drogą do ramienia.
- **D3 (budowa):** brak wag bezpośrednich. Drogi dwuetapowe z czubka są małe i mieszane w znaku. Dłoń ma silne drogi (BM → DNg15/DNge078 → neurony ruchowe T1).
- **Poza celem (opis):** MDN ma w sieci 501 odbiorców i drogi do pul T1 w 2–3 krokach (2 318 / 815 104), czubek w 3 krokach 878 769, dłoń 5 087 953.
  Drogi więc **istnieją w budowie**, ale aktywność czubka (MDN ~16 Hz) gaśnie po drodze i nie przekracza progu neuronów pośrednich.

**Wniosek:** w tym mózgu dotyk nogi środkowej daje cofanie „w obrębie nogi” (MDN) i zaciskanie szczęki, ale **nie steruje nogą przednią**, czyli ramieniem.
Mocne cofanie ramienia od dotyku idzie wyłącznie drogą z głowy (BM → DNg15/DNge078), którą w układzie „czubek” nic nie pobudza, bo nie ma czujnika na dłoni.
Nic nie stroiłem. Podłączenie czubka także do szczecinek głowy byłoby wyborem mapy pod wynik, więc tego nie robię.
