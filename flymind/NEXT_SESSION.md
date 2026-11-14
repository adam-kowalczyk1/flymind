# FlyMind — wznowienie (stan 2026-10-29)

1. Przeczytaj `flymind/AUTONOMOUS_RESEARCH_LOG.md` (statusy zadań) i `flymind/VALIDATION_PLAN.md`.
2. Integralność: `.venv/bin/python -I -B <skrypt integralności>` — logika w logu (hashe z frozen_manifest_v4.json Stage 1).
   Oczekiwane: 28/28. Zawsze `python -I -B`, nigdy import bio2, nigdy ziarna 0–39 i 300–399, bez commitów.
3. Ziarna: dev 1001–1999; potwierdzające zużyte 2001–2005, 2011–2050, 2051–2100, 3001–3100 (V5 v3 = 3051–3100). BRAK wolnej puli
   potwierdzającej — przed kolejnym potwierdzeniem zarejestruj nową (np. 4001–4100) i sprawdź historię użycia. Tasowania: ziarno próby + 100 000 / 200 000 / 400 000.
4. V5 v3 WYKONANE 2026-10-29 (H1 niepotwierdzona: równoważne ±1°; RT PASS_WITH_LIMITATIONS). Historyczne instrukcje uruchomienia: Po zgodzie:
   skopiuj do `validation/v5v3_protocol.md`, zrób manifest (hashe `v5v3.py`, `side_shuffle.py`, `loop*.py`, …), kopia kodu,
   test dymny na ziarnach dev, potem `.venv/bin/python -I -B flymind/v5v3.py --seeds 3051-3100 --out flymind/results/v5v3
   --approved-protocol-sha256 <sha>`.
5. Testy: `for t in connectome snn_interface alif sensory decoder safety latency epg_ring encoder visual_path side_shuffle v5v3_analysis; do .venv/bin/python -I -B flymind/test_$t.py; done`
   oraz `.venv/bin/python -I -B flymind/test_so101.py --zgoda-sim`.
6. Najwyższy priorytet po decyzji: (a) V5 v3 według r3, albo (b) jeśli użytkownik odrzuci — zaprojektować kontrolę rozdzielającą
   rekurencję LC10a×LC10a od bloku LC10a → AOTU (np. DATA z tasowanym tylko blokiem LC×LC vs DATA z cięciem AOTU) jako nowy protokół.
7. Wycofane/zawężone twierdzenia: „LC10a → AOTU wyjaśnia 43 %” (wycofane jako mechanizm specyficzny); V5 v2 DATA vs SHUF_STR
   miesza topologię, lateralizację i skalę sygnału (`results/audit_shared_decoder_20261029.txt`).
8. Następne zadanie (po zgodzie użytkownika i rejestracji nowej puli): protokół V5 v4 — sceny ρ < 0,28 m, TOST per warstwa ±0,5°
   dla DATA vs SWS v2 oraz SHUF_STR z własną kalibracją dekodera (rozdzielenie skali sygnału od lateralizacji).
9. V5 v4 ZAKOŃCZONE 2026-10-30 (`V5v4_FINAL_REPORT.md`): H1 przeciwne znaki w warstwach (S1 +0,51°, S2 −0,52°), H2 potwierdzone.
   Zużyte pule: 4001–4450 (+200 000, +400 000), 5001–5003, 6001–6002; zakaz ponownego użycia 1001–1999. Następne (za zgodą): Red Team wyników
   V5 v4, potem nowy protokół rozdzielający motywy LC10a×LC10a na nowej puli (sprawdzić historię, np. 7001–7500 — UWAGA: 7001/7002/7101 użyte
   jako ziarna RNG symulacji mocy/testów; wybrać inny zakres).
