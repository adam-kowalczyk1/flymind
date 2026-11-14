# Weryfikacja: inwestorzy_rynek.md (2026-11-12)

Metoda: ponowne otwarcie źródeł (WebFetch stron pierwotnych) i plików repo. Oryginalnej notatki nie edytowałem. Nic nie uruchamiałem.

## POPRAWKI OBOWIAZKOWE (autor raportu musi je wprowadzic)

1. **Larry Page**: notatka pisze, że w seedzie Eon uczestniczy family office Larry'ego Page'a i oznacza zakres jako VERIFIED na podstawie substacka Untapped Ventures. Substack Page'a NIE wymienia. Usunac lub oznaczyc jako REPORTED/niepotwierdzone (Seedtable zwrocil 403, nie sprawdzilem).
2. **Prophesee, upadlosc**: notatka: "wniosek o upadlosc w styczniu 2025". Zrodlo (Image Sensors World, wpis z 29 I 2025): wniosek zlozony w pazdzierniku 2024, postepowanie naprawcze od konca 2024; styczen 2025 to data wpisu bloga. Dodatkowo CEO wg zrodla to Luca Verre; "nowy CEO Jean Ferre" NIE zostal potwierdzony (REPORTED/UNVERIFIABLE).
3. **Krytyka Eon ("hard-wired, bez uczenia i pamieci")**: The Register (16 III 2026) tego nie pisze. Pisze: Steve Furber: "machine learning, clamped into the shape of a fly connectome", stan spoczynkowy 0 Hz, proste wejscia zamiast wirtualnych zmyslow; demo prawdopodobnie nie w czasie rzeczywistym; o finansowaniu nic. Przepisac krytyke na te slowa; sformulowanie "hard-wired" pochodzi z innego zrodla (Mindplex, nie sprawdzone).
4. **"Dane projektu VERIFIED w briefie"**: §4 nazywa liczby VERIFIED, a w Gaps przyznaje, że nie otwieral wynikow. Sprzeczne. Poprawna etykieta w tej notatce: REPORTED (z briefu); ja zweryfikowalem w repo (patrz tabela) wiekszosc liczb.
5. **Benchmark SO-101 (arXiv 2606.08881)**: abstrakt nie podaje liczb. Pelny tekst czytal subagent wg flymind/reports/fly_vs_vla_research_20261111.md l.223-225: pi0.5 56,25 %, Wall-X 51,25 %, ACT 33,75 %, SmolVLA 32,5 % (4 zadania, 100 demonstracji, 20 prob/komorke). Podawac jako "srednia z 4 zadan, tylko symulacja? NIE: benchmark autorow, nie nasz" i oznaczyc REPORTED; "56%" to zaokraglenie 56,25.
6. **ISEF 2027**: Youth Science Canada podaje tylko daty 8-14 V 2027, Los Angeles; NIE podaje terminu 12 IV, wieku ani limitu zespolu 3 osob (te z innych zrodel, nie sprawdzone). "zespoly do 3 osob" i "<20 lat" = UNVERIFIABLE. Uwaga: "8 czlonkow" na stronie dotyczy druzyny Kanady.
7. **Innatera 15 mln EUR EIC**: zrodlo mowi EIC Accelerator (granty + kapital), strona datowana 23.09.2023 (data niepewna). Notatka mowi "data/szczegoly niepotwierdzone" - zostawic, ale doprecyzowac: EIC Accelerator, 2023. Nie mieszac z "Series A 21 mln USD 2024".
8. **Mind Robotics**: zrodlo: 400 mln USD (13 V 2026, Kleiner Perkins, lacznie ponad 1 mld USD), nie "400-500 mln". Poprawic.
9. **EIC Pathfinder Open 2026**: Zabala potwierdza 12 V 2026, 166 mln EUR, do 4 mln EUR. "2 103 wnioski" - Zabala tego NIE podaje (inne zrodlo, UNVERIFIABLE); "3-4 mln" - zrodlo mowi "do 4 mln".
10. **Przewaga/nowosc (OVERCLAIM ryzyko)**: §4 pkt 4 "Co nowego: otwarte kontrole negatywne + protokol zatwierdzony przed wynikami" - czesc protokolow byla zatwierdzana, ale nie wszystkie (wg MEMORY: strength-matching shuffli NOT VERIFIED w V5). Nie pisac "wszystkie kontrole". Dodatkowo §4 pkt 2 "chwyt dotykowy 90/135-klasy" jest niezrozumiale: poprawnie "chwyt: siec 90/135 (miekki kontakt), klasyczny 93/135; sztywny: 84 vs 101".
11. **V5 38/40**: wynik to petla z kodera koloru (sztuczne pobudzanie, decyzja Adama 12 XI); w pitchu nie pisac "wizja muchy". Notatka to robi poprawnie w §2/§4 - zachowac. Zmienic "wzrok - okablowanie specyficzne" na "w pętli z koderem koloru, nie 'mucha widzi'"; P-regulator byl precyzyjniejszy (40/40, blad 0,16 st. vs 1,41 st.).

## Tabela

