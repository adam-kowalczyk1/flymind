# FJ2: notatki z pilotów (eksploracja, bez ziaren, szum 0; to nie są wyniki testu)

## Pilot 1 (`pilot_arm.py`, 2026-11-03)

Start Q_POSE, piłeczka na wprost w odległości 0,20 / 0,27 / 0,34 m.

- **Odległości 0,20 i 0,27 m:** piłeczki nie ma w kadrze (g = 0), sieć nie dostaje bodźca, ramię stoi.
- **Odległość 0,34 m:**
  - Glu −1: zbliżenie z 94 do 80 mm. Wzrok pobudza też pulę goleni, więc szczęka zamyka się na pusto.
  - Glu +1: ramię oddala się z 94 do 130 mm.

## Pilot 2 (`pilot_arm2.py`, 2026-11-03)

**Zmiany względem pilota 1:**
- piłeczka w strefie widzenia: 0,30 / 0,34 / 0,38 m (skan widoczności: z Q_POSE kamera widzi piłeczkę tylko w 0,30–0,40 m);
- szczęką steruje sam dotyk (FlyJaw z FJ1), bez wejścia wzrokowego;
- badane jawnie oba kierunki przypisania: s1, s2 ∈ {+1, −1}.

**Wyniki (odległość punktu chwytu od piłeczki):**

| Wariant | 0,30 m | 0,34 m | 0,38 m |
|---|---|---|---|
| Glu −1, s1 = +1, s2 = +1 (mapowanie z DESIGN.md, spisanego przed pilotami) | 71 → 17 mm, obie szczęki w kontakcie (11 / 9 N), piłeczka przesunięta o 27 mm | 94 → 80 mm | 126 → 121 mm |

- **Glu −1, s1 = −1:** ramię się oddala we wszystkich odległościach (do 168–181 mm).
- **Glu +1:** wyniki niespójne. Mapowanie z DESIGN oddala ramię. Przy s1 = −1 bywa zbliżenie, maksymalnie 94 → 69 mm, ale bywa też uderzenie w piłeczkę (przesunięcie 190–217 mm).

**Problem bezpieczeństwa:** przy 0,34 i 0,38 m stały pad ma 29–44 N siły, choć piłeczka się nie rusza. Najpewniej chwytak
wciska się w stół. `safety.py` nie pilnuje stołu (brak geometrii kartezjańskiej). Potrzebna jest niezależna klasyczna kontrola
odstępu od stołu dla komend sieci, np. `reach.clearance`.

**Wniosek [MODEL, pilot]:** przy mapowaniu ustalonym z góry i Glu −1 sam wzrok przez sieć muchy przybliża chwytak do
piłeczki. Nie ma jeszcze ruchu podnoszenia: brak sygnału muchy, który by go wywołał.

## Pilot 3: w którą stronę dotyk porusza ramię (2026-11-03, bez obrazu, sieć vision_leg, mapowanie z DESIGN)

Ustawienie: poza chwytu z pilota 2 (0,30 m) i 0,5 s stałego dotyku obu padów.

**Glu −1:** biodro 65–161 Hz → shoulder_lift +0,6…+1,6 rad/s. Chwytak jedzie **w dół**, 12–31 mm na 100 ms.
Wyjaśnia to wciskanie w stół: dotyk wzmacnia dociskanie, więc pętla dodatnia.

**Glu +1:** pule koaktywne, przewaga antagonistów. Chwytak jedzie **w górę**, 26–42 mm na 100 ms.
To kandydat na naturalny sygnał „unieś po chwycie”.

**Pułapka:** kierunek góra/dół zależy od przypisania pul do stawów (s1, s2), a to przypisanie jest arbitralne. Dlatego
zlecono weryfikację w literaturze dwóch rzeczy. Po pierwsze, co robią te pule MN (unoszenie i opuszczanie nogi, ruch w przód
i w tył). Po drugie, jaki jest naturalny odruch nogi na dotyk. Mapowanie „uniesienie nogi → uniesienie ramienia” ma wynikać
z biologii, nie z wyniku pilota.

## Literatura: znaczenie pul MN i odruch na dotyk (agent, źródła pobrane 2026-11-03)

**Pule MN [LITERATURA]:**
- **Sternal anterior rotator:** obrót nogi do przodu w fazie wymachu (swing). Źródło: Cheong i in., eLife RP96084, s. 2.6.1.
- **Pleural remotor/abductor i Sternal posterior rotator:** biodro do tyłu, aktywne w fazie podporu (stance).
  Źródła: Lesser 2024 (moduł „posterior coxa”); Cheong 2.6.1 i 2.7.3.
