# Nowa podstawa i nowy bark w pętli, scena 45 s (24 XI 2026, MuJoCo, Glu −1, ziarno 27 601 001)
Plan i znaki przed przebiegiem: `experiments/one_run/PLAN_PODSTAWA_BARK.md`, sumy `PRE_HASHES.txt`, test znaków `selftest.log`. Liczby `analysis.json`; wykresy `trzy_rzeczy_obok_siebie.png`, `kamera_i_zblizenia.png`. Pokaz jednego przebiegu, nie test hipotezy. Nic na sprzęcie.

- Znaki: promotor = +q0 (zgodnie z ruchem wskazówek zegara z góry, ZAŁOŻENIE: ramię = lewa noga w bok); prostowniki krętarza = +q1 (opuszczanie), zginacze = −q1. Autotest znaków w MuJoCo 4/4.
- Koniec 45 s (prognoza / komendy / faktyczny kąt): podstawa +3,22 / +5,30 / +5,30°; bark +20,07 / +19,15 / +19,15°; łokieć −3,39 / −4,50 / −4,50°; zgięcie nadgarstka 0 / 0 / 0. Błąd kąta wobec sumy komend ≤ 0,03°. Stary bark: −3,15°.
- Flagi SafetyLayer 0, strażnik stołu 0, kontakty 0; wyprzedzenie celu ≤ 0,0007 rad. Obrót 0, szczęka opada 0,2° jak w oryginale.
- Kontrola `zablokowane` (podstawa i bark liczone, niewysłane): podstawa 2,87, bark 19,69, łokieć −3,09°. Jej impulsy 76 neuronów są identyczne z oryginałem do 36,37 s.
- Ruch zmienił impulsy: pierwszy takt różnicy 12,41 s (po ruchu barku 12,39 s); A0 i A1: zmiana łokcia −0,37° i −0,88°; w zbliżeniu 2 + A1: podstawa 3,15 zamiast 0,72°, bark 2,78 zamiast 3,40°. Łokieć A0/A1 mieści się w rozrzucie 10 ziaren z próby `three_joints` (−3,06…−1,99 i −1,63…−0,64), więc dla jednego ziarna nie jest to wykazany skutek ruchu.
- Kontrola `mikro` okazała się bezużyteczna: przesunięcie czucia łokcia o 1e-6 rad nie zmieniło żadnego impulsu (za małe, by przekroczyć próg), więc wrażliwości sieci na realne różnice nie zmierzyła.
- Zbliżenie 2: kamera przesunięta o 27,6/−4,7/−30,6 mm i obrócona o 12,7°; oko L sygnał wcześniej i tylko z lewej strony, P = 0. W 36,0–36,48 s (przed artefaktem) podstawa +1,92° zamiast +0,49°, bark 0,00° zamiast +0,83°. Od ok. 36,49 s kula jest prawdopodobnie przycinana przed kamerą (przerwa 15 mm, oko = 0) — artefakt rysowania, wcześniejszy niż przyjęty próg 5 mm.
- Wpływ kamery = HIPOTEZA: czucie łokcia różniło się też (do 0,022 rad do 36 s) i żadna kontrola nie rozdzieliła kanałów.
