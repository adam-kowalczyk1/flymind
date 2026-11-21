# P2 — kopia ruchu ramienia dla oka (21 XI 2026): **formalnie PASS, w praktyce kopia nic nie daje**

Plan: `flymind/experiments/step3_wiring/PREREG_P2_KOPIA.md` (9f5e182, przed testem). Ziarna 24 105 001–010. Mediany (× zbliżanie):

| oko v3 | obrót poz. | obrót pion. | obrót skośny | zbliżanie w obrocie | kamera jedzie na fakturę |
|---|---|---|---|---|---|
| bez kopii | 0,003 | 0,003 | 0,004 | 0,80 | 0,12 |
| kopia nominalna | 0,034 | 0,030 | 0,021 | 0,80 | 0,12 |
| kopia g 0,8, opóźn. 25 ms | 0,025 | 0,025 | 0,014 | 0,85 | 0,12 |
| kopia g 1,2, opóźn. 25 ms | 0,039 | 0,039 | 0,039 | 0,74 | 0,12 |

E1 i E2: 10/10 w każdym warunku (oko v3 i v2). Warunek „kopia coś poprawia o ≥ 0,05” spełniony tylko jednym
przypadkiem: zbliżanie w obrocie przy kopii g 0,8 (0,853 vs 0,801 = +0,052) — na granicy, w warunku z BŁĘDNĄ kopią, a przy
kopii dokładnej zmiany brak. Dlatego wynik formalny PASS, ale uczciwie: **na tych scenach kopia ruchu nie pomaga** — VS/HS
już gasi obrót kamery (0,003), a przesuwanie stanu oka dodaje drobne zakłócenia (0,02–0,04, wciąż daleko pod 0,25).
Mój warunek „poprawia” był napisany za luźno (wystarczył jeden przypadek z jednego warunku).

Kamera jadąca prosto na fakturę: 0,12 (v3) / 0,03 (v2) — gładkie rozszerzanie całego obrazu NIE myli oka. Na prawdziwym
nagraniu (oko_r1) fałszywe sygnały przy pochylaniu pochodziły z BLISKICH kontrastowych przedmiotów (klawiatura, ubranie),
tego te sceny nie odtwarzają.

## Wniosek
Kopia ruchu w tej postaci (sam obrót) nie jest dziś potrzebna oku v3 na scenach syntetycznych. Czy pomoże na prawdziwym
ramieniu, sprawdzi dopiero kamera na ramieniu poruszanym przez muchę (z odczytem stawów) — to wymaga „ruszamy” Adama.
Kod zostaje (`FlyEye._remap`, domyślnie wyłączony: bez `eye.ec` nic się nie zmienia).
