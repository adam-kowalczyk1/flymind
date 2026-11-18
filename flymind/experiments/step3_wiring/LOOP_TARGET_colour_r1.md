# Benchmark „kolor × położenie × czas pętli” (cel zapisany PRZED testem, 16 XI 2026)

## Po co (prośba Adama 16 XI)
Pytanie: co się stanie, gdy zmienimy położenie i kolor przedmiotu? System ma trzy moduły i musi zamykać pętlę decyzyjną w czasie poniżej 60 ms.

Trzy moduły w każdym takcie (100 Hz czasu symulacji):
1. **Percepcja:** kamera na chwytaku → maska przedmiotu → prąd LC10a L/P albo sylwetka do pomiaru.
2. **Decyzja:**
   - E: sieć z MaleCNS (1931 neuronów: droga wzrokowa + obwód nogi T2 L). DNa02 obraca bazę na przedmiot, a nerwy ruchowe nogi sterują szczęką.
   - A: kontroler klasyczny.
3. **Wykonanie:** klasyczne rusztowanie (dojazd, podniesienie, transport, puszczenie) + warstwa bezpieczeństwa → komendy stawów.

## Co jest nowe (kod `colour_bench.py`; `vision_manipulation.py` i `encoder.py` bez zmian, podmiany tylko w pamięci)
- **Percepcja „chroma”:** przedmiot to piksele o nasyconym kolorze, w dowolnym odcieniu. Wykluczone są piksele własnego chwytaka (maska z 7 położeń szczęki) i piksele rzutujące się na pudełko (własna kinematyka).
- **Percepcja „green”:** dotychczasowa, wykrywa tylko zieleń.
- **To nadal nie jest oko muchy.** Prąd podawany do LC10a to sztuczne pobudzanie (decyzja Adama z 12 XI).
- **Kolor przedmiotu zmienia tylko wygląd;** fizyka jest bez zmian. Kolory: zielony (40,180,50; jak dotąd), czerwony (200,45,40), niebieski (45,70,210), żółty (225,200,40), biały (235,235,235).
- **Położenie przedmiotu:**
  - losowe w strefie podajnika: każdy z 45 przedmiotów (9 kształtów × 5 materiałów) ma nowe położenie i obrót;
  - dla danego przedmiotu położenie jest to samo we wszystkich kolorach i ramionach (pary).
- **Czas pętli:** czas zegarowy taktu kontrolera bez kroku fizyki, czyli klatka → percepcja → decyzja → bezpieczeństwo → komenda.

## Eksploracja przed testem (sceny rozwojowe 21 990 xxx, tylko 2 przedmioty — uczciwie)
| Ramię / percepcja / kolor | Wynik | p99 pętli | Maks. |
|---|---|---|---|
| A / chroma / czerwony | 2/2 | 26,6 ms | 84,6 ms |
| E / chroma / czerwony | 2/2 | 28,4 ms | 83,3 ms |
| E / chroma / zielony | 1/2 | — | — |
| E / green / czerwony | 0/1 (nie widzi przedmiotu) | — | — |

Porażka E przy zielonym to chwyt sieci (`snn_released`), nie percepcja. Błąd położenia z kamery: 0–13 mm.

## Test (raz)
- **Sceny:** `--seed 21991`, czyli sceny 21 991 000–21 991 440 (45 przedmiotów × 1 poza). Szum drogi wzrokowej: 39 991 000–440.
- **Ramiona:**
  - chroma: A_cam i E_vis_touch × 5 kolorów, każde na 45 przedmiotach;
  - green: A_cam i E_vis_touch × zielony na 45 przedmiotach;
  - green × {czerwony, niebieski, żółty} na 9 przedmiotach (9 kształtów, materiał hard_grip) — kontrola czułości testu.
- **Uruchomienie:** `one_colour.sh` + `colour_jobs.txt`, xargs -P 5 -L 1 → `results/step3_20261115/colour/`.

## Kryteria (analiza `analyze_colour.py`, zapisana przed testem)
- **K0 (test czuły):** percepcja „green” na kolorach czerwonym, niebieskim i żółtym ma ≤ 2/9 sukcesów w każdym ramieniu. Jeśli nie, test nie mierzy koloru i wynik jest NIEWAŻNY.
- **K1 (odporność na kolor, osobno dla A i E, percepcja chroma):** dla każdego z kolorów czerwony, niebieski i żółty, w parach z zielonym:
  - różnica co najmniej −10 pp;
  - i McNemar nie wskazuje istotnego pogorszenia (p < 0,05 przy n10 > n01).
- **K2 (sieć nie gorsza od klasycznego, chroma, 4 kolory nasycone razem, 180 par):**
  - dolna granica 95 % bootstrapu par (10 000, ziarno 21 991 999) różnicy E − A ≥ −10 pp.
- **K3 (czas pętli, chroma):** p99 czasu taktu < 50 ms w każdym kolorze, czyli 10 ms okresu kamery + p99 obliczeń < 60 ms.
  - Opisowo: maksimum i liczba taktów > 50 ms.
- **WERDYKT** „system trzech modułów z siecią muchy działa niezależnie od koloru i położenia, z pętlą < 60 ms” = K0 i K1(E) i K2 i K3(E).
- **Opisowo:**
  - biały (szary stół → percepcja chroma powinna go nie widzieć: ograniczenie zapisane z góry);
  - sukces w zależności od położenia (odległość od środka strefy);
  - błąd położenia z kamery.

## Oczekiwania zapisane uczciwie
- K0 spełnione: stara percepcja nie widzi innych kolorów.
- K1 raczej spełnione dla A; dla E niepewne, bo porażki E są głównie w chwycie (sieć nogi), a nie w percepcji.
- K2 niepewne lub raczej nie. Wzrok v3 dał A 98 i E 86 na 135, czyli różnicę −9 pp; granica 95 % zapewne spadnie poniżej −10 pp.
- K3 raczej spełnione dla p99 (dotąd p99 26–33 ms). Maksimum przekracza 60 ms: pojedyncze takty 80–650 ms, prawdopodobnie przez inne procesy na tym samym komputerze.
- Biały: ok. 0 w percepcji chroma.

## Ograniczenia
- Symulacja. Czas pętli liczony jest na tym komputerze, w czasie zegarowym, przy innych procesach w tle. Nie obejmuje opóźnienia prawdziwej kamery ani serw.
- Sieć wydaje tylko część komend: obrót bazy przy patrzeniu i szczękę. Resztę robi klasyczne rusztowanie.
- Strefa położeń jest ta sama co dotąd: zmieniają się położenie i obrót w strefie, ale nie odległość robota od strefy.
