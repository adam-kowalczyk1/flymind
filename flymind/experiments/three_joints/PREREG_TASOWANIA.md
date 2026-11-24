# Trzy stawy — kontrola na sieciach potasowanych (24 XI 2026, zapisane PRZED pierwszym przebiegiem na tasowaniu)

**Pytanie:** czy różnica ruchu barku i łokcia między palcem 1 a palcem 2 (Glu −1) wynika z tego, KTO Z KIM jest połączony w danych muchy?
Uwaga: wynik sieci z danych był znany przed wyborem tych miar (bark 2,0° tylko przy palcu 2; łokieć 2,3° / 1,1°). Miary nie są ślepe.

## Niezmienione względem PREREG_THREE_JOINTS.md
Glu −1, te same grupy receptorów (A0: 230, A1: 92, bodyId), bodźce (spokój / palec 1 / palec 2, 3 N przez 2 s), poza, wzmocnienie k = 0,005,
J0 = 0,2 mV, szum 2 mV i ziarna szumu 27 301 001–010, MuJoCo + SafetyLayer, czasy. NIE wyrównuję aktywności tasowań (g = 1).
Sieć z danych liczona ponownie (pomiar aktywności): kąty muszą być identyczne co do bitu z pierwszą próbą.

## Tasowania (podwójne zamiany krawędzi o tej samej wadze ze znakiem; zachowane stopnie, siły we/wy, znak neuronu; 5 zamian na krawędź)
- **F** swobodne (10; ziarna 27 310 001–010)
- **L** zachowuje warstwy: receptory / interneurony z mózgiem / neurony ruchowe (10; 27 320 001–010)
- **LS** zachowuje warstwę i stronę: klasa neuronu (superclass MaleCNS) × strona L/R/U — **rodzina główna** (20; 27 330 001–020)
- **LSN** = LS + rozdzielone nogi: receptory T1 / T2 / inne, neurony ruchowe T1 / inne (10; 27 340 001–010)
Implementacja: `shuffles.py:shuffle_edges` (wektorowa wersja reguły `side_shuffle.shuffle_within_side`), sprawdzana `side_shuffle.properties`.

## Miary (m_c = zmiana kąta 3–5 s przy palcu c minus spokój, to samo ziarno; d = m_1 − m_2; składowe bark i łokieć)
- D: mediana d po 10 ziarnach (bark, łokieć), min…max, liczba ziaren jednego znaku.
- **Rozróżnia palce:** w barku lub łokciu dokładny test zmiany znaku (Holm, 2 stawy) p < 0,05, ≥ 9/10 ziaren jednego znaku, |mediana| ≥ 0,02 rad.
- A_c = √max(0, śr. po parach różnych ziaren m_c(s)·m_c(s′)); S = to samo z d (wielkość powtarzalnej różnicy, bez zawyżania szumem).
- **SI = S / (A_1 + A_2)** — różnica między palcami względem wielkości ruchu (0 = ten sam ruch, 1 = zupełnie inny). MIARA GŁÓWNA.
- **Zareagowała ruchem:** A_1 lub A_2 ≥ 0,005 rad. Inaczej „nie reaguje”, SI nieokreślone.
- Napad: po zwolnieniu (5–8 s, minus spokój) ruch barku lub łokcia ≥ 50 % ruchu z okna nacisku i ≥ 0,02 rad. Ruch własny: w spokoju ≥ 0,005 rad.
- Aktywność: średnia Hz i odsetek aktywnych neuronów (cała sieć, część rdzeniowa, mózg), receptory, neurony ruchowe T1 L, 6 pul stawów;
  okna: spokój 3–5 s, nacisk 3–5 s, po nacisku 5–8 s. Flagi SafetyLayer i strażnik.
- Ten sam wzór co dane (opis): |bark m_2| ≥ 0,02, |bark m_1| < 0,01, łokieć m_1 < łokieć m_2 ≤ −0,01 (mediany).

## Decyzja
Rodzina LS: p_SI = (1 + liczba tasowań z SI ≥ SI_danych) / 21. „Dane wyróżniają się” tylko gdy p_SI ≤ 0,05 ORAZ co najmniej 15/20 tasowań zareagowało
ruchem. Mniej reagujących → „nierozstrzygnięte: kontrola milczy”. Wtórnie to samo dla S (wielkość bezwzględna) i dla pozostałych rodzin (opis; 10 tasowań
nie może dać p < 0,09). Gdy wiele tasowań też rozróżnia palce → mówimy wprost, że rozróżnianie nie jest swoiste dla danych.

## Czego nie wolno
Zmieniać miar, rodzin ani liczby tasowań po zobaczeniu wyników; pomijać sieci. Próba dymna: szum 27 309 001, tasowanie 27 349 001.
