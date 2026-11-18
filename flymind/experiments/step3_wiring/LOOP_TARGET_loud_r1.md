# Etap 2 — „dwa odruchy” kontra tasowania o TEJ SAMEJ aktywności (cel zapisany PRZED testem, 18 XI 2026)

## Pytanie
Krok 4 r2 (`LOOP_TARGET_reflex_r2.md`, `REFLEX_R2_REPORT_20261116.md`) potwierdził: sieć z danych częściej niż tasowania
F i L robi oba odruchy (dotyk dłoni → cofnij, nie zaciskaj; dotyk palców → zaciśnij i trzymaj). Raport zostawił otwarte:
sieć z danych jest ogólnie „głośniejsza”. **Czy przewaga zostaje, gdy tasowania mają tę samą aktywność?**

## Wyrównanie aktywności (`loud.py`, bez robota, bez patrzenia na wynik zadania)
Aktywność = średnia częstość wszystkich neuronów poza pobudzanymi receptorami, ostatnie 0,5 s z 1 s bodźca 40 mV,
średnia z dwóch warunków: dłoń (receptory T1 L) i palce (pady → T2 L). Tasowanie: W · g, jedno g dla całej sieci (ze
znakiem), g z bisekcji do ±2 % aktywności sieci z danych (gdy aktywność skacze z g — najbliższe trafienie, odchyłka
w pliku kalibracji). Sieć z danych bez zmian. Kalibracja tasowań testowych liczona po zapisaniu tego pliku, przed testem;
pliki `results/step3_20261115/loud_test/calib_{F,L}_g{±1}.json` haszowane razem z kodem.

Pomiar bez wyrównania (trening, tasowania 21 100 001/002/006/007): dane Glu +1 6,65 Hz vs F 1,7–2,5, L 3,3–5,6;
Glu −1 2,14 vs F 0,65–0,71, L 1,5–1,6. Potrzebne g: F 1,38–2,13, L 1,09–1,44.

## Trening (sceny 21401, 3 pozy, 13 par; `results/step3_20261115/loud_train/`) — NIE dowód
OBA (oba odruchy w parze): Glu +1 dane 8/13; wyrównane F 5, 0; L 0, 10. Glu −1 dane 2/13; F 2, 2; L 8, 3.
Dla porównania r2 (bez wyrównania, 77 par): F prawie zawsze 0, L 0–34.

## Przewidywanie (z treningu)
H-M(F) i H-M(L) raczej **niespełnione** dla obu Glu: po wyrównaniu aktywności przewaga sieci z danych w tym zadaniu
w większości znika. Jeśli tak wyjdzie, wynik kroku 4 r2 trzeba opisywać jako „wygrana z tasowaniami o mniejszej aktywności”.

## Test — raz
`reflex.py` (sieć z danych) i `loud.py reflex CALIB …` (tasowania z g), bez zmian w `reflex.py`. Sceny: `--seed 21874`,
`21875`, `21876`, po 6 póz (90 par na Glu). Tasowania: F1–F5 = 21 877 001–005 (`--net F`), L1–L5 = 21 878 001–005
(`--net L`), oba Glu. 66 przebiegów, najwyżej 3 naraz. Wyniki: `results/step3_20261115/loud_test/`.

## Kryteria (`analyze_loud.py` = logika `analyze_reflex2.py`: para ważna, gdy w sieci N oba podjazdy osiągalne; wynik OBA)
- **H-M(F)**, **H-M(L)**: sieć z danych lepsza na OBA od każdego z 5 wyrównanych tasowań rodziny (McNemar dokładny,
  Holm w rodzinie 5, p_Holm < 0,05 i różnica > 0), osobno dla każdego Glu.
- „Przewaga kroku 4 r2 nie wynika z samej aktywności” = H-M(F) i H-M(L) dla danego Glu.
- Opisowo: W, C, OBA każdej sieci; liczba wyrównanych tasowań, które dorównały lub wygrały z danymi.

## Zastrzeżenia z góry
- Wyrównanie jedną liczbą g zmienia też siłę hamowania; to jedna z możliwych definicji „tej samej głośności”
  (inna: wyrównanie na neuronach ruchowych). Wybrana przed testem, nie zmieniam jej po wyniku.
- Symulacja, jeden zestaw parametrów neuronu, dłoń = noga T1 L, palce = noga T2 L (wybór modelu).
- Wynik negatywny jest wynikiem; nie szukam innej miary „aż wyjdzie”.