| # | Twierdzenie | Werdykt | Poprawna wartosc / sformulowanie | Zrodlo sprawdzone |
|---|---|---|---|---|
| 1 | Prophesee: 20 mln EUR, 15 VI 2026, lider Critical Path Ventures, produkt Mantara, brak nazwanych klientow/przychodow | CONFIRMED | Komunikat nazywa partnerow (IDS, Exosens MoU), nie klientow; brak przychodow. "Wiekszosc udzialowcow francuska" - nie sprawdzalem tego zdania | prophesee.ai/2026/06/15/... (WebFetch) |
| 2 | Prophesee: upadlosc "w styczniu 2025", CEO Jean Ferre | WRONG (data) / UNVERIFIABLE (CEO) | Wniosek X 2024, postepowanie naprawcze koniec 2024, lacznie zebrane 126 mln EUR; CEO Luca Verre (wg bloga) | image-sensors-world 2025/01 (WebFetch) |
| 3 | Eon: seed 3,5 mln USD, 30 XII 2025, lider Protocol Labs, Andregg/Song/Shiu | CONFIRMED | cel "complete mouse brain emulation within two years" | untappedventures.substack.com (WebFetch) |
| 4 | Eon: family office Larry'ego Page'a | UNVERIFIABLE | Brak w substacku; Seedtable 403 | j.w. |
| 5 | Eon: demo chodzenie/czyszczenie/jedzenie, ciało w MuJoCo | CONFIRMED (czesciowo) | NeuroMechFly v2 + MuJoCo, demo: chodzi, czyści czułki, wysuwa trąbkę na sygnał "zapachu cukru"; "jedzenie" -> wysuniecie trabki | theregister.com 2026/03/16 (WebFetch) |
| 6 | Krytycy: "hard-wired, bez uczenia i pamieci" | WRONG (przypisanie) | Furber: "ML clamped into fly connectome", 0 Hz, proste wejscia | j.w. |
| 7 | Mind Robotics 400-500 mln USD 2026 | WRONG | 400 mln USD, 13 V 2026, Kleiner Perkins | therobotreport.com (WebFetch) |
| 8 | Innatera 15 mln EUR EIC | CONFIRMED (kwota), data niepewna | EIC Accelerator, strona z data 23.09.23 | innatera.com press release (WebFetch) |
| 9 | EIC Pathfinder Open 2026: 12 V 2026, 166 mln EUR | CONFIRMED | do 4 mln EUR; "2 103 wnioski" UNVERIFIABLE | zabala.eu (WebFetch) |
| 10 | ISEF 2027: 8-14 V 2027, Los Angeles | CONFIRMED | wiek <20, zespoly do 3, termin 12 IV: UNVERIFIABLE | youthscience.ca (WebFetch) |
| 11 | Regulamin EUCYS PL/Odkrycia (daty cyklu 2025/26, Kiel 22-27 IX 2026, KFnrD->ZDOLNI) | UNVERIFIABLE | PDF nieczytelne dla autora; nie otwieralem | brak |
| 12 | Opteran/SynSense/ABR/BrainChip kwoty; Sky9 pre-seed 250 tys.-2 mln | UNVERIFIABLE | autor sam oznaczyl REPORTED, niespojne; ja nie otwieralem | - |
| 13 | SO-101 benchmark pi0.5 56%, SmolVLA 32,5% (2606.08881) | CONFIRMED wg repo, abstrakt bez liczb | 56,25 / 32,5; odczyt pelnego tekstu przez subagenta - REPORTED | fly_vs_vla_research_20261111.md l.223-225; arxiv.org/abs/2606.08881 |
| 14 | Chwyt T2L 135 prob: miekki klasyczny 93 / siec 90; sztywny 101/84 | CONFIRMED | przeliczone z surowych plikow; miekki: p=0,70 (brak roznicy); sztywny: p=0,001 na korzysc klasycznego | flymind/reports/bio_advantage_research_20261110.md §2.3 |
| 15 | 10 tasowan 101,82,80,102,83,79,82,79,99,4 vs 90 | CONFIRMED | dokladnie te; siec 4. z 11, mediana tasowan 82. Strength-matching tych 10 tasowan: raport mowi "przed wynikami", ale dla V5 NOT VERIFIED - nie mieszac | j.w. l.92 |
| 16 | Wizja+dotyk klasyczny 98, siec 86 | CONFIRMED | A_cam 98 (klasyczny), E 86; integracja bez zysku (5/4, 3/3, p=1,0) | j.w. |
| 17 | V5: siec 38/40, tasowane 3/40, lustro 0/40, P 40/40 | CONFIRMED | przeliczone z 240 surowych prob; mediana bledu 1,41 st. vs 0,16 st.; z opoznieniem obrazu 50 ms 17/40 | fly_vs_vla_research_20261111.md l.104 |
| 18 | Mediana czasu obliczen 1,29 ms | CONFIRMED (z zastrzezeniem) | 1,2924 ms mediana, p95 1,3327 ms; czas obliczen modelu na laptopie, nie opoznienie na ramieniu i nie energia | research_notes/.../projekt_fakty.md l.40 (odsyla do latency_v1_stdout.txt; pliku nie otwieralem) |
| 19 | 1931 z 165 122 neuronow (1,2 %), wzrok 54 % | CONFIRMED | 1931/165122 = 1,17 % | flymind/reports/fly_learning_research_20261112.md l.104 |

## Przeglad uczciwosci
- Notatka nie twierdzi, ze siec bije klasyke, ani ze dziala na sprzecie; zakazy w §4 sa poprawne. Ryzyko: sformulowania "chwyt 90/135-klasy" i "wzrok - specyficzne" (patrz 10, 11).
- Wnioski o rynku (nie ma VC dla projektu, Eon vs FlyMind) sa INFERRED i tak oznaczone; brak zawyzania rynku.
- Etykieta VERIFIED przy Eon i przy "dane projektu" jest zawyzona (poprawki 1, 4).
