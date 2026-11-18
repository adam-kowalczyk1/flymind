# FJ2: ramię SO-101 sterowane przez muchę (projekt, 2026-11-03; nic nie uruchomiono)

**Cel:** ruchem ramienia decyduje sieć z danych (`vision_leg.py`, 5643 neurony).

**Wejścia** (wyłącznie zmysły; neuronów ruchowych ani przedruchowych nie pobudza się sztucznie):
- obraz → `encoder.py` → LC9 L/R (g_L, g_R, i_max = 12 mV), tak jak dla LC10a w `loop.py`;
- dotyk padów → receptory szczecinkowe (jak FJ1);
- później: kąty stawów → FeCO.

Mucha nie ma ramienia. Każde przypisanie mięśnia nogi do stawu ramienia to **analogia, ustalona przed testem**.
Klasyczny kod zostaje wyłącznie jako niezależna warstwa bezpieczeństwa (`safety.py`: zakresy, prędkość, stół) i jako ramię
porównawcze.

## Mapowanie v1 (lewa środkowa noga T2 L ↔ ramię)

| staw SO-101 | agonista (+) | antagonista (−) | uzasadnienie analogii |
|---|---|---|---|
| shoulder_pan (0) | DNa02 L − R (pętla V5, jak dotąd) | | obrót podstawy = skręt muchy; jedyna część zwalidowana wcześniej |
| shoulder_lift (1) | Pleural remotor/abductor MN | Sternal anterior rotator MN | ruch biodra w przód/tył ↔ wymach ramienia; biodro reaguje na wzrok najmocniej (pilot 6) |
| elbow_flex (2) | Tr flexor MN | Tr extensor MN | krętarz/udo ↔ łokieć |
| wrist_flex (3) | stały (v1) | | goleń jest już przypisana szczęce; brak drugiej pary pul bez konfliktu |
| wrist_roll (4) | stały | | brak odpowiednika |
| gripper (5) | Ti extensor MN (zaciskanie) | Ti flexor + Acc. ti flexor MN | goleń/stopa/pazurek ↔ chwytak; to samo mapowanie co FJ1, ale w tej samej sieci (J0 0,275, nie 0,2 jak w FJ1) |

**Prawo sterowania [MODEL]:** prędkość celu stawu j = k_j · (r_agonista − r_antagonista), przy k_j wspólnym dla stawów 1–3
i ustalonym przed testem. Pule MN są wygładzane wykładniczo, τ = 50 ms, jak w FJ1.

**Parametry ustalone przed jakimkolwiek wynikiem ramienia:**

| parametr | wartość |
|---|---|
| J0 | 0,275 mV/synapsę (Shiu i in. 2024; nie 0,2) |
| Glu | −1 i +1 raportowane osobno |
| szum | 0 |

## Czego się spodziewać (uczciwie)

- Nie wiadomo, czy z tych połączeń wyjdzie ruch w stronę obiektu. Wzorzec może być nieskoordynowany albo za słaby.
- Wtedy wynik brzmi: „mucha steruje, ale ramię nie sięga”. Nie wolno tego maskować dostrajaniem mapowania pod wynik.
- Dostrajanie jest dozwolone tylko w jawnie oznaczonym pilocie. Każda zmiana po pilocie wymaga nowego testu na nowych warunkach (jak FJ1).

## Kolejne kroki

1. **Pilot:** piłeczka w polu widzenia, pomiar ruchu stawów 1–3 i tego, czy chwytak zbliża się do piłeczki.
2. **Protokół FJ2:** ramiona porównawcze
   - sieć z danych;
   - sieć przetasowana;
   - brak wejścia wzrokowego (zasłonięte oko);
   - klasyczne IK jako górna granica.

   Ziarna do zarejestrowania przed startem.
3. **Red team** protokołu, uruchomienie, red team wyników.

**Poprawka 2026-11-03 (przed pilotem):** w v0 projektu Ti flexor/extensor przypisano jednocześnie nadgarstkowi i szczęce — konflikt. Goleń → szczęka, nadgarstek stały.
