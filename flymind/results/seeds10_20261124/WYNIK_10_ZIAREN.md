# Zamrożona nowa podstawa i bark, 10 nowych ziaren (24 XI 2026, MuJoCo, Glu −1)
Plan: `experiments/one_run/PLAN_10_ZIAREN.md`; zamrożenie `zamrozenie.json` (38 plików, pule, znaki, macierz sieci), `PRE_HASHES.txt`. Ziarna 27 602 001–010. Sprawdzian: ziarno 27 601 001 odtworzone co do bitu. 10 z 10 przebiegów ukończonych, żaden nie zastąpiony.
Liczby: `analysis.json`, `ruch_10_ziaren.csv`, `ruch_10_ziaren.png`. Plus = bark w dół, podstawa promotorem, łokieć zgina.

- **Główna miara** (bark, 20,00→22,00 s): 12,686 · 13,274 · 12,460 · 12,207 · 12,587 · 12,393 · 12,558 · 12,356 · 12,175 · 12,338°; mediana 12,43°; zakres 12,18–13,27°; 10/10 w dół (0 bez ruchu).
- A0: podstawa mediana +1,70° (1,15…2,43; 10/10 plus), łokieć −2,39° (−2,91…−2,10; 10/10 minus). A1: podstawa +1,43° (0,64…2,01; 10/10), łokieć −0,93° (−1,30…−0,48; 10/10), bark +3,96° (3,60…4,21; 10/10). Zgięcie nadgarstka: 0 w każdym ziarnie.
- Spokój 0–6 s: 0° ruchu, 0 komend i 0 impulsów w 76 odczytywanych neuronach i w 5 grupach we wszystkich 10. Szum 2 mV sam nie wywołuje impulsów, więc to bezruch braku aktywności, a nie wstrzymanie ruchu.
- Ograniczenia: flagi SafetyLayer 0, strażnik 0, kontakty 0 we wszystkich 10. Kąt wobec sumy komend ≤ 0,03°.
- Zbliżenie 2 poza miarami: kula wchodzi w kamerę (przerwa ≤ 2,8 mm, w części ziaren ujemna).
- Nie sprawdzono: tasowań, Glu +1, odwróconych znaków, innych poz i siły nacisku.
