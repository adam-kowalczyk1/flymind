# V5 wersja 2 — protokół potwierdzający (zamrożony 2026-10-29, przed przebiegiem)

Status: POTWIERDZAJĄCY, jednorazowy, ziarna **2051–2100** (n = 50, ostatnia pula potwierdzająca). Kod: `flymind/loop_v2.py`
(warianty, zadanie, analiza) + `flymind/loop.py` (`run_trial`, bez zmian zachowania V5 v1 — trajektorie v1 odtwarzane
co do bitu). Hashe kodu: `v5_v2_manifest.json`. Zmiana czegokolwiek po odsłonięciu = nowa wersja.

## Powód (Red Team V4/V5, zweryfikowane)
V5 v1 pokazało, że pętla działa, ale kontrola tasowania nie zachowywała siły wejściowej neuronów; tasowanie
zachowujące siłę dało 10/10 na dev. Pytanie v2: **czy dla zachowania liczy się topologia z danych ponad lateralizację?**

## Zadanie (zmiany wobec v1)
|az0| ~ U(−30°, 30°) (także blisko 0 — „bez wzroku” wygrywa, gdy |az0| < 5°: poziom przypadku), ρ ~ U[0,16; 0,35] m.
Reszta jak v1: poza Q_POSE, 3 s, takt 10 ms, sukces = |e| < 5° we wszystkich taktach 2,5–3,0 s, e z prawdy symulatora
tylko do oceny. Dystraktor (tylko w `*_distr`): zielona kula r 1,25 cm (cel 2,5 cm) po przeciwnej stronie,
|az| ~ U[15°, 30°], ρ ~ U[0,16; 0,35].

## Warunki (te same ziarna, sparowane)
`snn`, `snn_eqshuffle` (siła wej./wyj., znak, stopnie zachowane; ziarno + 100 000), `snn_dnperm` (wejścia DNa02 na losowe
neurony tego samego znaku; siła wejścia DNa02 zachowana; ziarno + 200 000), `toy_relay` (tylko krawędzie modelowe
LC10a → DNa02 ipsilateralnie, n_syn wg reguły z nagłówka `loop_v2.py`; własna kalibracja procedurą V4 v2),
`classical_p`, `no_vision`, `snn_distr`, `p_distr`. Warianty `snn_eqshuffle` i `snn_dnperm` używają dekodera sieci
z danych (logika ablacji: zmieniamy sieć, nie odczyt).

## Hipotezy (α = 0,05/2 = 0,025)
- **H1 (lateralizacja konieczna):** snn > snn_dnperm — dokładny McNemar, jednostronny, p < 0,025.
- **H2 (topologia ponad lateralizację):** snn vs snn_eqshuffle — różnica odsetka sukcesów, sparowany bootstrap 95 % CI
  (ziarno 2202, 10 000). „Równoważne” ⇔ CI ⊂ [−0,15; +0,15]. „Topologia ma znaczenie” ⇔ McNemar dwustronny p < 0,025
  i różnica > 0. W pozostałych przypadkach: nierozstrzygnięte.
- Opis (bez testu): toy_relay − snn, classical_p − snn, no_vision − snn, snn_distr − snn, p_distr − snn_distr
  (różnice odsetków z CI); sukces wg przedziałów ρ [0,16; 0,24), [0,24; 0,30), [0,30; 0,35].

## Przewidywania z eksploracji (zapisane przed przebiegiem, NIE kryteria)
H1 spełniona; H2 „równoważne”; toy_relay ≥ snn; classical_p > snn głównie w przedziale ρ ≥ 0,30 (próg LC10a — na dev
także toy_relay zawodzi przy ρ 0,30, więc martwa strefa pochodzi z progu wejścia, nie z sieci); dystraktor obniża
oba sterowniki (brak selekcji celu).

## Interpretacja ustalona teraz
- H1 ∧ H2 „równoważne” → „w tym zachowaniu sieć z danych działa jak przekaźnik lateralizacji; topologia ponad
  lateralizację nie ma wykrywalnego znaczenia (margines 15 pp)”.
- H2 „topologia ma znaczenie” → twierdzenie o roli topologii w orientacji (z ograniczeniem do tej sieci i zadania).
- ¬H1 → wynik v1 nie przenosi się na zadanie v2; raport bez dalszego strojenia.
Próba z błędem symulatora = porażka, raportowana osobno. Brak innych wykluczeń.
