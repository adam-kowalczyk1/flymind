# Bramka oka — opcja 2 (flyvis), wynik 16 XI 2026, 20:55

Plan zapisany przed uruchomieniem: `flymind/experiments/v1_camera_input/PREREG_GATE_flyvis.md`
(sumy sha256 w `PRE_GATE_HASHES.txt`, 15:49:41; sprawdzone po teście — zgodne). Dane: `flyvis_dsi.json`
(50 modeli `flow/0000/000–049`, wszystkie, bez wyboru), log: `flyvis_gate.log`. Bez ziaren (modele deterministyczne).

| podtyp | mediana DSI (50 modeli) | min–max | mediana odległości od znanego kierunku |
|---|---|---|---|
| T4a | **0,400** | 0,008–0,799 | **22,2°** |
| T4b | 0,170 | 0,006–0,743 | 65,5° |
| T4c | **0,583** | 0,010–0,758 | **22,5°** |
| T4d | **0,469** | 0,000–0,730 | **26,2°** |
| T5a | 0,041 | 0,000–0,785 | 29,3° |
| T5b | 0,092 | 0,000–0,830 | 162,0° |
| T5c | 0,043 | 0,000–0,702 | 90,0° |
| T5d | 0,085 | 0,000–1,000 | 56,0° |

- **G2-fv (≥ 3/4 T4 z medianą DSI ≥ 0,20): PASS** — 3/4 (T4a, T4c, T4d). VERIFIED.
- **G3-fv (≥ 3/4 T4 z medianą odległości ≤ 30°): PASS** — 3/4 (T4a, T4c, T4d). VERIFIED.
- Dla porównania na MaleCNS (r1/r2): DSI T4 0,001–0,030. flyvis daje 15–20× więcej.

Uwagi (bez wpływu na werdykt, który był ustalony z góry):
- Modele bardzo się różnią: 18/50 przechodzi oba warunki pojedynczo (0, 1, 2, 3, 6, 7, 8, 9, 11, 12, 21, 22, 23, 24, 27, 29, 36, 44);
  najlepsze modele (niskie numery = najmniejszy błąd zadania) są w większości dobre. VERIFIED.
- T5 (krawędzie OFF) słabe: mediany DSI 0,04–0,09, tylko 4/50 modeli ma ≥ 3/4 T5 ≥ 0,20. Przyczyna NIE SPRAWDZONA
  (możliwy błąd mojego pomiaru dla OFF albo cecha tych modeli). T5 nie było warunkiem bramki.
- T4b (ruch w jedną stronę poziomo) słabszy w medianie.
- To NIE jest nasz konektom MaleCNS: konektom FIB-SEM samicy, parametry dopasowane przez autorów do zadania
  przepływu optycznego. Wniosek: „gotowe oko flyvis daje działające czujniki ruchu ON (T4)”, a nie
  „MaleCNS sam z siebie widzi ruch”. Ta druga teza po r1 i r2 pozostaje FAILED.

Następny krok według planu: most flyvis T4/T5 → MaleCNS (wyjście oka → LPLC2/LPLC4 → DNp07 → noga), osobny cel.