- **Tr extensor, Sternotrochanter, Tergotr.:** prostują krętarz na wspólnym ścięgnie (Lesser 2024, Extended Data Fig. 6).
  Tergotr. (TTM) w T2 opuszcza i prostuje środkowe nogi, na przykład przy wybiciu do skoku (Cheong).
  „Tr extensor = opuszczanie nogi” to wniosek z tych opisów, nie podany wprost fakt.
- **Tr flexor:** zgina krętarz. „= unoszenie” jest NIEZWERYFIKOWANE.
- **Ti extensor / flexor:** prostują i zginają goleń.
- **Fe reductor, ltm, Ta:** kierunek NIEZWERYFIKOWANY.

**Odruch na dotyk szczecinek [LITERATURA]:**
- Celowane czyszczenie miejsca dotyku. Źródło: Eichler i in. 2024, eLife RP87602, za Corfasem i Dudaiem 1989 oraz Vandervorstem i Ghysenem 1980.
- U unieruchomionej muchy nieskoordynowana aktywność „unikania” bodźca, wytwarzana w samym VNC. Źródło: Medeiros i in. 2024, Curr Biol, doi 10.1016/j.cub.2024.05.021.
- Czystego odruchu „unieś nogę po dotyku” nie znaleziono.
- U patyczaka dotyk stopy przedniej nogi aktywuje podpór środkowej (Graham 1989). To odpowiedź typu podpór, a nie uniesienie.
  Źródło przeczytane tylko jako fragment wyszukiwania.

**Znak glutaminianu na MN nóg [LITERATURA]:**
- GluCl (hamujący) jest najliczniej wyrażanym receptorem glutaminianu w MN (Lesser 2024).
- 14A, 21A i 8A to hemilinie glutaminianergiczne (Lacin i in. 2019, eLife 8:e43701).
- Brak zapisu fizjologicznego znaku dla MN nóg. Glu = −1 to rozsądne założenie domyślne z poparciem na poziomie ekspresji
  receptorów, nie fakt.

**Wniosek dla mapowania:** mapowanie z DESIGN, ustalone przed pilotami, okazuje się zgodne z biologią osi podpór/wymach.
- Pule podporu (Pleural remotor) → shoulder_lift +, co w symulacji opuszcza chwytak.
- Pula wymachu (Sternal anterior rotator) → antagonista, co unosi chwytak.

Przy Glu = −1 (założenie z lepszym poparciem) dotyk włącza pulę podporu, więc chwytak jest dociskany. To zgadza się
z odpowiedzią typu podpór. **W tym obwodzie nie ma więc naturalnego sygnału uniesienia po chwycie.** Uniesienie przy Glu +1
wynika z założenia o słabszym poparciu.

**Gdzie szukać dalej:** w danych, w pętli dotyk nogi → neurony wstępujące → mózg → neurony zstępujące → pule wymachu
(Sternal anterior rotator, Tr flexor).

**Errata (2026-11-03).** `vision_leg.py` miał w `VNC` nazwy „descending” i „ascending”, których w danych nie ma. Prawdziwe
nazwy to `descending_neuron` i `ascending_neuron`. W rzeczywistości przekaźniki pilotów 4–6 i FJ2 to wyłącznie `vnc_intrinsic`.
Liczby w notatkach pozostają poprawne dla tej definicji. Nieprawdziwy był opis, nie wynik. Poprawiono opis, nie sieć.

## Szukanie sygnału uniesienia w pętli przez mózg (2026-11-03)

**`search_lift_loop.py`** [DATA, strukturalnie, bez znaków]:
- Dotyk nogi T2 L dochodzi do 432 neuronów AN, w tym 108 bezpośrednio, a przez nie do 1295 neuronów DN.
- Kandydaci o wyjściu przesuniętym ku wymachowi: DNge037, DNge080/081, DNpe002, DNde006, DNb08.
- Kandydatów nie użyto do symulacji: wybór według wyjścia byłby wyborem pod wynik.

**`pilot_touch_brain_loop.py`** [MODEL, pilot, szum 0, J0 0,275]:
- Sieć ma 5344 neurony: noga T2 L, 100 AN wybranych według wejścia z obwodu nogi, 1932 neurony mózgu, 100 DN
  wybranych według wejścia z dotyku (nie według wyjścia) i 1705 przekaźników VNC.
- Bodziec: sam dotyk, czyli 40 mV na receptory szczecinkowe.
- Kontrola: te same neurony, ale wyjścia DN odcięte.

| | wymach (Hz) | podpór (Hz) |
|---|---|---|
| Glu −1, pętla | 7,8 | 63,5 |
| Glu −1, bez pętli | 8,7 | 42,5 |
| Glu +1, pętla | 172,7 | 177,7 |
| Glu +1, bez pętli | 165,8 | 172,2 |

