# P3 — oko flyvis wyuczone OD ZERA na połączeniach MaleCNS (spisane PRZED uczeniem, 21 XI 2026)

## Połączenia (`p3_connectome.py` → `malecns_flyvis.json`, raport `malecns_flyvis_raport.json`)
- Typy, pary typów, znaki = flyvis (zmieniamy tylko liczby i miejsca synaps). Pary z R1–R8, CT1, Am — z flyvis (brak danych
  kolumnowych w MaleCNS; hybryda, 94 pary). 484 pary z MaleCNS; 27 par bez synaps w MaleCNS usuniętych (lista w raporcie).
- Liczby BEZWARUNKOWE (suma w rdzeniu / liczba komórek celu). Przyczyna eksplozji T1: średnia tylko po komórkach z
  połączeniem (2–3× za dużo). Suma pary = suma flyvis (siłę pary flyvis i tak uczy) → z MaleCNS bierzemy rozkład po
  przesunięciach. Przesunięcia niosące 80 % synaps pary (4221 przesunięć vs 2140 we flyvis). Bez wypełniania luk
  (n_syn_fill 0 — MaleCNS jest kompletny). Ramka typów bez heksu wyrównana stałym przesunięciem (T4/T5: 0).
- Siła startowa: scale = 0,01 × 2140 / 4221 = 0,00507 (średni sygnał startowy jak flyvis; sprawdzone: max |V| ≈ 2, flyvis 1,3).
Uwaga: przed tym planem obejrzałem tylko stabilność startu i czas kroku (nie wyniki uczenia).

## Uczenie
Przepis flyvis bez zmian (Sintel, ruch obrazu, partia 4, 19 klatek, dt 20 ms), `flyvis train-single`, CPU tego Maca.
Ziarna 24 107 000 + nr modelu. Czas: ok. 0,33 s/krok → 250 000 kroków ≈ 25–30 h na model.
1. **Próba:** model 000, 50 000 kroków. Bramka G0: brak NaN i średnia straty z ostatnich 1000 kroków < 0,8 × z pierwszych 1000.
2. **Główne (po G0):** modele 000–003 po 250 000 kroków (2 naraz).

## Kryteria (główne modele)
- **K1 (kierunek):** jak T1b — mediana DSI T4a–d ≥ 0,2 i T5a–d ≥ 0,2, max |V| < 100, w ≥ 3 z 4 modeli.
- **K2 (zadanie):** strata walidacyjna (EPE ruchu obrazu) ≤ 1,5 × mediana modeli flyvis 000–003 liczona tą samą drogą.
- Raport: kierunki preferowane T4/T5 vs znane; potem te oczy w T2 (komórki zbliżania) i na nagraniu oko_r2.
Po wyniku nic nie stroję. Kontrola (przesunięcia potasowane w parze) — osobna decyzja po wyniku, bo podwaja czas.
