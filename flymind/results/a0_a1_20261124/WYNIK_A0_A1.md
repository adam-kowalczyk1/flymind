# A0 czy A1 jako pierwszy dotyk (24 XI 2026, MuJoCo, Glu −1, ziarna 27 602 001–010)
Plan: `experiments/one_run/PLAN_A0_A1.md`; zamrożenie bez zmian. A0 z `seeds10_20261124/raw`, A1 nowe przebiegi do 22,00 s. Liczby `analysis.json`, `pary.csv`, wykres `pary.png`.

- Zgodność: 10/10 par — wszystkie 24 sprawdzone pola równe co do bitu w taktach 0–1999 (do 20,00 s); pierwsza różnica to siła odczuta w 20,01 s, potem impulsy 20,02 s i kąty 20,03 s. Siła A1 w kanale 1 = siła A0 w kanale 0 takt po takcie (maks. 3,003 N), drugi kanał 0.
- Bark: A0 mediana 12,43°, A1 3,92°, różnica A1 − A0 mediana −8,51° (−9,25…−8,21), 10/10 mniejszy przy A1. Łokieć: −2,39° i −1,04°, różnica +1,28° (0,84…1,76), 10/10. Podstawa: 1,70° i 1,46°, różnica −0,04° (−1,12…+0,28), 5 par w każdą stronę.
- Kierunek (znak) ruchu w A1 taki sam jak w A0: bark, podstawa i łokieć 10/10. Ograniczenia 0/10.
- Zastrzeżenie: A0 = 230 receptorów, A1 = 92; nie rozdzielono wpływu rodzaju receptorów od ich liczby. Znaki i mapa są naszym wyborem.
