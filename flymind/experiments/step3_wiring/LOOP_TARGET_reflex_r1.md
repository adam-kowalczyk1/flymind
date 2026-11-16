# Krok 4 — „dwa czucia, dwa odruchy” na robocie (cel zapisany PRZED testem, 15 XI 2026)

## Pytanie
Czy schemat połączeń ma znaczenie w zadaniu dla robota, w którym liczy się, KTÓRE czucie uruchamia KTÓRY ruch?
(Potwierdzenie bez robota: `LOOP_TARGET_spec_r1.md` — wybiórczość noga → noga, dane 0,87 / 0,91, 80 tasowań ≤ 0,12.)

## Układ (kod `reflex.py`; nic nie strojone)
Jedna sieć „pre” (3148 neuronów) steruje naraz szczęką i stawami 1–3. Pady chwytaka → szczecinki nogi środkowej T2 L;
czujnik dłoni → szczecinki nogi przedniej T1 L (40 mV/N, maks. 40 mV). Szczęka: 0,005 N·m/Hz × (prostownik − zginacze goleni
T2); stawy: jak w kroku 2/3 (k = 0,005). Podjazd klasyczny — identyczny dla każdej sieci; potem 2 s sterowania siecią.
- Próba W (wycofanie): otwarty chwytak schodzi nad walcem 60 mm, aż dłoń naciśnie ≥ 1 N. Sukces: po 2 s nacisk dłoni
  < 0,05 N, chwytak nie niżej niż w chwili kontaktu, sieć NIE zacisnęła szczęki (moment ≥ 0,10 N·m krócej niż 10 taktów
  z rzędu), bezpiecznik ≤ 10 % taktów, siła ramię↔blat ≤ 5 N.
- Próba C (chwyt): standardowy dosuw do walca 50 mm, domykanie klasyczne do zaciśnięcia przez sieć (jak w etapie dotyku),
  potem sieć trzyma 2 s. Sukces: na końcu moment sieci ≥ 0,10 N·m, pady dotykają przedmiotu (> 0,05 N), chwytak nie
  obniżył się o więcej niż 2 mm, bezpiecznik ≤ 10 %, siła ≤ 5 N.
- Para scen = (materiał, numer pozy); 5 materiałów × 6 póz = 30 par. Para ważna, gdy oba podjazdy są osiągalne
  (nie zależy od sieci). **Wynik główny pary: OBA odruchy udane.**

## Trening (ziarno 21401, 3 pozy, 13 ważnych par; nic nie zmieniano po jego obejrzeniu)
OBA: N Glu +1 8/13 (W 13, C 8); N Glu −1 2/13 (W 2 — odruch cofania za słaby, C 11).
Tasowania eksploracyjne Glu +1: F 0, 0; L 0, 3; G 2, 8. Glu −1: F 0, 0; L 4, 0; G 6 (drugie w toku w chwili zapisu).
Kryterium W zostaje ostre (< 0,05 N): nacisk dłoni maleje częściowo sam, bez ruchu ramienia (np. 1,55 → 0,84 N przy
sieci, która nie ruszyła żadnym stawem), więc kryterium względne nie odróżniałoby odruchu od biernego osiadania.

## Test
`--seed 21501` (sceny 21 501 000–149), 6 póz, **raz**. Sieci: N; F1–F5 (tasowania swobodne, 21 510 001–005);
L1–L5 (zachowujące warstwy, 21 520 001–005); G1–G5 (warstwy + przynależność do nóg, 21 530 001–005); oba znaki Glu.

## Kryteria (analiza `analyze_reflex.py`, zapisana przed testem)
H-R(F), H-R(L), H-R(G): sieć z danych lepsza na wyniku OBA od każdego z 5 tasowań rodziny (McNemar dokładny + Holm,
p < 0,05, różnica > 0) — osobno dla każdego Glu.
„Schemat połączeń ma znaczenie w zadaniu dla robota” uznaję za potwierdzone dla danego Glu, gdy spełnione są H-R(F) i H-R(L).
H-R(G) mówi, czy wystarcza zachować podział na nogi.

## Oczekiwania zapisane uczciwie
Glu +1: H-R(F) i H-R(L) raczej spełnione; H-R(G) raczej nie (jedno tasowanie G w treningu = dane).
Glu −1: raczej niespełnione — odruch cofania w sieci z danych jest w tym wariancie za słaby (W 2/13).
Ograniczenia: próba W używa jednego kształtu (walec 60 mm) — jedynego w katalogu, na którym dłoń może usiąść; mapowanie
„dłoń = noga przednia, palce = noga środkowa” to wybór modelu; symulacja; jeden zestaw parametrów neuronu.
