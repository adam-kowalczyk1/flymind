# Krok 7 — test konfliktu bodźców (wzrok + dotyk) na sieci wspólnej — plan r1 (spisany PRZED testem; po 2 pilotach bodźca)

Kod: `conflict_test.py` (nowy plik). Sieć: `vision_manipulation.VisJaw` (moduł wspólny, bez zmian) = droga wzrokowa LC10a →
pośrednie → DNa02 ∪ obwód nogi T2 L (podgraf indukowany MaleCNS, 1931 neuronów; krawędzie wzrok → noga: 91, w tym DNa02 L → noga
70, DNa02 R → noga 3 — z raportu sieci w pilocie, VERIFIED). Szczęka = moment z MN goleni tej sieci. Wzrok włączony przez CAŁY czas
(brak ręcznego bramkowania): kamera „eye” na chwytaku → enkoder koloru → LC10a L/R w każdym takcie; szum 2 mV tylko w drodze
wzrokowej (ziarno = 20 990 000 + nr próby, to samo w „on” i „sham”). Ramię: klasyczne rusztowanie, percept-wyrocznia.

## Bodziec (ustalony w pilotach z OBRAZU, nie z zachowania)
- Pilot 1 (`conflict_7/pilot/pilot1_*`, przedmioty zielone jak w etapie wzroku): enkoder nasycony przez trzymany przedmiot
  (g ≈ 1,0 po obu stronach w „on” i ≈ 0,86–1,0 w „sham”) → bodziec prawie nie zmienia wejścia. Odrzucone.
- Pilot 2 (`pilot2_*`, przedmioty w kolorach materiałów): przy cube_S/hard_grip i long/heavy „on” vs „sham”: g (1,00; 0,78) vs
  (0,51; 0,28), DNa02 L/R 164/124 vs 12/0 Hz; przy sphere/light (żółty materiał też pobudza enkoder) różnica mała. Przyjęte.
  Moment szczęki w pilocie: 0,57–0,58 vs 0,57–0,59 N·m (3 próby — bez wniosków; offset bodźca NIE był zmieniany po tym odczycie).
- Bodziec: zielona kula r = 2,5 cm, bez kolizji, 10 cm przed kamerą, 4,5 cm w lewo (układ kamery), od początku fazy podniesienia
  do początku odkładania. Sham: ta sama kula, szara.

## Ramiona i liczba prób
- N (sieć z danych): Glu −1 i Glu +1 × {on, sham} × 135 prób (`--seed 20971 --poses 3`).
- S1–S5 (`block_shuffle` tylko bloku wzrok → noga, ziarna 20 980 001–005): Glu ±1 × {on, sham} × 45 prób (`--poses 1`, czyli
  pierwsza poza tych samych scen) — ograniczenie czasu, ustalone z góry.

## Miary (okno = pierwsze 100 taktów = 1 s od włączenia bodźca, pierwsze okno próby; tylko próby z oknem w obu warunkach)
1. **Główna:** średni moment szczęki z sieci w oknie; efekt = sparowana różnica on − sham.
2. Kontrola manipulacji: średnia częstość DNa02 L w oknie (on − sham) — jeśli nie rośnie istotnie, test jest NIEWAŻNY (bodziec
   nie dotarł do sieci).
3. Pomocnicze (binarne, wszystkie próby): `placed`, utrata chwytu (`snn_released`), McNemar dwustronny.

## Rozstrzygnięcie (każdy Glu osobno)
- „Wzrok zmienia chwyt (bez bramkowania)” = Wilcoxon (znakowanych rang, dwustronny) p < 0,05 dla miary 1 w N **i** 95 % przedział
  bootstrapu (10 000, ziarno 20 999 999) średniej różnicy nie zawiera 0.
- „Efekt swoisty dla połączeń z danych” = powyższe **i** |efekt N| na wspólnych 45 scenach > max |efekt Sᵢ| (i = 1–5).
- Wynik zerowy (brak efektu) raportowany jako wynik: sieć wspólna przy tym bodźcu nie przenosi konfliktu na chwyt.
