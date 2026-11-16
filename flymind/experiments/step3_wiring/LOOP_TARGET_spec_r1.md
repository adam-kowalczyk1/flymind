# Krok 3b — wybiórczość „która noga dotknięta → która noga odpowiada” (cel zapisany PRZED uruchomieniem, 15 XI 2026)

## Pochodzenie hipotezy (eksploracja, uczciwie)
`explore_specificity.py` na 10 tasowaniach eksploracyjnych (21 100 001–010): wskaźnik W sieci z danych 0,868 (Glu +1)
i 0,913 (Glu −1); tasowania swobodne i zachowujące warstwy od −0,31 do +0,24. Hipoteza powstała po zobaczeniu tych liczb,
dlatego potwierdzam ją na NOWYCH tasowaniach i z dodatkową, ostrzejszą kontrolą, której wyniku nie znam.

## Miara (bez robota, szum 0, sieć „pre”, 3148 neuronów)
Bodziec A: dotyk 1 N tylko na szczecinki nogi środkowej T2 L; bodziec B: tylko na szczecinki nogi przedniej T1 L; 1 s.
Odpowiedź: średnia częstość neuronów ruchowych własnej i drugiej nogi (ostatnie 0,5 s).
Wskaźnik bodźca = (własna − cudza) / (własna + cudza); **W = średnia z A i B** (0 = brak wybiórczości, 1 = pełna).

## Kontrole (po 20 nowych tasowań na rodzinę i na każdy znak Glu)
- F (swobodne, równa waga): ziarna 21 250 001–020.
- L (zachowujące warstwy: receptory / interneurony / neurony ruchowe): 21 260 001–020.
- G (zachowujące warstwy ORAZ przynależność receptorów i neuronów ruchowych do nogi: grupy receptory T2, receptory T1,
  interneurony, MN T2, MN T1): 21 270 001–020. Zachowuje sumy połączeń między każdą parą grup; losuje tylko to, KTÓRE
  konkretne neurony są połączone. Wynik tej rodziny nie był oglądany.

## Kryteria (osobno dla Glu +1 i Glu −1)
- H-W(F), H-W(L), H-W(G): W sieci z danych większe niż W każdego z 20 tasowań rodziny (p = 1/21 ≈ 0,048 na rodzinę).
- „Schemat połączeń ma znaczenie dla tego, które mięśnie odpowiadają na dotyk” uznaję za potwierdzone, gdy H-W(F) i H-W(L)
  są spełnione dla OBU znaków Glu. H-W(G) rozstrzyga, na jakim poziomie: spełnione → liczy się dobór konkretnych
  interneuronów, a nie tylko „która grupa z którą”; niespełnione → wystarcza zachować sumy połączeń między nogami.
- Opisowo: W danych, mediana i zakres W tasowań, odpowiedzi własna/cudza [Hz].

## Zastrzeżenia zapisane z góry
To test na modelu obwodu (neurony ALIF, J0 0,2, bez szumu), bez robota. Nie mówi, że ramię lepiej wykonuje zadanie;
mówi, czy losowe przepięcie połączeń niszczy przypisanie czucia do ruchu. Tasowania F i L nie zachowują przynależności do
nóg — ich porażka jest spodziewana i pokazuje poziom „która noga z którą”; ostrzejszym sprawdzianem jest rodzina G.
