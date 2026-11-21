# Plan na po Explory: skóra dotykowa i rękawiczki (21 XI 2026)

Źródło pomysłu: film Founders Inc na X (21 XI, https://x.com/fdotinc/status/2123956755705233548) — firma robi „skórę
dotykową”: warstwa z przewodzącymi ziarnami między elektrodami, opór mierzony w poprzek arkusza → **obraz nacisku**
(siatka 0–255, jak zdjęcie), z którego algorytm ocenia chwyt i poślizg. Treść odczytana z fragmentów napisów i rysunków
(bez dźwięku) — nie pełny zapis.

## Po co nam to
Dziś do muchy wchodzą 2 liczby (2× FSR). Przy tak wąskim wejściu przemieszane połączenia nie mogą przegrać z prawdziwymi
(raport 10 XI; przegląd 21 XI, `mucha_plus_uczenie_research_20261121.md`). Obraz dotyku daje **mapę miejsca** → różne
punkty do różnych szczecinek nogi muchy (mapa 230 szczecinek uda w `touch_map.py`, HIPOTEZA). Odruchy zależą od miejsca
dotyku (testy 19 XI), więc to wejście, przy którym połączenia muchy mogą mieć znaczenie.

## A. Rękawiczka dla chwytaka (skóra na szczękach SO-101)
- Tanio, samemu: Velostat (folia zmieniająca opór pod naciskiem) między paskami miedzi w kratkę, np. 8×8 na szczękę;
  odczyt Arduino (wiersz po wierszu). Koszt kilkadziesiąt zł — **niesprawdzone**, do wyceny.
- Najpierw symulacja: ta sama siatka w MuJoCo (czujniki dotyku w kratce na padach) → szczecinki muchy wg mapy.
- Test (spisany przed liczeniem): mapa 8×8 vs 2 czujniki; prawdziwe połączenia vs przemieszane strojone OSOBNO (P2)
  + placebo (2 przemieszania między sobą); miara: wykrycie poślizgu i właściwy odruch zależnie od miejsca.

## B. Rękawiczka dla człowieka (nagrywanie dotyku)
- Człowiek w rękawiczce z tą samą folią chwyta przedmioty → nagrane obrazy nacisku = jak dotyk wygląda przy dobrym chwycie
  i przy poślizgu. Pomysł znany z badań (rękawica dotykowa MIT, Sundaram i in., Nature 2019 — do sprawdzenia szczegółów).
- Użycie u nas: (1) realistyczne bodźce dotyku do testów muchy zamiast wymyślonych; (2) porównanie: czy odruch muchy
  na nagrany poślizg jest podobny do reakcji człowieka (czas, siła). **Mucha dalej decyduje** — nagrania są tylko bodźcem
  i miarą, nie sterowaniem.

## Kolejność
1. Symulacja A (bez sprzętu). 2. Jeśli A pokaże przewagę mapy i połączeń → zakup folii, prototyp 8×8 na szczękę.
3. B jako źródło bodźców. Nic z tego nie jest uruchomione.
