# Plakat v14: poprawki względem v13 (16 XI 2026)

- **Plik:** `~/Downloads/FlyMind_plakat_v14.pdf`.
- **Oryginał:** `~/Downloads/FlyMind_plakat_v13.pdf` (Canva) pozostał bez zmian.
- **Co zmieniono w PDF:** tylko dwa pola, „Wnioski” i podpis pod grafikami. Reszta plakatu jest identyczna z v13: porównanie pikseli pokazuje różnice wyłącznie w tych dwóch polach, a poza nimi tylko w wygładzaniu krawędzi liter.
- **Metoda:** stary tekst przykryłem białym polem i wpisałem nowy czcionką Arial. Tło ma dokładnie ten sam kolor co w oryginale (`.9412 .8157 .0471`).
- **Uwaga:** stary tekst nadal jest w pliku pod przykryciem. Przy kopiowaniu tekstu z PDF może się wkleić stara wersja. Do druku to nie przeszkadza. Najczystsza droga to wkleić poniższe teksty w Canvie.

## Dlaczego
1. **„Wnioski” w v13 były nieaktualne.** Kończyły się wynikiem negatywnym całego ramienia (0/135). Brakowało dwóch nowszych wyników:
   - krok 3: większa sieć „pre” odkłada przedmioty na poziomie klasycznego sterownika, 94 wobec 93 na 135 prób (`results/step3_20261115/test_r2/analysis_arm3r2_test.json`);
   - test „dwa odruchy” r2 z 16 XI: 49 z 77 par; tasowania swobodne i warstwowe najwyżej 34; potwierdzone dla obu znaków Glu (`results/step3_20261115/reflex_r2/analysis_reflex2.json`).
2. **Usunięty kierunek prac.** Zdanie o kierunku „np. dozowanie siły” było nieaktualne: test dawki z 16 XI dał wynik negatywny (`results/step3_20261115/dose/analysis_dose.json`).
3. **Podpis pod grafikami wychodził poza białą ramkę.** Ostatnia linia „hipotezy i decyzje są moje.” leżała na żółtym tle. Skróciłem podpis: zdanie o tasowaniu z zachowaną siłą jest już we „Wnioskach”. Dodałem dopisek, że trzeci wykres dotyczy „małej sieci nogi”.

## Tekst „Wnioski” (do Canvy)
Eksperymenty kontrolne pokazują, że rola biologicznego okablowania zależy od zadania. W śledzeniu obiektu kluczowy jest podział połączeń na stronę lewą i prawą (38/40 udanych prób wobec 3/40 po przetasowaniu osłabiającym połączenia; przy zachowanej sile połączeń przetasowana sieć również trafiała), natomiast w utrzymaniu chwytu (~90/135; ok. 2,5–3,1% wszystkich komend układu) sieci przetasowane dorównują konektomowi. Mała sieć nogi nie odłożyła obiektu całym ramieniem (0/135), ale większa sieć z danych (3148 neuronów) robi to na poziomie klasycznego sterownika tych samych stawów (94 wobec 93 na 135 prób).

Najmocniejszy wynik: na dotyk „dłoni” robot ma cofnąć ramię, a na dotyk „palców” zacisnąć chwyt. Sieć z konektomu wykonuje oba odruchy w 49 z 77 par scen, a każda z 10 sieci przetasowanych – także z zachowanymi warstwami – istotnie rzadziej (najwyżej 34); potwierdzone dla obu wariantów znaku glutaminianu. Dalej: realistyczny wzrok i testy na fizycznym ramieniu SO-101.

## Podpis pod grafikami (do Canvy)
Od lewej: śledzenie obiektu (trafienia na 40 prób), utrzymanie chwytu (w pudełku na 135 prób; kropki – 13 sieci przetasowanych) i podniesienie całym ramieniem małą siecią nogi (odłożone na 135 prób; A i B – dwa warianty znaku glutaminianu). Tasowanie na pierwszym wykresie osłabiało połączenia. Dane: MaleCNS v1.0 (Janelia), MuJoCo. Dużą część kodu napisały narzędzia AI (Claude Code) według moich poleceń; kierunek, hipotezy i decyzje są moje.

## Zastrzeżenia do liczb na plakacie
- **94 wobec 93 (wariant B znaku):**
  - limit fazy podnoszenia wynosił 10 s;
  - wariant A daje 86 wobec 86;
  - przy limicie 3 s wariant A nie przeszedł (r1).
- **„Dwa odruchy”, 49/77 (wariant B):**
  - wariant A daje 22/77, a tasowania F i L najwyżej 1;
  - nie wygrywa z tasowaniami, które zachowują także podział na nogi.

## v15 (16 XI 2026, 18:41): poprawka nazwiska
- Adam poprawił nazwisko: **Oliwier Szypczyn**, a nie „Szewczyn”, jak było w v13 i v14.
- **Plik:** `~/Downloads/FlyMind_plakat_v15.pdf`. Ma wszystkie zmiany z v14 i do tego poprawione nazwisko w nagłówku: Arial Bold, ten sam rozmiar i położenie co oryginał.
- **Uwaga:** jak wyżej, stare nazwisko zostaje w pliku jako ukryty tekst pod łatką. W druku go nie widać, ale przy kopiowaniu tekstu z PDF może się pojawić. Trzeba je poprawić także w Canvie.
