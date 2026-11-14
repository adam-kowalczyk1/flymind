# V5 v4 — Etap A: audyt stanu (2026-10-29 21:50)

## Potwierdzone samodzielnie w tej sesji (polecenia uruchomione)
- Stage 1: 28/28 hashy z `frozen_manifest_v4.json`, protokół Stage 1 zgodny, manifest 2f061a60…; `bio2/__pycache__` bez zmian od 26.10;
  brak zmian w bio2/assets/data (skrypt integralności, wpis w `AUTONOMOUS_RESEARCH_LOG.md`).
- V5 v3: kod = manifest = kopia zamrożona; protokół = sha a0f09809…; dane bez zmian (`check_v5v3_manifest.py`).
- V5 v3: niezależna reanaliza (`audit_v5v3_independent.py`) ponownie daje d i decyzje zgodne z `v5v3.analyze` (H1 −0,191°, H2 −2,401°, H3 −2,210°).
- Testy: 12 zestawów jednostkowych + symulator T1–T9 zielone (uruchomione teraz); nowe `test_v5v4.py` 18 asercji zielone.
- Pule ziaren 4001–4240, 5001–5010, 6001–6010 i pochodne (+100 000/200 000/400 000/500 000): brak w 57 plikach JSON i w kodzie.
  Brak ziaren 0–39 i 300–399 w jakimkolwiek zapisie.
- Kalibracja `v5v4.calibrate` na puli 5001–5003: deterministyczna; DATA 492,1 Hz/rad, TOY 306,1 Hz/rad.

## Tylko z wcześniejszych raportów (nie powtarzane teraz)
- Odtwarzalność bitowa prób V5 v3 (ziarna 3051–3052) — raport Red Team V5 v3.
- Wynik eksploracji skali sygnału na dev 1001–1044 (Red Team) — moja weryfikacja dotyczyła dev 1501–1520.
- Wyniki V5 v1/v2 i wcześniejszych etapów — wcześniejsze raporty i audyty.

## Zajęte pule ziaren
dev 1001–1999 (zakaz ponownego użycia); potwierdzające 2001–2005, 2011–2050, 2051–2100, 3001–3100; pochodne +100 000, +200 000,
+400 000, +500 000 od użytych ziaren; RNG analiz 2201, 2202, 3301, 3401, 3402, 7001 (symulacja mocy V5 v4).

## Braki blokujące
Brak blokad integralności. Do protokołu V5 v4 wymagane były: nowa pula kalibracyjna (dotychczasowa kalibracja używała ziaren 1001–1003,
teraz zakazanych) i nowa pula dev do testu dymnego — zaprojektowane (5001–5003, 6001–6002).
