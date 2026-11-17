# LOOP_TARGET — W2b „czy LC4 działa w modelach flyvis, w których T2 zachowuje się jak u muchy” (zapisane PRZED testem, 17 XI 2026)

Polecenie Adama po raporcie W2 (17 XI): „dalej kroki i badaj”. Druga sesja zakończyła B1b (FAILED) i stoi.

## Skąd hipoteza (eksploracja, ujawniona)
W2 (modele 000–009) = FAILED: LC4 z modelu reaguje na „jaśnieje”, nie na „zbliża się”; winny typ T2 (największe wejście LC4).
Literatura: u muchy T2/T3 odpowiadają **i na rozjaśnienie, i na ściemnienie** (Keleş i in. 2020, Cell Reports — REPORTED z wyszukiwania, pełnego tekstu nie czytałem).
Eksploracja na modelach 000–009 (`t2_flash.py`, plik `w2b/t2_flash_explore_000-009.json`): wskaźnik biegunowości T2
P = (ON − OFF)/(ON + OFF) dla plamki r = 2 kolumny. P = +1 w większości modeli (tylko rozjaśnienie); wyjątki: model 003 (P = +0,01)
i 001 (P = −0,62). Model 003 jako jedyny wygrywa zbliżaniem dla obu dysków (7/7 i 7/7); 001 tylko dla ciemnego; reszta tylko dla jasnego.
Zależność P ↔ (LI ciemny − LI jasny) na tych 10 modelach: ρ Spearmana = −0,61. Progi poniżej wybrałem, znając te liczby.

## Pytania
- **H-T2 (mechanizm):** biegunowość T2 w modelu przewiduje, dla którego dysku LC4 „widzi” zbliżanie.
- **W2b (praktyczne):** w modelach, w których T2 jest zrównoważony (jak w literaturze), LC4 policzony z synaps MaleCNS woli zbliżanie
  od oddalania i przesuwania **dla ciemnego i dla jasnego dysku**.

## Test — modele flyvis `flow/0000/010–049` (40 modeli; wyników LC4 dla nich nie oglądałem*)
\* Model 040 był próbą dymną potoku W2 (sprawdzone tylko kształty/NaN). Modeli 010–019 użyła druga sesja do LPLC2 (B1b), nie do LC4.
- Wybór modeli **niezależny od LC4**: `t2_flash.py 10-49` → P każdego modelu. „Zrównoważony” = |P| ≤ 1/3 (słabsza odpowiedź ≥ połowa silniejszej).
- LC4: kod, mapa, bodźce i odczyt **identyczne jak W2** (`w2_run.py discs`, `map_LC4.npz`, sumy w `PRE_W2b_HASHES.txt`). LI i „wygrana” jak w W2.
- Ocena: `w2b_analysis.py` (sprawdzona na sucho na modelach 000–009).

## Kryteria
- **H-T2 PASS:** ρ Spearmana między P a (mediana LI ciemny − mediana LI jasny) po 40 modelach ≤ −0,5.
- **W2b PASS:** co najmniej 3 modele zrównoważone, a w nich (przypadki = modele × 7 środków) dla ciemnego **i** jasnego dysku:
  mediana LI > 0 oraz zbliżanie wygrywa w ≥ 80 % przypadków (te same progi co W2/B1).
  Mniej niż 3 modele zrównoważone → **NOT TESTABLE** (nie zmieniam progu P po fakcie).
- Opisowo: miejsce układu prawdziwego wśród 24 permutacji typów; odsetek wygranych w modelach niezrównoważonych;
  sceny z kamery robota (K-D z W2) dla modeli zrównoważonych.

## Przewidywanie
H-T2: raczej PASS. W2b: niepewne — w modelu 003 przewaga zbliżania była mała (LI +0,05 i +0,11), a zrównoważonych modeli może być za mało
(1 na 10 w eksploracji → spodziewam się ok. 4 na 40).

## Co z wyniku wolno wnioskować
- W2b PASS → wolno napisać: „w modelach flyvis zgodnych z muchą co do T2 detektor LC4 z połączeń MaleCNS rozróżnia zbliżanie”.
  Wtedy piszę osobny cel W3 (pętla z ramieniem) **tylko na modelach zrównoważonych**, z jawną regułą wyboru modeli.
- W2b FAILED lub NOT TESTABLE → linia LC4 zamknięta na tym odczycie; bez strojenia; raport.
- To nadal przewidywanie modelu, nie pomiar muchy. Wybór modeli po zgodności z literaturą jest założeniem — nazywam je wprost.

## Zasady
Jeden przebieg. Najwyżej 3 procesy. Po wyniku nie zmieniam progów, bodźców ani odczytu. Bez ziaren poza permutacjami 23 505 001–023 (te same co W2).
Wyniki: `flymind/results/fly_eye_20261117/w2b/` (`t2_flash_010-049.json`, `discs_*.npz`, `cam_*.npz`, `w2b_result.json`).
