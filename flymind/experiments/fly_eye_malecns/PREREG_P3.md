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
2. **Główne (po G0):** 2 modele na prawdziwym układzie (000, 001) + 2 KONTROLNE (`malecns_flyvis_shuf0/1.json`: w każdej
   parze liczby synaps potasowane między tymi samymi przesunięciami, ziarna 24 107 100/101), po 250 000 kroków, 2 naraz.
   (Zmiana 21 XI przed uczeniem, po uwadze z zewnętrznego przeglądu: w T2c prawdziwe ≈ potasowane, więc bez kontroli
   wynik nic by nie znaczył.)

## Kryteria (główne modele)
- **K1 (kierunek):** jak T1b — mediana DSI T4a–d ≥ 0,2 i T5a–d ≥ 0,2, max |V| < 100, w 2 z 2 prawdziwych modeli.
- **K3 (zasługa połączeń):** mediana odległości kierunku preferowanego T4/T5 od znanego dla prawdziwych mniejsza o ≥ 15°
  niż dla potasowanych, LUB K1 spełnione w 2/2 prawdziwych i ≤ 1/2 potasowanych. Bez K3 nie mówię, że „połączenia muchy uczą kierunku”.
- **K2 (zadanie):** strata walidacyjna (EPE ruchu obrazu) prawdziwych ≤ 1,5 × mediana modeli flyvis 000–003 liczona tą samą drogą.
- Raport: kierunki preferowane T4/T5 vs znane; potem te oczy w T2 (komórki zbliżania) i na nagraniu oko_r2.
Po wyniku nic nie stroję. Nazwa uczciwa: oko HYBRYDOWE — od MaleCNS pochodzi głównie kto z kim i w którym miejscu;
fotoreceptory, CT1, Am i znaki z flyvis; siły uczone. Na Explory pokaz zostaje na obecnym oku (to jest badanie w tle).

## Zmiana 21 XI wieczór, PRZED uczeniem (Adam: „odpal trenowanie”)
Próba i główne uczenie łączę: 4 modele ruszają od razu, naraz (po 2 wątki), `run_p3_main.sh`, ziarna 24 107 000–003
(000, 001 = prawdziwe; 002, 003 = potasowane shuf0/shuf1). **Bramka G0 liczona na modelu 000 po 50 000 krokach**
(te same warunki co wyżej); jeśli nie przejdzie — zatrzymuję wszystkie 4 i zapisuję FAILED. Test 30 min: 1,29 s/krok
dla 1 modelu (dane w 1 wątku); 4 naraz — szybkość niezmierzona, szacunek 4–6 dób.

## Pomiar szybkości 4 naraz (21 XI 20:29–20:44, ok. 300 kroków, przed jakimkolwiek wynikiem)
Model 000: 252 kroki w 906 s = **3,6 s/krok** (1 model sam: 1,29). 250 000 kroków ≈ 10,4 doby dla wszystkich 4.
Propozycja do decyzji Adama (spisana teraz, przed wynikami): ocena główna (K1–K3) na punkcie kontrolnym **100 000 kroków**
(≈ 4,2 doby), dalsze uczenie do 250 000 tylko jako rozszerzenie (raport osobno). Jeśli Adam nie zdecyduje — zostaje 250 000.
**Decyzja Adama 21 XI wieczór: „Ocena po 100 000”.** Ocena główna K1–K3 na punkcie kontrolnym najbliższym 100 000 kroków
(ten sam numer kroku dla wszystkich 4 modeli); potem uczenie zatrzymane, chyba że Adam zdecyduje inaczej.

## Zmiana 22 XI rano, przed wynikami (Adam: „po tym zapisie zatrzymujesz, odpalasz jeden, żeby sprawdzić, czy działa”)
Po 11 400 krokach strata wszystkich 4 spadła < 1 % (bez punktu odniesienia). Modele 001–003 wstrzymane zaraz po zapisie
`chkpt_00005` (wznowienie od niego); 000 liczy dalej sam. Obok **kontrola K0: oryginalny konektom flyvis uczony od zera** tym
samym przepisem (`task_name=p3_ctrl`, ziarno 24 107 010, domyślne n_syn_fill 1 i scale 0,01) — żeby wiedzieć, jak wygląda
normalne uczenie na początku.
**Szybki sprawdzian G0′** (gdy K0 przejdzie ≥ 20 000 kroków): spadek straty modelu 000 (średnia z kroków [k−1000, k] /
średnia z [0, 1000], przy tym samym k) ≥ połowa spadku K0. Nie → zatrzymuję 000, P3 FAILED (nie uczy się). Tak → wznawiam
001–003. G0 z 50 000 krokami na 000 zostaje bez zmian.
