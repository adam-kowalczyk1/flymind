# Neurony muchy (spajki, konektom) + uczenie maszynowe — przegląd z Lacuna (21 XI 2026)

Pytanie: jak połączyć sieć z konektomu MaleCNS z uczeniem, żeby nadal decydowała mucha, i w jakich zadaniach prawdziwe
połączenia mogą wygrać z przemieszanymi (u nas po uczeniu: prawdziwe ≈ przemieszane, T2c).

## Najważniejsze znalezione prace
1. **„When Does the Real Wiring Win?”** (arXiv 2611.14508, 10 XI 2026). Trzy sposoby porównania: P1 = parametry dobrane
   pod prawdziwe połączenia i przeniesione na przemieszane (typowa praktyka, **stronnicza**: daje fałszywą przewagę nawet
   między dwoma przemieszaniami — „placebo”); P2 = każda wersja strojona osobno; P3 = osobno, ale tylko w zakresach z pomiarów.
   Wynik: ciała grzybkowate (KC→MBON) — przewaga pod P1/P2 (+0,09) **odwraca się** pod P3 (−0,09); kompas (ring attractor) —
   prawdziwa topologia wygrywa we **wszystkich** protokołach (+0,72); flyvis — P1 „karze” lustrzane odbicie bardziej niż tasowanie.
2. **„Is Newborn Wiring Special?”** (arXiv 2611.01213) — część „przewagi konektomu” to rozmieszczenie wag, nie połączenia;
   proste grafy small-world dorównują mózgowi. Wniosek: kontrole muszą rozdzielać „kto z kim” od „gdzie silne wagi”.
3. **flyGNN** (NeurIPS DBM 2025, OpenReview KFmIRruzvL) — cały konektom FlyWire jako sieć grafowa, uczona naśladowaniem,
   steruje chodem muchy w MuJoCo. **Bez kontroli z przemieszanym grafem** — nie wiadomo, czy to zasługa konektomu.

## Kierunki (od najlepszego dla nas)
| # | Kierunek | Nowość (szybkie sprawdzenie) | Tani test do spisania przed liczeniem |
|---|---|---|---|
| 1 | **Zadanie, w którym topologia musi działać** (jak kompas w pracy 1): kierunek ucieczki zależny od miejsca zbliżania — w MaleCNS LC4→DNp02/DNp11 mają gradient przestrzenny (ρ −0,65/−0,73; Dombrovski 2023). Uczymy tylko odczyt, wejście przestrzenne (nie jedna liczba). | otwarte dla robota z konektomem MaleCNS (nie znalazłem) | uczony tylko odczyt, prawdziwe vs 10 przemieszań, każde strojone osobno (P2): błąd kierunku; przewidywanie: przemieszanie niszczy gradient |
| 2 | **Uczciwe porównanie jako zasada (P2 + placebo)** — dotyczy też naszych wygranych z odruchami dotyku (15–18 XI), gdzie parametry dobierano pod dane (to jest P1!) | metoda istnieje (praca 1), zastosowanie do robota — nowe | powtórzyć test odruchów: przemieszanie A vs przemieszanie B tym samym sposobem; jeśli „placebo” daje przewagę, nasza przewaga jest zawyżona |
| 3 | **Uczenie w ciałach grzybkowatych** (nagroda jak dopamina, zmiana tylko KC→MBON) — robot uczy się „ten przedmiot chwytaj, ten omijaj” | ramię robota + MaleCNS — nie znalazłem; ostrzeżenie z pracy 1: wynik zależy od udziału komórek α′β′ (~44 % z pomiarów) | krzywa uczenia w kilkunastu próbach, prawdziwe vs przemieszane wejścia KC, strojone osobno, z udziałem α′β′ z pomiarów (P3) |
| 4 | **Uczone wejście/wyjście wokół zamrożonej muchy** (jak flyGNN, tłumacz) | zrobione częściowo (flyGNN), ale bez kontroli | 4 ramiona: mucha / przemieszana / BEZ muchy (wejście→wyjście wprost) / graf small-world; jeśli „bez muchy” remisuje — mucha jest ozdobą |

## Wniosek
Uczenie samo z siebie zaciera przewagę prawdziwych połączeń. Szukać zadań, które wymagają struktury (mapy przestrzenne,
pierścienie), porównywać uczciwie (P2/P3 + placebo) i oddzielać „kto z kim” od „wag”. Pilne dla plakatu i pokazu:
sprawdzić naszą przewagę odruchów dotyku testem „placebo” (kierunek 2) — może być zawyżona.
