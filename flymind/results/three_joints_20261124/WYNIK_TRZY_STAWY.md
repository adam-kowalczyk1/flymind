# Trzy stawy z sieci bez sekwencji zadania — wynik (24 XI 2026, tylko MuJoCo)
Plan: `experiments/three_joints/PREREG_THREE_JOINTS.md` (przed przebiegiem, skróty w PRE_TEST_HASHES.txt). Liczby: `analysis.json`. 80 przebiegów, 10 ziaren.

**Glu −1 (główne): TAK.** Mediany zmiany kąta w oknie nacisku 3–5 s (min…max po ziarnach):
| | bark | łokieć | nadgarstek |
|---|---|---|---|
| spokój | 0 | 0 | 0 |
| palec 1 | +0,12° (0,05…0,53) | −2,34° (−3,06…−1,99) | 0 |
| palec 2 | −1,98° (−2,90…−1,19) | −1,12° (−1,63…−0,64) | 0 |
| palec 1, losowe 92 receptory | +0,14° | −0,42° | 0 |
Każda różnica palec 1 − palec 2 w barku i łokciu ma ten sam znak w 10/10 ziaren (Holm p 0,018). Rozpoznanie 3 warunków z ruchu 30/30.
Próg 0,02 rad: spełnia łokieć (palec 1 − spokój), bark (palec 2 − spokój), bark i łokieć (palec 1 − palec 2); łokieć palec 2 − spokój 0,0195 — o włos nie.
Przed dotykiem: ramię nieruchome, pule ruchowe 0 Hz, komendy 0 (10/10). Po zwolnieniu ruch się kończy, ramię zostaje w nowym miejscu.
Nadgarstek: pula 0 Hz przez cały czas, komenda 0 w każdym takcie. Flag SafetyLayer 0, strażnik stołu 0, kontakty 0; cel po bezpieczniku = cel sieci.

**Glu +1 (dodatkowe):** w spokoju też bez ruchu. Każdy nacisk uruchamia prawie ten sam ruch trzech stawów (bark −8…−9°, łokieć −40…−43°, nadgarstek −18…−19°),
który NIE kończy się po zwolnieniu (3 s dalej). Różnica między palcami mała (łokieć 2,6° z 40°; 8/10 ziaren jednego znaku).

**Ograniczenia:** nacisk = sygnał czujnika, nie mechaniczne pchnięcie; palce pobudzają 230 i 92 receptory wg HIPOTEZY mapy; tasowania: patrz WYNIK_TASOWANIA.md (dane NIE wyróżniają się), więc nie wolno
pisać „dzięki konektomowi”; jedna poza, jedna siła (40 mV = nasycenie); jedna losowa podgrupa 92; bez czucia własnego kontaktu.
Po fakcie (poza planem): palec 1 vs palec 2 z ruchu: Glu −1 20/20, Glu +1 19/20.
