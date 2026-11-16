# FlyMind, 16 XI 2026: „dwa odruchy” na robocie, test 3× większy (r2)

Wszystko w symulacji MuJoCo, bez robota fizycznego.

Zanim test ruszył, zapisałem:
- cel w `experiments/step3_wiring/LOOP_TARGET_reflex_r2.md`,
- hasze plików w `PRE_TEST_HASHES.txt` (15:36),
- nowe ziarna w rejestrze.

Test uruchomiony raz. Liczby: `audit_log_step3_20261115.md`, wiersze R1–R4. Nic nie zostało zacommitowane.

## Co sprawdzano
Jedna sieć z danych muchy steruje naraz szczęką chwytaka i ramieniem. Musi zrobić dwa różne odruchy:
- dotyk **dłoni**: cofnij ramię i NIE zaciskaj szczęki;
- dotyk **palców**: zaciśnij i trzymaj.

Sukces pary scen = oba odruchy udane.

Porównanie z 15 sieciami o przetasowanych połączeniach (te same neurony, ta sama liczba połączeń):
- F: tasowanie swobodne;
- L: tasowanie zachowujące warstwy (czucie, sieć pośrednia, mięśnie);
- G: tasowanie zachowujące warstwy i nogi.

Test liczono dla obu znaków glutaminianu, bo znak nie jest znany z danych. Scen jest 3× więcej niż w pierwszym teście: 77 ważnych par, wcześniej 24.

## Wynik według reguł zapisanych przed testem: POTWIERDZONE dla obu znaków Glu [VERIFIED, model]

Liczba par z oboma odruchami udanymi, na 77:

| | Glu +1 | Glu −1 |
|---|---|---|
| Sieć z danych | **49** | **22** |
| 5 tasowań swobodnych | 0, 0, 1, 0, 0 | 0, 0, 0, 0, 0 |
| 5 tasowań z warstwami | 34, 15, 3, 8, 26 | 0, 0, 0, 0, 1 |
| 5 tasowań z warstwami i nogami | 43, 31, 34, 9, 14 | 0, 29, 12, 1, 2 |

- Sieć z danych jest istotnie lepsza od każdego z 10 tasowań F i L, przy obu znakach Glu (McNemar z poprawką Holma).
- W pierwszym teście (24 pary) przewaga nad tasowaniami z warstwami była tylko częściowa. Przy 3× większej liczbie scen jest wyraźna.

## Czego ten wynik NIE mówi
- **Nie mówi, że liczy się każdy konkretny neuron.** Z tasowaniami zachowującymi warstwy i nogi sieć z danych nie wygrała z każdym (Glu +1: 4 z 5; Glu −1: 3 z 5). Wygląda na to, że wystarczy zachować, która grupa neuronów łączy się z którą. [VERIFIED, model]
- **Przy Glu −1 sieć z danych robi oba odruchy rzadko** (22 z 77, ok. 29 %). Wygrywa, bo tasowania F i L nie robią ich prawie nigdy. Zapisałem z góry, że tu raczej przegra; wynik jest lepszy od oczekiwań.
- **Nie wykluczono „głośności”.** Sieć z danych jest ogólnie aktywniejsza od tasowań (test dawki). Ten test tego nie rozdziela. [NOT VERIFIED]
- **Wynik pierwszego testu nadal jest niespełniony.** Ten test zaprojektowałem po zobaczeniu tamtego, z nowymi ziarnami i tymi samymi kryteriami.
- **Ograniczenia modelu:** symulacja; neurony uproszczone; „dłoń = noga przednia, palce = noga środkowa” to wybór modelu; odruch cofania sprawdzany na jednym kształcie (walec 60 mm); materiały sztywne.

## Po ludzku
To pierwszy wynik na robocie (w symulacji), w którym schemat połączeń muchy wygrywa nie tylko z całkiem losowym przepięciem, ale też z przepięciem zachowującym warstwy. Wygrywa przy obu wariantach nieznanego znaku i według reguł zapisanych z góry. Dotyczy to wyboru, **który** ruch uruchomić po **którym** dotyku. Siły zacisku (test dawki) nie dotyczy.
