# P1 — oko muchy na PRAWDZIWEJ kamerze (spisane PRZED nagraniem, 21 XI 2026)

Oko: `oko_mucha.FlyEye` z VS/HS (test 2 PASS, stałe OUT_FULL2 = 0,04322, G0 = 0,04628) — **bez żadnych zmian**.
Nagranie: `hardware/sensors/nagraj_oko.py` (Adam, Terminal.app; głos prowadzi; 640×400, ~80 kl./s, ffv1 bez strat; czas każdej
klatki = zegar komputera). Ocena: `oko_kamera.py` (klatki skalowane do 160×100 jak w live_avoid). Ramię: nic nie jest wysyłane.
Sprawdzian ścieżki: `oko_kamera.py --check` (sceny testu 2 zszyte w jedno nagranie) → PASS; `nagraj_oko.py --fake` → klatki = znaczniki.

Okna (od początku polecenia „teraz” do końca + 0,5 s), wynik okna = szczyt max(L, R) / OUT_FULL2 (1 = pełne 40 mV w mózgu):
zbliżanie na środku ×3, z lewej ×2, z prawej ×2 (kamera leży); dłoń w poprzek ×3; odsuwanie ×3; kamera w ręce: obrót poziomy ×3,
pochylanie ×3, zbliżanie w czasie obrotu ×2; światło ×2 (tylko raport); spokój ×1; zasłonięcie obiektywu (znacznik czasu).

## Kryteria (PASS = wszystkie)
- **K1:** okna „w poprzek”, „odsuwanie”, „obrót”, „pochylanie” (11): szczyt ≤ 0,25 × mediana szczytów zbliżań w ≥ 80 % okien.
- **K2:** zbliżania (7): szczyt ≥ 0,5 w ≥ 80 % okien (mózg dostaje ≥ 20 mV).
- **K3:** strona: lewe i prawe zbliżania dają przeciwne strony we wszystkich 4 oknach (przy jednym z dwóch przypisań; które —
  raportuję, bo orientacja kamery nieznana → ewentualnie `--flip`).
- **K4:** zbliżanie w czasie obrotu: szczyt ≥ 0,5 × mediana zbliżań w 2 / 2.
- **K5:** spokój: szczyt ≤ 0,1.
Tylko raport: światło, ciemność przy zasłonięciu (sprawdzian zegara), kl./s. Jeśli Adam źle wykona okno (np. pominie), okno
zostaje policzone, a w raporcie to opisuję. Po wyniku nic nie stroję; jedno nagranie = jeden wynik (oko_r1).
