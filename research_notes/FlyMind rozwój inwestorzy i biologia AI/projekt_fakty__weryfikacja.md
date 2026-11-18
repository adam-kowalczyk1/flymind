# Weryfikacja: projekt_fakty.md (2026-11-12)

Metoda: ponownie otworzyłem pliki w repo (JSON, stdout, feather przez pandas, git) oraz arXiv API / Crossref / Europe PMC. Nic nie uruchamiałem poza odczytem. Oryginału nie edytowałem.

## 1. Poprawki, które autor raportu MUSI zastosować

1. **Nie pisać „sieć nie wykazała przewagi" jako dowodu, że połączenia nie mają znaczenia ani odwrotnie.** Zostaje wersja z notatek: sieć z danych (90/135) mieści się w zakresie 10 przetasowanych sieci o tej samej sile (79–102, jedno 4/135), więc nie wykazano roli konkretnych połączeń w zadaniu chwytu. (OK, ale patrz p. 2.)
2. **V5 (38/40) trzeba zawsze podawać razem z: „P-regulator 40/40 i dokładniejszy; wejście to heurystyka koloru uznana 12 XI za sztuczne pobudzanie".** Samo „38/40 vs tasowanie 3/40" bez tego jest OVERCLAIM. Dodatkowo kontrola tasowania zachowująca siłę (wg `FLYMIND_MASTER_CONTEXT.md` l. 117: 10/10) pokazuje, że V5 mierzy lateralizację, nie topologię. Tej kontroli nie otworzyłem, więc liczba 10/10 jest tylko REPORTED.
3. **Liczba „340 DAN" nie ma pokrycia w danych.** W adnotacjach: 354 (typy zaczynające się od PPL1/PAM/PPL2/PPM) lub 332 (PPL1+PAM). Pisać „ok. 330–350 neuronów dopaminergicznych (zależnie od definicji)" albo pominąć. Zgadza się z lukami w oryginale.
4. **„Płat wzrokowy ok. 54% neuronów" nie jest potwierdzone.** Mój przelicz: superclass `ol_*` = 95 501 z 166 700 ciał z superclass = 57,3% (58,0% względem 165 122 „Traced"). Pisać „ponad połowa neuronów".
5. **Wynik V5 z opóźnieniem 5 kroków (17/40) pomijany w kontekście** — to ten sam plik i słabszy wynik; przy cytowaniu 38/40 zaznaczyć „opóźnienie 0".
6. **Latencje 1,29 ms i 5,8 ms to czas obliczeń modelu na laptopie**, nie opóźnienie na ramieniu. Uwaga: mediana kamera→komenda w plikach v3 to 10,5–15,5 ms (`A_cam_v3`, `E_vis_touch_v3` stdout), nie 5,8 ms; wartość 5,8 ms nie jest w plikach v3, które otworzyłem (patrz tabela, wiersz 11) — nie cytować bez sprawdzenia `latency_v3.json`.
7. **Benchmark SO-101 (arXiv 2606.08881): liczby pi0.5 56% i SmolVLA 32,5% są UNVERIFIABLE** w abstrakcie. Abstrakt potwierdza tylko, że oceniono π0.5, SmolVLA, Wall-X i ACT na prawdziwym ramieniu i że „silniejsze VLA zwykle biją ACT, ale wynik zależy od zadania". Pisać „REPORTED (tylko abstrakt)" albo nie podawać procentów.
8. **Liczba wpisów `git status` = 148 dziś** (w notatkach 147). Drobne; używać „ok. 150 niezacommitowanych elementów".
9. **Nie pisać „odpornie", „działa" ani „mózg muchy steruje ramieniem" bez kwalifikatora „w symulacji MuJoCo; sieć decyduje tylko o obrocie bazy i sile zacisku; reszta to klasyczne rusztowanie".** To pokrywa się z Q4 oryginału i jest poprawne.

## 2. Tabela weryfikacji

