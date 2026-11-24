# Nowa podstawa i nowy bark w pętli, scena 45 s (24 XI 2026, zapisane PRZED przebiegiem)

Tylko MuJoCo. Jedna zmiana wobec `one_run.py` (`pelny`): podstawa = promotor 4 / remotor 2, bark = zginacze krętarza 11 / prostowniki krętarza 8 (oba z sieci). Łokieć i zgięcie nadgarstka: te same neurony.
Obrót i szczęka klasycznie jak dotąd. To samo: ziarno 27 601 001, szum, wzmocnienie 0,005 rad/s/Hz, filtr 50 ms, Glu −1, SafetyLayer (zakres, 1,5 rad/s, wyprzedzenie: podstawa 0,02 rad, reszta 0,3 rad), strażnik stołu 5 mm,
dotyk A0/A1 z harmonogramu, czucie łokcia z rzeczywistego kąta, oko `FlyEye` v2. Dzisiejsze neurony barku (przedni rotator, remotor + tylny rotator) nie sterują już barkiem.

## Znaki (z geometrii, poza startowa, liczone przed próbą; `geom_znaki.py`, wartości niżej)
- Oś podstawy w świecie = (0, 0, −1): +q0 obraca zgodnie z ruchem wskazówek zegara z góry; chwytak (ramię wzdłuż +x) idzie o 8,8 mm w −y na 0,05 rad, czyli w prawo patrząc wzdłuż ramienia na zewnątrz.
  ZAŁOŻENIE (nasz wybór): ramię = lewa noga odstająca w bok od ciała muchy; przód muchy jest wtedy po prawej stronie ramienia. Promotor ciągnie nogę do przodu → **podstawa: promotor = +q0, s0 = +1**.
- +q1 opuszcza chwytak: −7,35 mm na 0,05 rad (−q1 podnosi). Zginacze krętarza unoszą nogę, prostowniki podtrzymują ciężar ciała, czyli dociskają stopę do podłoża (opis funkcji: Lesser i in.) → zginacze = −q1, prostowniki = +q1 → **s1 = −1** (bez zmiany liczby). Niepewność: Azevedo opisuje zginacz krętarza też jako napęd do przodu.
- Znak s2 = +1 i s3 = −1 bez zmian. Znaków po przebiegu nie zmieniam; zamiana znaków to osobna próba.

## Scena
Kamera na chwytaku liczona z rzeczywistej pozy (wszystkie stawy, także podstawa) w każdym takcie; tor kuli w świecie identyczny jak dotąd. Kula jest tylko rysowana.
ZNANY SKUTEK UBOCZNY (z prognozy i geometrii): przy opuszczonym ramieniu kamera podjeżdża do toru kuli; pod koniec zbliżenia 2 środek kuli może być ok. 19 mm od kamery przy promieniu 20 mm (kamera w kuli). Zapisuję odległość; takty z przerwą < 5 mm od kamery traktuję jako artefakt i nie wnioskuję z nich.

## Przebiegi (to samo ziarno)
1. `nowa` — pełny. 2. `zablokowane` — sieć liczy, ale przyrosty podstawy i barku = 0 (łokieć i nadgarstek działają): kontrola skutku ruchu tych dwóch stawów.
3. `mikro` — jak 2, ale czucie łokcia przesunięte o 1e-6 rad: miara samej wrażliwości sieci na drobne różnice.
Oryginał `one_run` to punkt odniesienia dla starego barku.

## Co porównuję (bez progów istotności; jedno ziarno = pokaz)
- Prognoza = odczyt `six_readout` przeliczony tymi znakami. Komendy = suma przyrostów podczas nowej próby. Kąty = `qpos` z MuJoCo. Osobno: błąd kąta wobec sumy komend, flagi, strażnik.
- „Ruch zmienił następną reakcję”: od pierwszego ruchu podstawy/barku > 0,05°: pierwszy takt, w którym wejścia różnią się między `nowa` i `zablokowane` (dotyk, FeCO, oko), i pierwszy takt różnych impulsów w sieci;
  różnica komend każdego stawu i impulsów (76 neuronów, 5 grup) w oknach; obok ta sama różnica `mikro` − `zablokowane`. Jeśli różnica `nowa` nie przekracza `mikro`, odpowiedź: „nie da się odróżnić od wrażliwości sieci”.
- Do sieci wchodzi z ruchu tylko FeCO łokcia i dwie liczby z oka; sygnał, który różni się wcześniej, wskazuje kanał. Wpływ kamery nieodseparowany osobną kontrolą = HIPOTEZA, tak oznaczony.
Ziarno 27 601 001 użyte ponownie celowo. Wynik pokazuję niezależnie od tego, jaki będzie.
