# Weryfikacja i Audyt Danych Konektomu MaleCNS v1.0 dla Projektu SO-101

**Data audytu:** 25 października 2026  
**Autor audytu:** Antigravity & Gemini 4 Argon (Google DeepMind)  
**Pliki źródłowe:**
- `data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather` (211 577 ciał komórkowych)
- `data/malecns/body-neurotransmitters-male-cns-v1.0.feather` (1 835 518 ciał, model Eckstein et al., 2024, *Cell*)
- `data/malecns/connectome-weights-male-cns-v1.0-minconf-0.5.feather` (151 856 684 krawędzi synaptycznych)
**Skrypt audytowy:** [`bio2/audit_malecns_connections.py`](file:///Users/admin/so101_fly_project/bio2/audit_malecns_connections.py)  
**Wygenerowane tabele surowe CSV:**
- [`bio2/results/malecns_audit_DN_to_IN.csv`](file:///Users/admin/so101_fly_project/bio2/results/malecns_audit_DN_to_IN.csv)
- [`bio2/results/malecns_audit_IN_to_MN.csv`](file:///Users/admin/so101_fly_project/bio2/results/malecns_audit_IN_to_MN.csv)
- Kopie na Pulpicie: `/Users/admin/Desktop/Explory_Projekt_Mucha_SO101/dane_i_tabele/`

---

## 1. Oświadczenie metodologiczne i uznanie krytyki

W pełni uznajemy i przyjmujemy krytykę recenzenta. Wcześniejsze sformułowania w raporcie zawierały niedopuszczalne skróty myślowe:
1. **Liczba kontaktów synaptycznych to NIE siła fizjologiczna:** Wartości liczbowe w konektomie mikroskopii elektronowej (kolumna `weight`) oznaczają wyłącznie liczbę morfologicznie zrekonstruowanych stref aktywnych (T-bars / PSDs). Nie są to miliwolty ($mV$), nanosiemensy ($nS$) ani moment siły w niutonometrach ($N\cdot m$).
2. **Obecność synapsy to NIE dowód pobudzania:** Znak synapsy zależy od neuroprzekaźnika i receptorów postsynaptycznych. U owadów interneurony GABA-ergiczne oraz glutaminergiczne (działające na kanały $GluCl\alpha$) wywołują **hamowanie postsynaptyczne**.
3. **Ścieżka dwuskokowa to NIE dowód behawioralny:** Wykazanie szlaku `DN` $\to$ `IN` $\to$ `MN` w grafie konektomu stanowi hipotezę anatomiczną, a nie dowód funkcjonalny *in vivo*, że szlak ten steruje „chwytaniem” czy „lądowaniem”.

Poniższy dokument przedstawia stan faktyczny wynikający bezpośrednio z surowych danych.

---

## 2. Skąd pochodzą identyfikatory neuronów i nazwy motoneuronów?

W publikacjach syntetycznych (np. Cheong et al., 2024; Lesser et al., 2024) omawia się główne grupy funkcjonalne, natomiast nazwy takie jak `IN12B018`, `IN12A001`, `IN13A014` są **oficjalnymi identyfikatorami systematycznymi (`type`)** nadanymi przez konsorcjum FlyEM (Janelia Research Campus / Cambridge) dla całego zbioru Male Adult Nerve Cord (MANC) / MaleCNS v1.0.

* **Format nazewnictwa interneuronów:** `IN` (interneuron) + oznaczenie hemilinii rozwojowej i neuropilu (np. `12B`, `12A`, `13A`, `08A`, `21A`) + 3-cyfrowy numer porządkowy typu.
* **Identyfikacja motoneuronów (`Ti flexor MN`, `Ti extensor MN`, `ltm MN`):**
  W bazie MaleCNS v1.0 neurony te zostały zidentyfikowane na drodze korelacji morfologicznej (NBLAST dendrytów oraz nerwów wyjściowych z VNC, takich jak *ProLN*) z atlasami mikroskopii świetlnej (Baek & Mann 2009; Brierley et al. 2012; Enriquez et al. 2015; Azevedo et al. 2020; Lesser et al. 2024). Nazwy te znajdują się bezpośrednio w polu `type` w pliku `body-annotations-male-cns-v1.0-minconf-0.5.feather`.

---

## 3. Wyniki surowego audytu danych (Ciała, Synapsy i Neuroprzekaźniki)

### A. Neurony zstępujące (Descending Neurons)
Wszystkie kluczowe neurony zstępujące są **cholinergiczne (ACh)** (pobudzające):
* `DNp07`: bodyId `11513` (R), `11704` (L) — `acetylcholine` (pewność: 0.967)
* `DNp10`: bodyId `10425` (L), `10433` (R) — `acetylcholine` (pewność: 0.960)
* `DNp47`: bodyId `10280` (R), `522961` (L) — `acetylcholine` (pewność: 0.964)
* `DNa02`: bodyId `10360` (R), `523769` (L) — `acetylcholine` (pewność: 0.942)
* `DNg13`: bodyId `11074` (L), `512006` (R) — `acetylcholine` (pewność: 0.953)

### B. Weryfikowane interneurony i ich neuroprzekaźniki
Kwerenda bazy `body-neurotransmitters` wykazała podział chemiczny:
* **`IN12A001`**: bodyId `800073` (T1_R), `800147` (T1_L), `800383` (T2_L), `903429` (T2_R) $\to$ **`acetylcholine` (pewność 0.97)** — **interneuron pobudzający**.
* **`IN12B018`**: bodyId `800898` (T1_R), `802751` (T3_R), `802843` (T3_L), `802944` (T2_R), `904036` (T2_L), `904246` (T1_L) $\to$ **`gaba` (pewność 0.90)** — **interneuron hamujący**.
* **`IN13A014`**: bodyId `801412` (T3_L), `801493` (T2_L), `802546` (T1_L), `802990` (T1_R), `902313` (T2_R), `905164` (T3_R) $\to$ **`gaba` (pewność 0.88)** — **interneuron hamujący**.
* **`IN08A006`**: bodyId `800511` (T2_L), `800561` (T1_L), `800722` (T3_R), `800856` (T3_L), `801437` (T1_R), `905009` (T2_R) $\to$ **`gaba` (pewność 0.89)** — **interneuron hamujący**.
* **`IN21A007`**: bodyId `801222` (T1_R), `801510` (T3_R), `801638` (T2_R), `801666` (T3_L), `801904` (T1_L) $\to$ **`glutamate` (pewność 0.80)** — **interneuron glutaminergiczny**.

---

## 4. Weryfikacja twierdzeń z poprzedniego raportu

| Twierdzenie z raportu | Rzeczywiste dane w MaleCNS v1.0 | Weryfikacja chemiczna | Prawidłowy wniosek naukowy |
|---|---|---|---|
| *„IN12B018 otrzymuje 1237 synaps od DNp47”* | **Potwierdzone anatomicznie:** `DNp47` (10280, 522961) tworzy sumarycznie **1237 kontaktów synaptycznych (T-bars)** na komórki typu `IN12B018` (np. 138 synaps na ciało 904036, 131 na 904036, 126 na 802751). | `DNp47` to ACh, ale `IN12B018` to **GABA**. | `DNp47` silnie pobudza hamujący interneuron `IN12B018`. W efekcie szlak ten realizuje **hamowanie wyprzedzające (feed-forward inhibition)**, a nie pobudzanie! |
| *„IN12B018 pobudza motoneurony zginacza i prostownika”* | **Błędna interpretacja:** `IN12B018` łączy się z `Ti extensor MN` (np. ciało 815344 w T1) oraz `Ti flexor MN` (ciało 827188). | `IN12B018` jest **GABA-ergiczny**. | Połączenie jest **hamujące**, co w biologii odpowiada mechanizmowi wyciszania ko-kontrakcji antagonistów. |
| *„Synapsa o wadze 200.0 powoduje natychmiastowe rozprężenie prostownika”* | **Częściowo trafna intuicja, ale zła terminologia:** `IN13A014` tworzy od **120 do 271 kontaktów synaptycznych** bezpośrednio na motoneurony prostownika `Ti extensor MN` (np. 162 synapsy na ciało 815344 w T1, 138 na 815678 w T1, 206 na 801234 w T2, 271 na 800158 w T3). | `IN13A014` jest **GABA-ergiczny**. | Ogromna liczba kontaktów synaptycznych (>160 w segmencie T1) ze zidentyfikowanym przekaźnikiem **GABA** oznacza silny szlak **hamowania prostownika piszczeli**. W modelu inżynierskim przekłada się to na zdjęcie momentu prostującego, umożliwiając zamknięcie chwytaka. |
| *„DNa02 przygotowuje chwyt przed kontaktem z celem”* | **Fakt anatomiczny + Hipoteza funkcjonalna:** `DNa02` tworzy silne połączenia (113 do 209 kontaktów) na interneurony `IN08A006` (GABA), a te z kolei rzutują na motoneurony nogi. | `DNa02` (ACh) $\to$ `IN08A006` (GABA) $\to$ MN. | Anatomicznie pościg wzrokowy (`DNa02`) moduluje sieć przedmotoryczną nogi. Twierdzenie, że służy to „przygotowaniu chwytu”, to **hipoteza inżynierska i model obliczeniowy**, a nie udowodniony fakt behawioralny u muchy. |
| *„ltm MN steruje chwytem pazurków”* | **Potwierdzone w literaturze (Azevedo et al., 2024):** Mięsień *ltm* (*long tendon muscle*) napędza ścięgno *retractor unguis*, które bezpośrednio zgina pazurki stopy (*tarsal claws*). W MaleCNS zidentyfikowano motoneurony `ltm MN` (np. ciała 910334 w T1, 905487 w T2). | Motoneurony *ltm* są glutaminergiczne (jak wszystkie motoneurony stawowe owadów na NMJ). | Rola *ltm* w zacisku stopy jest poparta literaturą, ale przeniesienie tej funkcji na szczęki serwa STS3215 w robocie SO-101 jest **analogią bioniczną**. |

---

## 5. Podział epistemologiczny (Dla Jury Konkursu E(x)plory)

| Poziom dowodowy | Zakres | Co udowodniono w projekcie? | Źródło / Plik |
|---|---|---|---|
| **Poziom A: Fakty anatomiczne (EM)** | Połączenia i liczby styków synaptycznych ($N_{\text{syn}}$) | Bezpośrednie numery `bodyId`, istnienie krawędzi synaptycznych i surowa liczba wykrytych stref aktywnych (T-bars). | `malecns_audit_DN_to_IN.csv`, `malecns_audit_IN_to_MN.csv`, MaleCNS v1.0. |
| **Poziom B: Predykcje neuroprzekaźników** | Chemia synaps (ACh, GABA, Glu) | Konsensus predykcji uczenia maszynowego z morfologii pęcherzyków synaptycznych (Eckstein et al., 2024, *Cell*). | Kolumny `consensus_nt` i `predicted_nt_confidence` w bazie MaleCNS. |
| **Poziom C: Model i Sterownik Robota** | Funkcja behawioralna i ruch ramienia SO-101 | Architektura sterownika SO-101 inspirowana konektomem (nawigacja proporcjonalna PN, pre-shaping loomingu, odruch Hennemana). Wykazano, że model ten skutecznie łapie piłkę w wietrze (35% vs 0% w próżni), ale **jest to bioniczna hipoteza inżynierska, a nie dowód fizjologiczny na żywym owadzie**. | Kod [`throw_catch_embodied.py`](file:///Users/admin/so101_fly_project/bio2/throw_catch_embodied.py), wideo MP4/GIF. |
