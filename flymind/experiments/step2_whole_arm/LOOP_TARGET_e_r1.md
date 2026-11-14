# Cel pętli dla stawu (e) wrist_roll — wersja r1 (spisana 2026-11-13, PRZED pierwszą iteracją stawu e; hash w logu)

**Słaba analogia, znak arbitralny** (tabela C r1, decyzja Adama): staw 4: POS = Tr flexor MN (8, T1 L), NEG = Tr extensor (2) +
Sternotrochanter (2) + Tergotr. (4) MN (T1 L), s₄ = +1 ustalony w `CALIBRATION_k_SIGNS.md` (bez zmian). Para antagonistów
zgięcie/prostowanie krętarza — VERIFIED (Lesser, preprint); ruch zawiasowy → obrót nadgarstka = [ANALOGIA] słaba.
Kod: `joint_net.py --roll` (bez `--joints`). Analiza: `analyze_joint.py DIR GLU --outcome placed --no-reflex`.

## 1. Zadanie (inne niż b–d, bo obrót nadgarstka nie podnosi: Δpoz ≤ 0,4 mm / 0,05 rad — CALIBRATION §3)
Staw 4 jest sterowany siecią **od zaciśnięcia szczęki do zwolnienia przedmiotu** (fazy: podniesienie, transport, odkładanie):
`cel₄ = q₄(poza chwytu) + Σ (+1 · 0,005 · 0,01 · (r_Tr_flexor − r_Tr_ext))`. Stawy 0–3 jak w rusztowaniu (IK: `P["lift"]`,
transport). Po zwolnieniu staw 4 wraca do rusztowania. Zadanie stawu = **utrzymać chwyt i umieszczenie mimo tego, że obrót
nadgarstka wykonuje sieć**. Mucha nie ma tu informacji o celu obrotu; to test „czy sieć steruje stawem bez psucia zadania”.
Wynik główny: **`placed`/135** (cały cykl; obrót może przeszkodzić w transporcie i odłożeniu). Pomocniczo: `lift`, maks.
odchylenie |q₄ − q₄(chwyt)| na próbę (`roll_dev`), udział komend `snn:legT1L` w stawie 4.

## 2. Wejścia iteracji 1 (z góry) — jak (c)/(d) it1: `padsT2` + `padsT1`, interneurony regułą `fl`.
Przewidywanie [HYPOTHESIS, receptor_screen_groups_v1.json]: pule krętarza dostają ≤ 4 Hz nawet przy pobudzeniu WSZYSTKICH
receptorów T1 L 40 mV; przy samym dotyku stopy ≤ 1 Hz → |Δq₄| rzędu 0,005 rad/s → sieć praktycznie trzyma staw. Wtedy wynik
„niegorszy od K” będzie trywialny i **nie dowodzi sterowania** — tak zostanie opisany.

## 3. Ramiona
N, S1–S5 (tasowania), **R = trzymanie q₄ z pozy chwytu (Δ = 0) — trywialny „odruch” zdefiniowany TERAZ**, K = rusztowanie
klasyczne (q₄ z IK, jak benchmark), K0.

## 4. Odniesienia (VERIFIED, pliki): K (trening b, seed 20101): placed 30/45 (Glu −1), 31/45 (Glu +1); K seed 100: placed 90/90
z 135 (B_fly_search Glu ∓1); K0 placed 93/135.

## 5. Cel (test, raz; każdy Glu osobno)
C1 niegorszość `placed` wobec K (dolna granica 95 % bootstrapu ≥ −0,10); **C2 nie dotyczy** (R = „nic nie rób”; zadanie nie wymaga
ruchu stawu 4 — porównanie N vs R jest raportowane bez progu); C3 N > S1–S5 (McNemar z Holmem) na `placed`; C4 ≤ 5 N, bezpiecznik
≤ 10 % taktów aktywnych. Dodatkowo raportowane (bez progu): roll_dev N vs S — czy sieć z danych w ogóle porusza staw.

## 6. Ziarna (SEED_REGISTRY.md): trening `--seed 20701` × 45, tasowania 20 710 001–002; test `--seed 20801` × 135,
tasowania 20 810 001–005.

## 7. Iteracje i koniec pętli — jak (c) r1 §7.
