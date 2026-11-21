# T1 — przeszczep liczb synaps MaleCNS do flyvis: **FAILED** (20 XI 2026, plan PREREG_T0_T1.md)
Policzone 4 modele (000, 013, 026, 038; po ~10 min) — w każdym DSI wszystkich T4a–d i T5a–d = **0,00** (te same modele
na liczbach flyvis: do 0,78). Pozostałe 46 modeli ZATRZYMANE (odstępstwo od planu: wynik systematyczny, ≥ 30/50 nieosiągalne
przy 0/4 z dokładnym zerem; kontrola „shuffle” też zatrzymana, 0 modeli). Sprawdzian metody: model 000 na liczbach flyvis
daje DSI identyczne z wbudowaną funkcją flyvis (t1_smoke_orig.json).
**Diagnoza (po teście, model 000, szary ekran → błysk):** sieć na liczbach MaleCNS jest niestabilna — napięcia rosną
do |V| ~ 10¹⁴ (np. T2 1,4·10⁹ w spoczynku; flyvis: 3,2). Wyuczone właściwości typów flyvis są dostrojone do liczb samicy;
MaleCNS ma w wielu parach więcej synaps (mediana 1,45×, szerokopolowe typy nawet ×10–60 w kluczach flyvis), co wypycha
pętle zwrotne poza stabilność. Wniosek: właściwości typów NIE przenoszą się 1:1 między mapami połączeń.

## Errata (21 XI, P3)
Liczby MaleCNS w T1 (`malecns_keys.csv`) to średnie tylko po komórkach celu, które MAJĄ dane przesunięcie (średnia
warunkowa) — sumy par wychodziły ok. 2–3× większe niż we flyvis, co tłumaczy eksplozję sieci. T1b skalował sumy do flyvis,
więc go to nie dotyczy. Wersja poprawna (bezwarunkowa) w `p3_connectome.py`.
