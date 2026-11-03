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
