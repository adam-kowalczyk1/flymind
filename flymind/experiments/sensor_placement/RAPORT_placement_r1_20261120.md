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

## Następne kroki (propozycja, nic nie uruchomione)
1. Adam mierzy czujnik i szczękę (suwmiarka: szerokość czubka, schodki).
2. Test na sprzęcie bez ramienia: FSR na czubku z wystającą folią, ciężarki 50–500 g w środku czubka. Czy odczyt rośnie
   tak samo jak przy całym polu podpartym?
3. Poślizg w MuJoCo dla układu „czubek + A0”: czy spadek siły wyprzedza wypadnięcie pręta.
4. Przypisanie w mózgu **według miejsca**: czubek → szczecinki końca nogi, A0 → bliżej nasady / obciążenie.
   Bez dobierania pod wynik.
