# Etap 3a — „nerwy” w symulacji: czy mózg muchy działa z czuciem i serwami jak w prawdziwym ramieniu? (cel zapisany PRZED testem, 18 XI 2026)

## Pytanie
Etap 1 (`TOUCH_R1_REPORT_20261118.md`): przy Glu +1 sieć muchy sama kończy zwykły dotyk dłoni, po wycięciu DNg15+DNge078 nie,
a przy chwycie łokieć i nadgarstek stoją. Tam czucie było idealne (dokładna siła z symulatora, natychmiast, w każdym takcie).
Prawdziwe ramię będzie miało 2 czujniki FSR402 przez Arduino i serwa STS3215. **Czy wynik etapu 1 przetrwa takie „nerwy”?**
Mózg muchy bez zmian (ta sama sieć, te same wagi, te same przeliczniki); zmienia się tylko wejście i wyjście.

## Nerwy (`nerves.py`, parametry ustalone z kart katalogowych przed treningiem, NIE strojone)
- Czucie: tylko 2 czujniki — dłoń i jeden pad szczęki stałej (jego odczyt → obie połówki receptorów padów; pad ruchomy bez czujnika).
  Siła × g (montaż/rozrzut, losowe na próbę), krzywa FSR402 (Adafruit: 0,2 N 30 kΩ, 1 N 6 kΩ, 10 N 1 kΩ, 100 N 250 Ω),
  próg zadziałania 0,2 N, dzielnik 10 kΩ, ADC 10 bit + szum, przeliczenie zliczeń na N krzywą nominalną (bez znajomości g), opóźnienie.
- Ruch: cele stawów co m taktów (10 ms), opóźnienie d taktów, kwant 4096 kroków/obrót; moment szczęki jako PWM (3,35 N·m = 100 %), kwant 1/1000.
- Poziomy: **typ** g ∈ [0,7; 1,1], szum σ 1,5 zliczenia, czucie +10 ms, serwa co 10 ms +10 ms;
  **pess** g ∈ [0,4; 1,2], σ 4, czucie +30 ms, serwa co 30 ms +20 ms; **ideal** = bez nerwów (sprawdzone: próba w próbę = etap 1).
- Losowość nerwów tylko z ziarna sceny → te same zakłócenia dla sieci i wycięcia.

## Trening (sceny 21421, 3 pozy, 9 par / 15 chwytów; `results/step3_20261115/nerves_train/`) — NIE dowód
Glu +1: ideal wycofanie 9/9, chwyt 9/15; typ 9/9, 13/15; pess 9/9 (5 prób z ponownym dotykiem), 14/15; typ + wycięcie 0/9.
Glu −1: typ 8/9, chwyt 15/15; pess 9/9, 15/15. Spokój przy chwycie 9/9 wszędzie.
Uwaga z treningu: chwyt z nerwami wychodzi CZĘŚCIEJ niż idealnie — prawdopodobnie dlatego, że jeden czujnik padu pobudza obie
połówki receptorów. Nie zmieniam tego (decyzja sprzętowa), opisuję w raporcie.

## Przewidywanie
Glu +1: NV_A–NV_D spełnione dla typ i dla pess. Glu −1: NV_A raczej NIE (w etapie 1 tylko 69 %: lekkie przedmioty jadą z dłonią).

## Test — raz
`nerves_run.py`, sceny `--seed 21941`, `21942`, `21943`, po 6 póz. Na każdą scenę i oba Glu: ideal N, typ N, pess N, typ Nboth, pess Nboth
(30 przebiegów, najwyżej 3 naraz). Bez tasowań (pytanie dotyczy odporności, nie wybiórczości — ta była w etapach 1 i 2).
Wyniki: `results/step3_20261115/nerves_test/`, analiza `analyze_nerves.py` → `analysis_nerves_r1.json`.

## Kryteria (osobno dla każdego Glu; GŁÓWNE = typ, pess = drugie, te same progi)
- **NV_A**: wycofanie (dłoń puszczona, prawdziwa siła < 0,05 N na końcu) ≥ 80 % par.
- **NV_B**: z wycięciem DNg15+DNge078 wycofanie ≤ 20 % par.
- **NV_C**: przy chwycie łokieć i nadgarstek stoją ≥ 95 % par.
- **NV_D**: chwyt (sukces próby C) nie gorszy niż bez nerwów o więcej niż 10 punktów procentowych.
- „Mózg muchy działa z nerwami” = NV_A–NV_D dla typ. Miary sukcesu liczone z PRAWDZIWEJ siły w symulatorze, nie z odczytu czujnika.

## Zastrzeżenia z góry
- To model nerwów, nie prawdziwy sprzęt: nie ma luzów przekładni, innej sztywności serw, nagrzewania, przesunięcia czujnika poza miejsce dotyku.
- Moment szczęki jako PWM — czy prawdziwe STS3215 w tym trybie da się tak sterować, sprawdzimy dopiero na ramieniu (NIEZNANE).
- Symulacja, jeden zestaw parametrów neuronu, dłoń = szczecinki głowy (BM), palce = noga T2 L (wybór modelu).
- Wynik negatywny jest wynikiem; nie zmieniam parametrów nerwów po teście.
