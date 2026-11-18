# Sprawa 2 — „dawka dotyku → siła zacisku” (cel zapisany PRZED testem, 16 XI 2026)

## Po co
Dotąd schemat połączeń wygrał tylko na „które czucie → który ruch” (wybiórczość noga→noga, odruchy). Ten test pyta
o liczby: czy sieć z danych **dozuje** siłę szczęki stosownie do siły dotyku lepiej niż sieci o przetasowanych połączeniach.

## Pochodzenie hipotezy (eksploracja, uczciwie)
`explore_dose.py` → `results/step3_20261115/explore_dose_g±1_v1.json` (tasowania eksploracyjne 21 100 001–003 F,
21 100 006–008 L i G). Moment przy pełnym dotyku (40 mV = 1 N): dane 0,90 (Glu +1) i 0,62 N·m (Glu −1); 18 tasowań
eksploracyjnych najwyżej 0,898 (G8, Glu +1 — prawie remis z danymi 0,903) i 0,38 N·m (G7, Glu −1); bez rodziny G:
0,65 i 0,26. Krzywa danych rośnie stopniowo (próg ok. 7,5 mV). Przy Glu +1 rodzina G może więc wygrać — zapisuję to z góry.
**Stopniowość sama nie odróżnia** danych od tasowań warstwowych (L6, L7, G7 przy Glu +1 też rosną płynnie) — dlatego nie
jest kryterium. Uwaga: z H-cisza wiadomo, że sieć z danych jest ogólnie AKTYWNIEJSZA niż tasowania, więc większy moment
mógłby wynikać z samej „głośności”. Dlatego drugie kryterium to wzajemność mięśni (normalizowana na aktywność), której
w eksploracji NIE mierzyłem i nie oglądałem.

## Miara (bez robota, szum 0, sieć „pre” 3148 neuronów, `dose_test.py`)
Oba pady → szczecinki nogi T2 L, poziomy 0; 2,5; 5; 7,5; 10; 15; 20; 30; 40 mV (40 mV = 1 N), 1 s; ostatnie 0,5 s.
press = MN Ti extensor T2 L [Hz]; release = MN Ti flexor + Acc. ti flexor T2 L [Hz]; τ = 0,005·(press − release) N·m
(dokładnie jak moment szczęki w `reflex.py`).
- **τ40** — moment przy pełnym dotyku (ile zacisku daje sieć).
- **rec40** = (press − release)/(press + release) przy 40 mV — wzajemność: 1 = pracuje tylko zaciskacz, 0 = oba mięśnie
  naraz (siła marnowana na współskurcz), −1 = tylko rozwieracz. Nie zależy od ogólnej głośności sieci.
- ρ — Spearman (poziom, τ), tylko opisowo i jako warunek wstępny.

## Kontrole (po 20 NOWYCH tasowań na rodzinę i na znak Glu)
F (swobodne, równa waga) 21 910 001–020; L (zachowujące warstwy S/I/M) 21 920 001–020; G (warstwy + przynależność
receptorów i MN do nóg, jak w `spec_test.py`) 21 930 001–020.

## Kryteria (osobno dla Glu +1 i Glu −1)
- Warunek wstępny P: w danych ρ ≥ 0,9 i τ40 ≥ 0,10 N·m (krzywa jest prawdziwym dozowaniem i sięga progu „zaciska”).
- H-S(rodzina): τ40 danych > τ40 każdego z 20 tasowań (p = 1/21 ≈ 0,048).
- H-Rec(rodzina): rec40 danych > rec40 każdego z 20 tasowań.
- H-D(rodzina) = H-S i H-Rec.
- **„Schemat połączeń ma znaczenie dla dozowania siły zacisku (w modelu)”** — gdy P oraz H-D(F) i H-D(L) dla OBU Glu.
  H-D(G) rozstrzyga poziom (dobór konkretnych neuronów vs tylko „która grupa z którą”).
- Opisowo: τ40, rec40, ρ — min / mediana / maks rodzin; liczba tasowań ≥ danych.

## Zastrzeżenia zapisane z góry
- Model obwodu, bez robota; nie mówi, że robot lepiej trzyma przedmioty. Jeśli wynik pozytywny, następny krok to próba
  na robocie z kontrolą tasowań od początku (osobny cel).
- Oczekiwanie: H-S raczej spełnione (eksploracja), H-Rec nieznane; Glu −1 i rodzina G mogą przegrać.
- Liczba neuronów ruchowych szczęki jest mała (Ti ext / Ti flex T2 L), więc rec40 może być 1,0 w wielu sieciach —
  wtedy remis = porażka hipotezy (wymagam ostrej przewagi).
- Analiza: `analyze_dose.py KATALOG OUT.json`; uruchamiane raz na `results/step3_20261115/dose/`.
