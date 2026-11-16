# Krok 6 r2 — ten sam test z bodźcem o stałym czasie (sonda dłoni), cel zapisany PRZED testem, 16 XI 2026

## Dlaczego r2 (wniosek z porażki r1 — zmiana wybrana PO teście r1, jawnie)
W r1 (`LOOP_TARGET_brainleg_r1.md`, ziarno 21831) Glu −1: 71 % < 80 %; Glu +1: nadgarstek 0/28. Diagnoza na ziarnach
treningowych (`explore_slick.py`, `results/step3_20261115/explore_step6/`):
- ruch trwa tylko tyle co dotyk: kontakt dłoni znika po 1–3 taktach (10–30 ms) na śliskim/ciężkim/twardym walcu, a na
  lekkim trwa całe 0,5 s — i wtedy ruch jest duży;
- przy zamrożonym ramieniu kontakt trwa 50/50 taktów dla każdego materiału → kontakt urywa ruch ramienia (odsunięcie),
  nie przedmiot; tasowania też go urywają nawet ruchem 0,0007 rad, więc „zerwanie kontaktu” nie jest dobrą miarą;
- przy Glu +1 łokieć prostuje się 2× szybciej, kontakt znika po 2–3 taktach i nadgarstek nie zdąży ruszyć.
Wniosek: w r1 mierzyłem długość bodźca, a nie odpowiedź sieci. W r2 bodziec ma stały czas.

## Jedyna zmiana: sonda dłoni (`brainleg_probe.py`)
W próbie W, przez całe sterowanie siecią (0,5 s), przedmiot jest dociskany do dłoni od dołu siłą = ciężar + 3 N
(jak palec szturchający głowę). Sonda to klasyczne otoczenie (bodziec), nie decyzja; o ruchu decyduje sieć. Próby C bez
zmian (sonda wyłączona). Sieć, wejścia (czujnik dłoni → BM, 40 mV/N, maks. 40 mV), k, dt, F_ON 3 N, progi — bez zmian.
Uwaga: czujnik nasyca się przy 1 N, więc z sondą bodziec jest ten sam dla każdego materiału — test mierzy odpowiedź
sieci na dotyk 0,5 s, a nie fizykę chwytu.

## Trening (ziarno 21421, 3 pozy, 9 ważnych par na Glu) — NIE dowód
N: łokieć 9, nadgarstek 9, oba 9, C stoi 9 — oba Glu (łokieć 0,05 rad przy Glu −1, 0,11 przy Glu +1; nadgarstek ~0,07).
F1: łokieć 9 (oba Glu), nadgarstek 0, C stoi 0. L6: łokieć 9 (Glu +1) / 0 (Glu −1), nadgarstek 0, C stoi 0.

## Test
`brainleg_probe.py --seed 21861 --poses 6`, `STEP6B_FINAL_TEST=1`, **raz**. Sieci: N; F1–F5 (21 870 001–005);
L1–L5 (21 880 001–005); oba Glu; 22 przebiegi.

## Kryteria — identyczne jak r1 (`analyze_brainleg.py`, bez zmian kodu)
BL_A łokieć ≥ 80 %, BL_B nadgarstek ≥ 80 %, BL_C oba ≥ 70 %, BL_D C stoi ≥ 95 %; H(F), H(L) na odpowiedzi wybiórczej
(McNemar dokładny + Holm, p < 0,05). Osobno dla każdego Glu.

## Zastrzeżenia z góry
r2 powstało po porażce r1, więc sukces tu nie unieważnia r1: r1 zostaje FAILED. r2 odpowiada na inne pytanie:
„czy przy dotyku o stałym czasie sieć rusza oboma stawami”. Symulacja MuJoCo, bez prawdziwego robota.
