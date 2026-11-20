# Oko bez tłumacza: przeszczep „dynamiki flyvis” na połączenia MaleCNS — plan T0 + T1 (spisany PRZED liczeniem, 20 XI 2026)
Zlecenie Adama 20 XI: „zbuduj oko, z którego mucha odbiera sygnały nie przez tłumacza; badaj, symuluj, nic nie zakładaj”.

## Pytanie
16–17 XI: (1) sam wycinek MaleCNS z jednakowymi parametrami NIE liczy kierunku (G2 FAILED: DSI T4 ≈ 0); (2) flyvis
(Lappalainen i in. 2024, 734 wyuczone liczby: stała czasowa i spoczynek dla 65 typów, siła dla 604 par typów) liczy
kierunek (G2-fv PASS), ale na mapie połączeń samicy (Shinomiya), a most flyvis → LPLC2 MaleCNS zawiódł.
**Hipoteza H1:** to, czego brakowało w (1), to właściwości typów komórek, nie połączenia. Jeśli wstawić do flyvis liczby
synaps z MaleCNS (zamiast samicy) i zostawić wyuczone właściwości typów, T4/T5 nadal liczą kierunek. Wtedy oko od
fotoreceptorów do T4/T5 liczy na mapie MaleCNS i może dalej karmić LPLC2/LC4 MaleCNS swoimi synapsami (krok T2, osobny plan).

## T0 — bramka danych (tylko odczyt)
Prawa strona MaleCNS. Nazwy: jak flyvis; Am→Am1; TmY9→TmY9a+TmY9b; CT1 pomijam (1 komórka na stronę, we flyvis 2 przedziały).
Kolumna komórki: `assignedOlHex1/2`, gdy jest; T4 = środek wejść z Mi1; T5 = środek wejść z Tm1/Tm2/Tm4/Tm9 (jak bridge_prep,
VERIFIED 16 XI); pozostałe bez kolumny = środek wejść od komórek z kolumną (ważony synapsami). Układ flyvis: obrót +30°
(`bridge_prep.to_flyvis`, PREREG_BRIDGE.md). Filtr średni: dla (typ pre, typ post, du, dv) średnia liczba synaps po komórkach
post (w promieniu 12 kolumn od środka) **które mają ≥ 1 synapsę z tego przesunięcia** (tak wyglądają wartości flyvis:
ułamki o małych mianownikach); du, dv = kolumna pre − kolumna post (sprawdzane na tabeli flyvis).
**Zamiana:** liczby MaleCNS zastępują liczby flyvis dla każdej pary typów, gdzie oba typy mają w MaleCNS ≥ 50 komórek
z kolumną; inaczej zostaje liczba flyvis („krawędź mieszana”). Fotoreceptory R1–R8 (w MaleCNS prawie brak: 9 komórek R1–R6
po prawej) → ich krawędzie zostają z flyvis. Przesunięcia spoza 2355 kluczy flyvis są pomijane (raportuję, ile masy to jest).
Raport: udział masy synaps MaleCNS, który trafił w klucze; ρ Spearmana sum par (flyvis vs MaleCNS); udział krawędzi mieszanych.
**Bramka T0 (PASS, by iść do T1):** ≥ 60 % par typów flyvis (bez fotoreceptorów) ma odpowiednik w MaleCNS i ρ ≥ 0,5.

## T1 — czy T4/T5 liczą kierunek na liczbach MaleCNS
Modele flyvis flow/0000/000–049 (właściwości typów bez zmian), liczby synaps wg T0. Bodziec: wbudowane w flyvis ruchome
krawędzie ON/OFF (12 kierunków), te same co w bramce G2-fv. Bez szumu (deterministyczne).
**PASS:** w ≥ 30 z 50 modeli mediana DSI T4a–d (ON) ≥ 0,2 i mediana DSI T5a–d (OFF) ≥ 0,2. Tylko raport: kierunki
preferowane vs flyvis, DSI oryginału, kontrola „przesunięcia potasowane w parze typów” (suma pary zachowana).
Jeśli FAILED: zapisuję, niczego nie stroję pod ten test; dalsza droga = osobny plan (np. douczanie na MaleCNS).

## Wynik T0 (20 XI): FAILED — ρ = 0,43 (próg 0,5), pary z odpowiednikiem 90 % (próg 60 %). Plik t0_gate.json.
Diagnoza: miara „suma średnich warunkowych po przesunięciach” zawyża typy szerokopolowe (TmY9→TmY9: flyvis 11, MaleCNS 707,
bo MaleCNS ma setki przesunięć, flyvis kilka). Tylko 30 % masy synaps MaleCNS między tymi parami mieści się w kluczach flyvis.

## T0b — poprawiona miara (spisana PRZED policzeniem)
Dla pary (A → B): średnia po WSZYSTKICH komórkach B w rdzeniu (promień 12) całkowitej liczby synaps od komórek A
(bez warunku, wszystkie przesunięcia). We flyvis to samo z pełnej tabeli krawędzi (komórki B w promieniu 12 od środka).
Raport: ρ Spearmana tych wartości (pary bez fotoreceptorów/CT1/Am); udział masy w kluczach flyvis osobno dla wejść T4a–d i T5a–d.
Bramka T0b: ρ ≥ 0,5. **T1 liczę niezależnie od wyniku T0b** (jest tani); jeśli T0b FAILED, T1 jest oznaczony jako eksploracyjny.