| # | Twierdzenie (z projekt_fakty.md) | Werdykt | Poprawna wartość / sformułowanie | Źródło, które sprawdziłem |
|---|---|---|---|---|
| 1 | Trzy pliki MaleCNS, weights 1 051 241 946 B, annotations 14,5 MB, NT 43 MB, daty 23 X | CONFIRMED | Rozmiary: 1 051 241 946 / 14 483 314 / 43 282 834 B; data 23 X 18:10 | `ls -la data/malecns` |
| 2 | 165 122 prześledzonych ciał (status „Traced") z 166 700 z superclass | CONFIRMED | Kolumna to `status` (nie `statusLabel`): Traced = 165 122; superclass niepuste = 166 700; wierszy w pliku 211 577 | pandas na `body-annotations…feather` |
| 3 | Liczby typów: LC10a 275, DNa02 2, LC9 219, DNp09 2, DNp01 2, LPLC2 185, LC4 126, LPLC1 134, KC 4064, MBON 97 | CONFIRMED | Dokładnie te liczby | pandas, `type` (KC/MBON przez prefiks) |
| 4 | „340 DAN" | UNVERIFIABLE (w praktyce WRONG) | 354 lub 332 zależnie od definicji | pandas, prefiksy PPL1/PAM/PPL2/PPM |
| 5 | Płat wzrokowy ≈ 54% neuronów | WRONG | ok. 57–58% (`ol_*`); pisać „ponad połowa" | pandas, `superclass` |
| 6 | 1931 z 165 122 ≈ 1,2% | CONFIRMED | 1931/165 122 = 1,17%. Uwaga: 1931 = 424 + 1507 pochodzi z dokumentów etapów (REPORTED), nie z mojego ponownego zapytania | arytmetyka; `VISION_MANIPULATION_STAGE.md`, `SENSORY_MANIPULATION_STAGE.md` |
| 7 | Sieć V5: 135 L + 140 P LC10a → 147 pośrednich → 2 DNa02 = 424; dna02_input_total 49 357, z pośrednich 6 022 (~12%) | CONFIRMED | 6022/49357 = 12,2% | `results/v5/v5_confirm_20261028T220223.json`, klucz `network` |
| 8 | V5: sieć z danych 38/40, tasowanie 3/40, zamiana stron 0/40, bez wzroku 0/40, P 40/40 (opóźnienie 0) | CONFIRMED | Dokładnie: snn 38/40, snn_shuffle 3/40, snn_swap 40× False, no_vision 0/40, classical_p 40/40; snn z opóźnieniem 5: 17/40 (80 przebiegów snn). Ziarna 2011–2050. Etykieta „mirrored" w tekście = cond `snn_swap` | to samo JSON, zliczone z `runs[].success` |
| 9 | Chwyt miękki: klasyczny 93, sieć 90 (Glu ±1), sztywny: klasyczny 101, sieć 84 | CONFIRMED (sztywny) / UNVERIFIABLE (miękki) | Sztywny: 101/135 i 84/135 potwierdzone w stdout. Miękki 93 i 90: pliki JSON istnieją, ale ich stdout kończy się samym „zapisano…", wartości nie otworzyłem | `results/contact_audit/stiff_{A,B}_v1_stdout.txt`; `object_handling/B_base_v2.json`, `sensory_manipulation/B_fly_search_glu±1_v1.json` (nie odczytałem pól wyniku) |
| 10 | 10 tasowań z dopasowaną siłą: 101, 82, 80, 102, 83, 79, 82, 79, 99, 4 z 135; sieć z danych 90 | CONFIRMED (tasowania) / UNVERIFIABLE (90) | Tasowania ziarna 17100011–17100020 dają dokładnie te liczby; skala k 1,49–9,05; tasowanie nr 20 (k = 9,05) = 4/135. Plik `shuffle_1.71e+07_v1_stdout.txt` to nieudany przebieg (błąd parsowania ziarna) | `results/shuffle_matched/shuffle_*_v1_stdout.txt` |
| 11 | Wzrok+dotyk: klasyczny 98, sieć 86; sieć sam dotyk 85, z wyłączonym wzrokiem 86, +FeCO 80, sam wzrok 0/135 | CONFIRMED | A_cam 98, E_vis_touch 86, B_cam 85, E_blind_grasp 86, F_vis_touch_feco 80, D_vis 0 (z 135). Wniosek „integracja bez korzyści" zgodny: 86 = 86 | `results/vision_manipulation/*_v3_stdout.txt` |
| 12 | Czas od czujników do komendy: mediana 1,2924 ms, p95 1,3327 ms | CONFIRMED | Pole `sensor_to_command_total`; ta sama wartość co „1,29 ms" | `results/sensory_manipulation/latency_v1_stdout.txt` |
| 13 | Kamera→komenda mediana 5,8 ms, p99 7,6 ms | UNVERIFIABLE | W otwartych plikach v3 `camera_to_command_total` = 8,0 ms (D_vis) do 15,5 ms (E/F); nie znalazłem 5,8. Nie cytować | `A_cam_v3`, `B_cam_v3`, `E_*_v3`, `F_*_v3`, `D_vis_v3` stdout; `latency_v3.json` nieodczytane w całości |
| 14 | Parametry ALIF: v_th −45, τ_m 20, τ_syn 5, t_ref 2,2, τ_a 300 | CONFIRMED (część) | v_th −45, τ_m 20, τ_syn 5, t_ref 2,2, τ_a 300 potwierdzone; v_rest/v_reset/b_a/delay nie sprawdzone. Z kodu: refrakcja kwantyzuje się do 3 kroków, r_max = 250 Hz | `flymind/alif.py` l. 6–42 |
| 15 | Git: 39 commitów, HEAD 664b611 (10 XI) | CONFIRMED | 39 commitów, 664b611 z 10 XI 2026; wymienione commity (da2d43b, ccc19d7, 54155d4, a7344e3) istnieją | `git log`, `git cat-file -t` |
| 16 | Cell, Sept 2026 (MaleCNS) | CONFIRMED | Berg i in., „Sexual dimorphism in the complete Drosophila male central nervous system connectome", Cell, 2026-09-01, DOI 10.1016/j.cell.2026.08.015. Uwaga: Janelia + Google Research jako autorzy nie sprawdzone | Europe PMC (core) |
| 17 | Dombrovski i in. Nature 2023: LC4→DNp02/11 antykorelowane, LPLC2→DNp04 | PARTIALLY CONFIRMED | Praca istnieje: „Synaptic gradients transform object location to action", DOI 10.1038/s41586-022-05562-8 (online 4 I 2023). Szczegóły gradientów nie sprawdzone w pełnym tekście. D0 (R 0,67–0,81; S 0,12 vs 0,025) pochodzi z `fly_vs_vla_research_20261111.md` i pozostaje REPORTED | Crossref + Europe PMC; D0 nieotwarte |
| 18 | Benchmark SO-101 arXiv 2606.08881: pi0.5 56%, SmolVLA 32,5% | UNVERIFIABLE | Artykuł istnieje (7 VI 2026, „Benchmarking VLA Models on SO-101: Failure and Recovery Analysis", π0.5, SmolVLA, Wall-X, ACT na prawdziwym ramieniu); abstrakt nie zawiera procentów | arXiv API |
| 19 | Rdzeń ruchu 47 473 neuronów, 1 155 853 połączeń, 7,1 mln synaps; plan oka nadal tylko na papierze | UNVERIFIABLE (liczby) / CONFIRMED (status) | Liczby są w `fly_eye_plan_20261112.md` l. 30 jako własne zapytanie autora, nie powtarzałem. Status „tylko na papierze" zgodny z l. 3 planu | `reports/fly_eye_plan_20261112.md` |
| 20 | Obwód nogi: 322 szczecinki, FeCO claw 9/14, hook 8/3, MN 2/11 | UNVERIFIABLE | 322 i 9/14/8/3 widoczne w dokumencie etapu (REPORTED), nie w ponownym zapytaniu | `SENSORY_MANIPULATION_STAGE.md` l. 46–48 |
| 21 | Śledzenie przedmiotu: klasyczny gorszy tylko w „loss" (5/20); sieć słabsza w loss 4/20, rotate 14/20, occl_push 15/20 | UNVERIFIABLE | Nie powtórzyłem obliczenia; sformułowanie w oryginale jest niejasne (klasyczny „gorszy tylko w loss", ale podany jest wynik 5/20 bez porównania). Przepisać z nowego odczytu przed użyciem | `results/vision_manipulation/tracking_*_v3.json` (nieodczytane) |
| 22 | P lepszy od SNN w 446/450 parach; P dokładniejszy o 1,2° | UNVERIFIABLE | Zgodne z `FLYMIND_MASTER_CONTEXT.md` l. 117, 122, 136, ale to repo-doc (REPORTED), nie plik danych | `flymind/FLYMIND_MASTER_CONTEXT.md` |
| 23 | Terminy: plakat 16 XI, rejestracja ok. 17 XI, festiwal 1 XII 2026 | UNVERIFIABLE (zewnętrznie) | W repo zgodne (`FLYMIND_MASTER_CONTEXT.md` l. 44–46), ale rejestracja „ok. 17 XI" ma w dokumencie adnotację „zweryfikować u p. Maciejczyka". Regulaminu nie otwierałem | master context |
| 24 | Sprzęt: M1 Max, jedno ramię skalibrowane 1 X, dotyk tylko w symulacji | UNVERIFIABLE | Nie sprawdzam fizycznie; wszystkie wyniki to MuJoCo, brak testu na prawdziwym ramieniu | master context pkt 4 (REPORTED) |

## 3. Overclaimy i zagrożenia dla zasad uczciwości (do pilnowania w raporcie)

- **„Mucha decyduje"**: decyduje tylko o obrocie bazy (V5) i sile zacisku (chwyt). Wszystko inne (dojazd, podniesienie, transport, puszczenie, geometria z kamery) to klasyczne rusztowanie. Nie pisać „sieć muchy steruje ramieniem" bez tej granicy.
- **Brak przewagi sieci**: klasyczny regulator ≥ sieć w każdej porównywanej konfiguracji (93 vs 90, 101 vs 84, 98 vs 86, V5 40/40 vs 38/40). Nie sugerować, że sieć jest lepsza, szybsza ani „bardziej odporna".
- **Przetasowane sieci**: 6 z 10 tasowań dało 79–83/135 (poniżej sieci z danych 90), 3 dały 99–102 (powyżej), 1 dało 4. Rozrzut jest duży, więc to nie jest ani dowód przewagi, ani jej braku; poprawne: „nie wykazano roli konkretnych połączeń".
- **Brak sprzętu**: żadnych wyników na prawdziwym ramieniu i żadnych czujników dotyku poza symulacją.
- **Nowość**: „nie znaleziono opublikowanej sieci z konektomu sterującej ramieniem" to wynik własnego, wcześniejszego przeszukania (REPORTED), nie dowód nieistnienia. Pisać „według naszego przeglądu literatury (stan: listopad 2026)".
- **„Mózg muchy"**: dynamika ALIF jest ogólna (parametry modelowe, nie pomiary tych komórek). Poprawne: „sieć impulsowa zbudowana na połączeniach z konektomu muchy".
- **Etykiety**: w oryginale „VERIFIED" przy stanie testów/commitów jest zasadne; przy obwodzie nogi, D0, V6m3, κ i planach etykieta REPORTED/PROPOSED jest poprawna. Nie awansować ich na VERIFIED.
- **Plany E1/E2, plan oka O0–O6, U1–U5, P1–P7, W3** nie są wykonane ani zatwierdzone do uruchomienia (oprócz samego planu oka na papierze, decyzja 12 XI). Nie pisać o nich w czasie przeszłym.

## 4. Czego nie sprawdziłem

Pól wyników w JSON dla chwytu miękkiego (93/90/83/74/49/82/0), `latency_v3.json`, plików D0, `results/v5_mech_strength/`, serii tracking, reguł konkursu Explory (strona/regulamin), składu autorów w Cell, treści publikacji Dombrovski poza metadanymi, stanu sprzętu.
