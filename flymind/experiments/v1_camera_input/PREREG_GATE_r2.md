# Bramka r2 — opcja 1: dynamika typów z literatury (zapisane PRZED uruchomieniem, 16 XI 2026)

Po porażce r1 (`results/v1_camera/gate/GATE_RESULT_20261116.md`: G1 PASS, G2/G3 FAILED). Decyzja Adama 16 XI: „najpierw
pierwszą opcję, potem drugą i tak w kółko”. Jedyna zmiana względem r1: dynamika typów (`eye_gate_lit.py`):
- dolnoprzepustowe (Borst i in. 2020, PMC7069908): **Mi4, Mi9, Tm9**, τ = 50 ms (Borst 2018, PMC6016951);
- pasmowe (jw.): **Mi1, Tm3, Tm1, Tm2, Tm4** — błona τ_m = 10 ms (mój wybór, Borst nie filtruje ich dolnoprzepustowo),
  wyjście = górnoprzepustowy τ 250 ms + 10 % składowej stałej (Borst 2018);
- pozostałe typy τ = 50 ms jak r1. Wartości z literatury, **nie dopasowane do wyniku**.
Próba dymna (15 501 060–061): stabilna, g = 1.

Wszystko inne jak `PREREG_GATE.md` (bodźce, miara szczytu, DSI, G1–G3, progi, 40 tasowań C1, Glu +1 opisowo).
Ziarna: dane 15 502 011–020 (A = 011–015, B = 016–020); tasowania 15 511 001–040, szum tasowań = 15 502 011–014.
Wyniki: `flymind/results/v1_camera/gate_r2/`. Nie przejdzie → opcja 2 (flyvis), zgodnie z decyzją Adama.