**Wniosek:** przy Glu −1 pętla przez mózg wzmacnia **podpór**, czyli dociskanie, a nie uniesienie. Przy Glu +1 prawie nic nie
zmienia. W obu sprawdzonych miejscach (sam obwód nogi oraz pętla AN → mózg → DN) dane nie dają naturalnego sygnału „unieś
po chwycie”. Spójne z literaturą jest to, że odpowiedzią na kontakt jest podpór.

**Niezbadane:** czy dotyk jednej nogi uruchamia wymach INNYCH nóg. Byłoby to zgodne z celowanym czyszczeniem miejsca dotyku
(Eichler i in. 2024).

## Dotyk jednej nogi → inne nogi (`pilot_touch_other_legs.py`, 2026-11-03)

Pilot: szum 0, J0 0,275.

**Sieć z danych (10 036 neuronów):**
- obwody 6 nóg;
- MN według podklasy fl/ml/hl;
- 2284 przekaźniki `vnc_intrinsic` z obwodu T2 L do pozostałych nóg.

**Wejście:** sam dotyk T2 L (40 mV na szczecinki).
**Kontrola:** te same neurony, ale wyjścia obwodu T2 L do reszty sieci są odcięte.

**Wyniki, wymach / podpór (Hz):**

| noga | Glu −1 pełna | Glu −1 odcięta | Glu +1 pełna | Glu +1 odcięta |
|---|---|---|---|---|
| T1 L | 0,0 / 19,4 | 0 / 0 | 16,3 / 57,9 | 0 / 0 |
| T1 R | 1,4 / 0,0 | 0 / 0 | 4,5 / 18,5 | 0 / 0 |
| **T2 L (dotknięta)** | 0,0 / 59,7 | 19,6 / 42,8 | 160 / 211 | 156 / 180 |
| **T2 R (przeciwna środkowa)** | **27,1 / 4,2** | 0 / 0 | **92,9 / 14,8** | 0 / 0 |
| T3 L | 36,7 / 23,5 | 0 / 0 | 163 / 182 | 0 / 0 |
| T3 R | 4,9 / 21,5 | 0 / 0 | 64 / 97 | 0 / 0 |

**Wnioski [MODEL, pilot]:**
- Dotyk T2 L uruchamia **wymach przeciwnej środkowej nogi T2 R** przy obu znakach Glu. To pierwszy znaleziony sygnał
  uniesienia odporny na założenie o glutaminianie.
- Dotknięta noga dociska (podpór). Pozostałe nogi pobudza wyłącznie sygnał z obwodu dotkniętej nogi (kontrola odcięta = 0).
- Sprzężenie zwrotne od innych nóg wycisza wymach dotkniętej nogi: przy Glu −1 spada z 19,6 do 0 Hz.

[HIPOTEZA] Wzorzec „dotknięta noga trzyma, przeciwna się unosi” przypomina odpowiedzi typu podpór i przenoszenie ciężaru.
W literaturze tego nie sprawdzono.

**Do zrobienia:**
- kontrola z przetasowanymi połączeniami (ziarna do zarejestrowania);
- weryfikacja, że wymach T2 R nie jest artefaktem doboru przekaźników (przekaźniki wybrane według wejścia z T2 L i wyjścia do
  dowolnej innej nogi, nie do pul wymachu).

## Kontrola z przetasowanymi połączeniami (`shuffle_six_legs.py`, 2026-11-03)

Badanie eksploracyjne. Kryterium spisano w pliku przed uruchomieniem.
- **Ziarna:** 9 211 001–020 (SEED_REGISTRY.md).
- **Smoke:** ziarno 9 218 001, wynik nieanalizowany. Smoke wydrukował jednak werdykt dla 1 instancji, co ujawniam tutaj.
- **Tasowanie:** `visual_path.shuffle(equal_weight=True)`.
- **Miara:** M = wymach − podpór w nodze T2 R przy dotyku T2 L.

| Glu | M (dane) | M (10 tasowań) | Werdykt |
|---|---|---|---|
| −1 | +22,9 Hz | 16,2; 2,8; −1,0; −12,0; −0,3; −4,1; 1,4; −4,2; 2,4; 3,4 | **SPECYFICZNY** (dane > każda instancja) |
| +1 | +78,1 Hz | −87,6; −61,0; −42,8; −12,2; 30,6; 16,8; −24,1; −77,4; −40,2; −6,7 | **SPECYFICZNY** |

