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
