# FlyMind, 16 XI 2026: benchmark „kolor × położenie × czas pętli”

Wszystko odbyło się w symulacji, bez robota.
- Cel testu zapisałem przed uruchomieniem: `experiments/step3_wiring/LOOP_TARGET_colour_r1.md`.
- Test uruchomiłem raz; szczegóły są w `audit_log_step3_20261115.md`, wiersze C1–C5.
- Nic nie jest zacommitowane.

## Pytanie
Co się dzieje, gdy zmieniamy położenie i kolor przedmiotu? Czy system trzech modułów zamyka pętlę w czasie poniżej 60 ms? Trzy moduły to:
1. **Percepcja:** kamera.
2. **Decyzja:** sieć muchy albo klasyczny sterownik.
3. **Wykonanie:** ruch ramienia i zabezpieczenia.

## Co odkryłem przed testem
Dotychczasowy system widział **tylko zielone** przedmioty. Dotyczyło to i „wzroku” podłączonego do sieci muchy, i klasycznego pomiaru z kamery. [VERIFIED, kod]

Dopisałem nową percepcję, która rozpoznaje przedmiot po nasyconym kolorze w dowolnym odcieniu. Nie zmieniłem przy tym modułów wspólnych.

Uwaga: to nadal **nie jest oko muchy**. Jest to sztuczne pobudzanie neuronów LC10a.

## Wyniki
Liczba przedmiotów odłożonych do pudełka, na 45 (każdy przedmiot w nowym, losowym położeniu i obrocie):

| | zielony | czerwony | niebieski | żółty | biały |
|---|---|---|---|---|---|
| Sterownik klasyczny, nowa percepcja | 33 | 34 | 34 | 34 | 0 |
| **Sieć muchy, nowa percepcja** | 29 | 28 | 28 | 30 | 0 |
| Stara percepcja (tylko zieleń), oba sterowniki | 34 i 32 | 0 | 0 | 0 | — |

Według reguł zapisanych przed testem:
- **Kolor przestał przeszkadzać. Potwierdzone** dla sieci muchy i dla sterownika klasycznego: wyniki różnią się o najwyżej ±1 przedmiot. [VERIFIED, model]
- **Położenie nie przeszkadza.** Wynik jest ten sam blisko i daleko od środka strefy. Strefa ma jednak tylko około 5 × 10 cm. Błąd pomiaru położenia z kamery to ułamek milimetra. [VERIFIED, model]
- **Biały przedmiot jest niewidoczny** (0/45), bo stół jest szary. Przewidziałem to z góry.
- **Sieć muchy jest gorsza od sterownika klasycznego: FAILED.**
  - Na 180 parach odłożyła 115 przedmiotów, a sterownik klasyczny 135. To 11 punktów procentowych mniej.
  - Porażki sieci są głównie w chwycie (szczęka puszcza przedmiot), nie we wzroku.
- **Pętla poniżej 60 ms: FAILED.**
  - 99 % taktów zmieściło się w 71–95 ms.
  - Najprawdopodobniej powodem było obciążenie komputera: jednocześnie liczyło 5 moich przebiegów i test drugiej sesji („Oko muchy”). [INFERRED]
  - Przebiegi liczone przy mniejszym obciążeniu miały 24–31 ms.
  - Czystego pomiaru czasu, bez innych programów w tle, jeszcze nie zrobiłem.

## Po ludzku
Robot w symulacji przestał być „ślepy na kolory” (oprócz białego) i nie przeszkadza mu, gdzie w strefie leży przedmiot. Sieć muchy steruje nadal gorzej niż zwykły program, bo słabiej trzyma przedmiot. Czy pętla mieści się w 60 ms, rozstrzygnie dopiero osobny pomiar na nieobciążonym komputerze.

## Granice
- Symulacja.
- Czas mierzony na tym laptopie, bez opóźnień prawdziwej kamery i serw.
- Sieć wydaje tylko część komend: obrót bazy przy patrzeniu i szczękę.
- Strefa położeń jest mała.
- Białe i szare przedmioty są niewidoczne dla nowej percepcji.

## Dopisek 21:30 — czysty pomiar czasu pętli: SPEŁNIONE [VERIFIED, model]
- **Warunki:** jeden przebieg naraz (w tle był tylko jeden program innej sesji), 9 przedmiotów zielonych i 9 czerwonych. Cel zapisałem przed pomiarem: `LOOP_TARGET_latency_r1.md`.
- **Wynik:** pętla, czyli 10 ms odstępu między klatkami kamery plus obliczenia, zamyka się w około **19 ms dla 99 % taktów**. To trzy razy mniej niż limit 60 ms.
  - Sieć muchy: najdłuższy takt obliczeń trwał 10,3 ms.
  - Sterownik klasyczny: 2 z 27 tysięcy taktów przekroczyły 50 ms (najdłuższy 55 ms).
- **Wniosek:** wynik „71–95 ms” z benchmarku wziął się z obciążenia komputera, nie z samego systemu.
- **Granica:** ten pomiar nie obejmuje opóźnień prawdziwej kamery, USB ani serw.
- **Uczciwie:** pierwsze uruchomienie (21:23) nie wystartowało przez błąd w moim skrypcie. Nie powstał żaden wynik i nie zużyłem żadnych ziaren; opisałem to w dzienniku (wiersz T2).