Rzeczy, których nie widać w tabeli:
- Przy Glu −1 przewaga jest mała: najlepsza instancja daje 16,2 Hz wobec 22,9 Hz.
- Przy Glu +1 tasowane sieci zwykle dają odwrotnie, czyli przewagę podporu.
- Dotknięta noga T2 L w sieci z danych mocno dociska (podpór 59,7 Hz, wymach 0 przy Glu −1). W tasowanych sieciach jej
  odpowiedź jest bardziej wyrównana.

**Ograniczenia:**
1. Tasowanie zachowuje stopnie i siłę wejściową neuronów, ale nie klasy neuronów. Red team FJ1 pokazał, że miesza też warstwy
   receptor → IN → MN.
2. Sieć sześciu nóg wybrano według wejścia z dotykanej nogi, nie według wyniku.
3. To model bez szumu i z jednym bodźcem (40 mV).
4. Wynik przy 10 instancjach na znak.

Wniosek [MODEL, eksploracja]: wzorzec „dotknięta noga dociska, przeciwna się unosi” zależy w tym modelu od konkretnych
połączeń z danych, a nie tylko od rozmiaru i stopni sieci.

## Red team wyniku „dotyk T2 L → wymach T2 R” (2026-11-03)

**Werdykt:** SUPPORTED WITH CAVEATS, przy Glu −1 bliżej „słabe”. Ziarna red teamu: 9 219 001–008, 011–014, 021–023, 031.
Skrypty: `scratchpad/rt_sixlegs/`.

**Utrzymuje się (wąsko):** przy dokładnie tych pulach, 40 mV i szumie 0 sieć z danych wygrywa z każdym tasowaniem przy obu
znakach Glu. 8 nowych tasowań przy Glu −1 też jest poniżej wyniku z danych, więc łącznie 18/18 (p ≈ 0,05).

**Nie utrzymuje się:**
1. **Przy Glu −1 cały efekt robi jeden typ, Tr flexor**, którego znaczenie („= unoszenie”) jest NIEZWERYFIKOWANE.
   - W samym Tr flexor M = +32 Hz.
   - Pule tylko dobrze opisane (Sternal anterior rotator wobec remotor + posterior rotator): M = +2,9 Hz przy 40 mV i ujemne
     przy 20 i 10 mV.
   - Przy tych pulach tasowania sięgają +15,4, więc specyficzności brak.
2. **Zależność od bodźca przy Glu −1:** M = +22,9 / +14,5 / **−2,5** przy 40 / 20 / 10 mV. Znak odwraca się przy słabym dotyku.
   Przy Glu +1 wynik jest odporny (+78 / +48 / +61), ale to słabiej poparty znak, a częstości ok. 160–240 Hz są blisko
   sufitu 250 Hz.
3. **Nie jest to para lewa → prawa:**
   - Dotyk T3 L daje T2 R ten sam efekt (+23,9 i +59,3).
   - Lustro, czyli dotyk T2 R, daje T2 L tylko +7,3 przy Glu −1.
   - To raczej cecha samej nogi T2 R niż „dotknięta trzyma, przeciwna się unosi”.
4. **T2 R wybrano po obejrzeniu 6 nóg.** Przy maksimum po 5 nogach 1 z 18 tasowań przebija wynik z danych.
5. **Cały efekt idzie przez 2284 wybrane przekaźniki:** odcięcie ich wyjścia daje M = 0. Tasowanie niszczy strukturę
   wbudowaną przez dobór (warstwy, klasy), więc wynik „dane > tasowanie” częściowo znaczy tylko „wybrany obwód > losowe
   okablowanie”.
   - Tasowanie zachowujące bloki klasa × noga: 3–4 instancje na znak, eksploracyjnie.
   - Przy Glu −1: −1,8…+1,8 Hz, wyraźnie poniżej 22,9. Przy Glu +1: do 61,9 wobec 78,1.
6. **Mierzona jest aktywność pul, nie ruch nogi.** Słowo „uniesienie” było skrótem myślowym.

**Poprawione twierdzenie:** w tym modelu dotyk T2 L zwiększa aktywność pul „wymachu” w T2 R bardziej niż losowe okablowanie,
ale tylko przy definicji pul zawierającej Tr flexor i przy silnym bodźcu. Nie jest to potwierdzony naturalny sygnał
uniesienia ani wzorzec przeniesienia ciężaru. Wcześniejsze zdanie „pierwszy znaleziony sygnał uniesienia odporny na założenie
o glutaminianie” **wycofuję**.

**Żeby to rozstrzygnąć, trzeba:**
- potwierdzić w literaturze, co robi Tr flexor (tabele mięśni Azevedo i in. 2024, przy pierwszym podejściu niedostępne);
- powtórzyć test na nowych ziarnach z tasowaniem zachowującym bloki i z kilkoma poziomami bodźca, ustalonymi z góry.
