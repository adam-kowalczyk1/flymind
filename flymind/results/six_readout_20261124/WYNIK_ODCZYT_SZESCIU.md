# Odczyt sześciu osi w próbie 45 s (24 XI 2026, MuJoCo, Glu −1, ziarno 27 601 001)
Plan przed przebiegiem: `experiments/one_run/PLAN_ODCZYT_SZESCIU.md`, sumy `PRE_HASHES.txt`. Jeden przebieg, jedno ziarno: pokaz, nie test. Nic z nowych odczytów nie poszło do stawów.
Liczby `analysis.json`; identyfikatory i impulsy `neurony.csv`; przebiegi w czasie `aktywnosc_w_czasie.npz`; wykresy `szesc_osi_45s.png`, `obrot_a_podstawa.png`.

- Zgodność: 16 z 16 pól dawnego zapisu równe co do bitu (kąty, komendy, cele, częstości, oko, dotyk, kontakty, impulsy 5 grup); różnica kątów 0. Sprawdzian: obecny bark, łokieć i nadgarstek odtworzone z pojedynczych neuronów = zapisane (≤ 4e-15 Hz).
- Poza oknami bodźców wszystkie komendy 0 (poza ogonem filtra oraz 4 impulsami krętarza i 2 szczęki T2 w pierwszych 0,03 s po końcu nacisku).
- Suma komend w 45 s (+ = pierwsza grupa mięśni): podstawa +3,22°, bark −20,07° (A0 −12,30°; A1 −3,94°; zbliżenie 1 +0,41°; zbliżenie 2 + A1 −3,78°), łokieć −3,39° (identyczny z dzisiejszym), zgięcie nadgarstka 0, obrót +3,65°.
- Obrót a podstawa: nie są kopią. Takty, gdy podstawa daje komendę (> 0,57 °/s), a rotatory milczą (< 0,05 °/s): 86 (0,86 s); odwrotnie 18 (0,18 s). Oba > 0,05 °/s: zgodne 220, przeciwne 34 (przy progu 0,57: 101 i 12).
  A0: podstawa +1,50°, rotatory −0,34°. A1: +0,65° i +1,86°. Zbliżenie 2 + A1: +1,07° i +2,22°. Zbliżenie 1: 0 i −0,07° (jeden impuls tylnego rotatora).
  Liczy się przy tym tylko 96 impulsów podstawy i 45 rotatorów; jeden impuls w grupie 2 neuronów = skok do 2,9 °/s, więc przeciwne kierunki to głównie pojedyncze impulsy i ogony filtra.
- Chwytak T1: ltm 0 i ltm1 0 impulsów; ltm2 3 impulsy (12,48, 12,56 i 36,54 s, jeden neuron 1050615112, tylko przy zbliżeniu, nie przy dotyku). T2: zaciskanie 593 impulsy (A0 132 Hz, do 0,94 N·m; A1 7 Hz), zwalnianie 24 (zbliżenie).
- Dodane po przebiegu: rozkład na pojedyncze neurony i czasy epizodów (`obrot_a_podstawa.png`).
