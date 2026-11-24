# Jeden ciągły przebieg 45 s (24 XI 2026, MuJoCo, Glu −1, ziarno 27 601 001)
Plan przed przebiegiem: `experiments/one_run/PLAN_JEDEN_PRZEBIEG.md`; film `przebieg.mp4`; wykres `przebieg.png`; liczby `analysis.json`. To pokaz jednego przebiegu, nie test hipotezy.
Zmiana po fakcie: zdarzenie = komenda > 0,05 °/s (plan: „niezerowa”; ogon filtra nigdy nie jest dokładnie zerem).

- Ruch trzech stawów = suma komend sieci (różnica ≤ 0,0004 rad). Po odcięciu sieci (te same bodźce) ruch 0. Flagi SafetyLayer, strażnik, kontakty: 0.
- Bezruch (komenda < 0,05 °/s we wszystkich stawach): 88 % czasu. Nadgarstek: pula 0 Hz, komenda 0 przez całe 45 s. Dwa stawy naraz (> 0,57 °/s): 0,96 s; trzy: 0.
- Spokój, kula w poprzek, wjazd na środek, oddalenie, wyjazd: 0 ruchu (oko 0 mV). Oko reaguje tylko na zbliżenie (40 mV).
- Zbliżenie 1 (12 s): łokieć +0,28°, bark +0,05° (tylko z wzrokiem). A0 (20–22 s): łokieć −2,40°, bark +0,42°. A1 (27–29 s): bark −1,67°, łokieć −0,54°. Zbliżenie + A1 (36–38,3 s): bark −1,96°, łokieć −0,74°.
- Bez dotyku ten sam przebieg kończy na +0,05° / +0,57°, bez wzroku −3,53° / −4,01°, bez obu 0. W 36 s: bez wzroku bark −1,86°, łokieć −0,64°.
- Ramię nie wraca do pozy startowej; koniec: bark −3,15°, łokieć −3,39°. Podstawa i obrót 0,00°, szczęka opada 0,2° (trzymane klasycznie).
