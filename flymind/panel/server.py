"""FlyMind — lokalny panel uruchamiania istniejących pokazów i testów (tylko 127.0.0.1, tylko biblioteka standardowa).

Uruchom:   .venv/bin/python -I -B flymind/panel/server.py          → http://127.0.0.1:8770
Zasady wbudowane w kod:
  - serwer słucha WYŁĄCZNIE na 127.0.0.1 (adresu nie da się zmienić opcją); żądania z innym nagłówkiem Host są odrzucane;
  - uruchamiane są tylko pozycje z zamkniętej listy JOBS; parametry tylko z list / zakresów zapisanych niżej —
    nigdzie nie ma pola na dowolną komendę ani dowolne ziarno;
  - ziarno pokazu ramienia jest stałe (20951 = „kontrola uruchomienia” z SEED_REGISTRY kroku 2); ziarna testowe nie występują;
  - nie ma benchmarków 135 prób ani żadnego kodu sprzętowego;
  - wyjścia uruchomień trafiają do flymind/panel/runs/<czas>_<pozycja>/ (nie do results/); niczego nie nadpisuje;
  - istniejących skryptów, modułów i wyników panel nie zmienia — tylko je uruchamia / czyta.
"""
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"                       # celowo stała, nie opcja
PORT = 8770
HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(HERE)
ROOT = os.path.dirname(FLY)
RUNS = os.path.join(HERE, "runs")
PY = os.path.join(ROOT, ".venv", "bin", "python")
MJPY = os.path.join(ROOT, ".venv", "bin", "mjpython")
ARM_SEED = 20951                         # jedyne dozwolone ziarno pokazu ramienia
# Zestaw podstawowy z object_handling.SETS["base"] (jedyny, który przyjmuje demo_arm.find_item). Opisy wg komentarzy
# w object_handling.py (wymiary = połówki × 2; materiał = gęstość, tarcie, „odpowiednik” z komentarza).
SHAPES = {"cube_S": "sześcian mały (2 cm)", "cube_M": "sześcian średni (3 cm)", "cube_L": "sześcian duży (4,5 cm)",
          "cyl": "walec stojący (3 × 5 cm)", "sphere": "kula (3,5 cm)", "flat": "płytka (5 × 3,5 × 1 cm)",
          "long": "belka (8 × 2 × 2 cm)", "L": "kształt L (nieregularny)", "wedge": "klin (nieregularny)"}
MATS = {"hard_grip": "guma, przyczepna (tarcie 1,0)", "hard_slick": "śliskie tworzywo (tarcie 0,2)",
        "heavy": "stal, ciężka (tarcie 0,5)", "light": "pianka/balsa, lekka (tarcie 0,6)", "mid": "drewno (tarcie 0,5)"}
WINDOW_NOTE = "NOT VERIFIED — okno MuJoCo musi obejrzeć człowiek"


# ------------------------------------------------------------------ parametry (zamknięte listy / zakresy)
def P_choice(key, label, options, default):
    """options: lista wartości albo słownik wartość → opis po polsku (opis tylko do wyświetlenia)."""
    labels = dict(options) if isinstance(options, dict) else {o: o for o in options}
    return dict(key=key, label=label, type="choice", options=list(labels), labels=labels, default=default)


def P_num(key, label, lo, hi, default, step):
    return dict(key=key, label=label, type="number", min=lo, max=hi, default=default, step=step)


def P_bool(key, label, default=False):
    return dict(key=key, label=label, type="bool", default=default)


def clean(spec, raw):
    """Zwraca wartości parametrów po sprawdzeniu; wszystko spoza list/zakresów → ValueError."""
    out = {}
    for p in spec:
        v = raw.get(p["key"], p["default"])
        if p["type"] == "choice":
            if v not in p["options"]:
                raise ValueError(f"{p['key']}: wartość spoza listy")
        elif p["type"] == "bool":
            if not isinstance(v, bool):
                raise ValueError(f"{p['key']}: oczekiwano tak/nie")
        else:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not (p["min"] <= v <= p["max"]):
                raise ValueError(f"{p['key']}: poza zakresem {p['min']}…{p['max']}")
            v = float(v)
        out[p["key"]] = v
    extra = set(raw) - {p["key"] for p in spec}
    if extra:
        raise ValueError(f"nieznane parametry: {sorted(extra)}")
    return out


def num(v):
    return str(int(v)) if float(v).is_integer() else repr(float(v))


# ------------------------------------------------------------------ zamknięta lista pozycji
def argv_demo_v5(p):
    a = [MJPY, os.path.join(FLY, "demo", "demo.py"), "--mode", p["mode"], "--az", num(p["az"]), "--rho", num(p["rho"]),
         "--jump", num(p["jump"]), "--seconds", num(p["seconds"])]
    return a + (["--present"] if p["present"] else [])


def argv_demo_arm(p):
    return [MJPY, os.path.join(FLY, "demo", "demo_arm.py"), "--item", f"{p['shape']}/{p['mat']}", "--seed", str(ARM_SEED),
            "--pose", p["pose"], "--glu", p["glu"], "--speed", num(p["speed"]), "--seconds", num(p["seconds"])]


JOBS = {
    "demo_v5": dict(
        group="Pokazy na żywo (osobne okno MuJoCo)", title="Pokaz 1 — ramię obraca się za piłeczką",
        desc="Obwód wzrokowy muszki (424 neurony) obraca podstawę ramienia w stronę zielonej piłeczki. Obok obrazu widać "
             "impulsy neuronów na żywo. Tryb P to klasyczny regulator do porównania. Uwaga: „oko” to wykrywacz zielonego "
             "koloru, nie oko muszki.",
        evidence="Liczby 38/40 itd.: VERIFIED (plik). Zgodność pokazu z eksperymentem: VERIFIED (test pokazu). Okno: " + WINDOW_NOTE,
        window=True, argv=argv_demo_v5,
        params=[P_choice("mode", "Kto steruje", ["snn", "p"], "snn"), P_bool("present", "Tryb prezentacji (scenariusz z podpisami)"),
                P_num("az", "Początkowy kąt piłeczki [°]", -30, 30, 20, 1), P_num("rho", "Odległość piłeczki [m]", 0.15, 0.30, 0.20, 0.01),
                P_num("jump", "Przestawiaj piłeczkę co [s] (0 = nie)", 0, 10, 0, 0.5),
                P_num("seconds", "Zamknij okno po [s] (0 = ręcznie)", 0, 600, 0, 5)],
        note="Ziarno szumu stałe (9 900 001, poza pulami eksperymentów)."),
    "demo_arm": dict(
        group="Pokazy na żywo (osobne okno MuJoCo)", title="Pokaz 2 — całe ramię sterowane siecią nogi muszki",
        desc="Sieć dwóch nóg muszki (2593 + 1507 = 4100 neuronów) steruje barkiem, łokciem i nadgarstkiem przy podnoszeniu. "
             "To pokaz WYNIKU NEGATYWNEGO: ramię chwyta i lekko unosi, ale przedmiotu nie przenosi. Budowa sieci trwa ok. minuty, "
             "zanim otworzy się okno; pokaz idzie wolniej niż czas rzeczywisty.",
        evidence="Wynik kroku 2: FAILED (0/135 odłożonych), liczby VERIFIED. Zgodność pokazu z eksperymentem: VERIFIED (test pokazu). "
                 "Okno: " + WINDOW_NOTE,
        window=True, argv=argv_demo_arm,
        params=[P_choice("shape", "Kształt przedmiotu", SHAPES, "cube_S"), P_choice("mat", "Materiał przedmiotu", MATS, "hard_grip"),
                P_choice("pose", "Położenie", {"0": "0", "1": "1", "2": "2"}, "0"),
                P_choice("glu", "Wariant znaku glutaminianu", ["-1", "1"], "-1"),
                P_num("speed", "Tempo (1 = czas rzeczywisty)", 0.25, 4, 1, 0.25),
                P_num("seconds", "Zamknij okno po [s] (0 = ręcznie)", 0, 900, 0, 5)],
        note=f"9 kształtów × 5 materiałów = 45 przedmiotów (zestaw podstawowy). Kształt i materiał wybiera się przed otwarciem okna; "
             f"żeby zmienić, zamknij pokaz i otwórz go ponownie. Ziarno stałe {ARM_SEED} (kontrola uruchomienia, nie test)."),
    "test_demo": dict(
        group="Testy (bez okna)", title="Test pokazu 1 (obrót za piłeczką)",
        desc="Sprawdza, że pokaz robi dokładnie to samo co eksperyment: te same ruchy co do liczby, ruch pochodzi z impulsów "
             "neuronów, tryb klasyczny nie używa sieci. Ok. 1 minuty.",
        evidence="VERIFIED 14 XI (T1–T10 OK)", window=False, params=[],
        argv=lambda p: [PY, "-I", "-B", os.path.join(FLY, "demo", "test_demo.py")]),
    "test_demo_arm": dict(
        group="Testy (bez okna)", title="Test pokazu 2 (całe ramię)",
        desc="Sprawdza, że pokaz ramienia daje wynik identyczny z eksperymentem i że impulsy na ekranie są prawdziwe. Ok. 1–3 minut.",
        evidence="VERIFIED 14 XI (T1–T5 OK, sha trajektorii 50b22ed1…)", window=False, params=[],
        argv=lambda p: [PY, "-I", "-B", os.path.join(FLY, "demo", "test_demo_arm.py")]),
    "module_tests": dict(
        group="Testy (bez okna)", title="Testy modułów (20 zestawów)",
        desc="Sprawdza podstawowe klocki projektu: wczytanie mapy połączeń, model neuronu, dekoder, warstwę bezpieczeństwa, "
             "symulator, chwyt. Ok. 3 minut.",
        evidence="VERIFIED 14 XI (20/20)", window=False, params=[],
        argv=lambda p: [PY, "-I", "-B", os.path.join(HERE, "run_module_tests.py")]),
}

# ------------------------------------------------------------------ filmy i obrazy (tylko te pliki, tylko do odczytu)
MEDIA = [
    ("v5_presentation", "demo/media/flymind_presentation.mp4", "Pokaz 1: prezentacja — ramię śledzi piłeczkę, sieć kontra klasyczny regulator"),
    ("v5_neurons", "demo/media/flymind_neurons.mp4", "Pokaz 1: impulsy neuronów obwodu wzrokowego"),
    ("arm", "demo/media_arm_20261113/demo_arm.mp4", "Pokaz 2: całe ramię z sieci (wynik negatywny — unosi, nie przenosi)"),
    ("grip_B", "results/sensory_manipulation/media/demo_B_fly_v1.mp4", "Chwyt sterowany dotykiem — seria ciągła (sam dotyk)"),
    ("grip_C", "results/sensory_manipulation/media/demo_C_fly_feco_v1.mp4", "Chwyt sterowany dotykiem i czuciem położenia szczęki"),
    ("G1", "results/poster_20261114/G1_obrot_do_pileczki.png", "Wykres: obrót w stronę piłeczki (trafienia na 40)"),
    ("G2", "results/poster_20261114/G2_chwyt_dotykiem.png", "Wykres: chwyt sterowany dotykiem (na 135)"),
    ("G3", "results/poster_20261114/G3_cale_ramie.png", "Wykres: całe ramię — wynik negatywny (na 135)"),
]
MEDIA_PATH = {k: os.path.join(FLY, rel) for k, rel, _ in MEDIA}
CTYPE = {".mp4": "video/mp4", ".png": "image/png", ".html": "text/html; charset=utf-8"}


# ------------------------------------------------------------------ kluczowe liczby — czytane z plików przy każdym żądaniu
def _j(rel):
    with open(os.path.join(FLY, rel)) as f:
        return json.load(f)


def numbers():
    rows = []

    def add(section, label, fn, src, level="VERIFIED (liczone z pliku w tej chwili)"):
        try:
            val = fn()
        except Exception as e:                                   # brak pliku = uczciwie „brak”, nie zgadujemy
            val, level = f"brak danych ({type(e).__name__})", "NOT VERIFIED"
        rows.append(dict(section=section, label=label, value=val, source="flymind/" + src, level=level))

    v5 = "results/v5/analysis_confirm.json"
    c = lambda k: _j(v5)["conds"][f"{k}|delay0ms"]["success"]  # noqa: E731
    S1 = "1. Obrót w stronę piłeczki (40 prób)"
    add(S1, "sieć z danych", lambda: f"{c('snn')}/40", v5)
    add(S1, "klasyczny regulator", lambda: f"{c('classical_p')}/40", v5)
    add(S1, "KONTROLA: połączenia przetasowane", lambda: f"{c('snn_shuffle')}/40", v5)
    add(S1, "kontrola łańcucha: strony zamienione / bez wzroku", lambda: f"{c('snn_swap')}/40 i {c('no_vision')}/40", v5)
    rows.append(dict(section=S1, label="KONTROLA: tasowanie zachowujące siłę połączeń", value="10/10", source="flymind/VALIDATION_PLAN.md (§ V4/V5 — Red Team, pkt 1)",
                     level="REPORTED (brak zachowanego pliku wyniku)"))
    k = lambda rel: _j(rel)["summary"]["success"]["k"]  # noqa: E731
    S2 = "2. Chwyt sterowany dotykiem (135 prób)"
    add(S2, "sieć z danych", lambda: f"{k('results/sensory_manipulation/B_fly_search_glu-1_v1.json')}/135", "results/sensory_manipulation/B_fly_search_glu-1_v1.json")
    add(S2, "klasyczny sterownik", lambda: f"{k('results/object_handling/B_base_v2.json')}/135", "results/object_handling/B_base_v2.json")
    add(S2, "prosty odruch", lambda: f"{k('results/sensory_manipulation/D_reflex_search_v1.json')}/135", "results/sensory_manipulation/D_reflex_search_v1.json")

    def shuffles():
        v = [k(f"results/sensory_manipulation/S_shuffle{i}_search_v1.json") for i in (1, 2, 3)]
        v += [_j(f"results/shuffle_matched/shuffle_171000{i}_v1.json")["success"] for i in range(11, 21)]
        return f"od {min(v)} do {max(v)} (13 sieci: {', '.join(map(str, sorted(v)))})"
    add(S2, "KONTROLA: sieci przetasowane", shuffles, "results/sensory_manipulation/S_shuffle*_search_v1.json, results/shuffle_matched/")
    add(S2, "sztywniejszy kontakt: klasyczny / sieć", lambda: f"{_j('results/contact_audit/stiff_A_v1.json')['success']} / {_j('results/contact_audit/stiff_B_v1.json')['success']}",
        "results/contact_audit/stiff_A_v1.json, stiff_B_v1.json")
    T = "results/step2_whole_arm_20261113/whole_arm_5/test/"
    pl = lambda tag, key="placed": sum(bool(r["truth"][key]) for r in _j(T + f"arm_test_{tag}.json")["runs"])  # noqa: E731
    S3 = "3. Całe ramię z sieci nogi muszki (135 prób) — WYNIK NEGATYWNY"
    add(S3, "sieć z danych: odłożone (wariant A / B znaku)", lambda: f"{pl('N_g-1')}/135 i {pl('N_g1')}/135", T + "arm_test_N_g*.json")
    add(S3, "sieć z danych: uniesione ≥ 2 cm (A / B)", lambda: f"{pl('N_g-1', 'lift')}/135 i {pl('N_g1', 'lift')}/135", T + "arm_test_N_g*.json")
    add(S3, "klasyczny sterownik: odłożone (A / B)", lambda: f"{pl('K_g-1')}/135 i {pl('K_g1')}/135", T + "arm_test_K_g*.json")
    add(S3, "KONTROLA: 5 sieci przetasowanych, odłożone (A)", lambda: ", ".join(str(pl(f"S{i}_g-1")) for i in range(1, 6)), T + "arm_test_S*_g-1.json")
    add(S3, "KONTROLA: 5 sieci przetasowanych, odłożone (B)", lambda: ", ".join(str(pl(f"S{i}_g1")) for i in range(1, 6)), T + "arm_test_S*_g1.json")

    def elbow(L):
        r = _j(f"results/verification_step2_20261114/elbow_diag/c_diag_N_g1_liftmax{L}.json")["runs"]
        return f"{sum(bool(x['success']) for x in r)}/{len(r)}"
    add(S3, "sam łokieć, limit 3 s / 10 s: odłożone", lambda: f"{elbow(3)} / {elbow(10)}", "results/verification_step2_20261114/elbow_diag/",
        "VERIFIED liczba; wynik EKSPLORACYJNY (limit zmieniony po teście, bez tasowań)")
    return rows


CONCLUSIONS = [
    "Wszystko działa w symulacji MuJoCo. Prawdziwe ramię SO-101 nie było sterowane siecią.",
    "Sieć z konektomu potrafi obrócić ramię w stronę celu i dobrać siłę chwytu; całym ramieniem nie steruje skutecznie.",
    "W żadnym z trzech zadań dokładny schemat połączeń muszki nie okazał się lepszy od przetasowanego ani od klasycznego sterownika.",
    "„Oko” w pokazie 1 to wykrywacz zielonego koloru podający ten sam prąd wszystkim neuronom jednej strony — sztuczne pobudzanie, nie oko muszki.",
    "W działających etapach sieć wydaje ok. 3 % komend; dojazd ramienia i kolejność faz są klasyczne.",
]

# ------------------------------------------------------------------ uruchomienia
LOCK = threading.Lock()
RUNS_MEM = {}                                   # id → dict(job, title, argv, proc, log, started, ended, code, stopped, params)


def start(job_id, raw):
    job = JOBS[job_id]
    params = clean(job["params"], raw)
    with LOCK:
        for r in RUNS_MEM.values():
            if r["proc"].poll() is None and (r["job"] == job_id or (job["window"] and JOBS[r["job"]]["window"])):
                raise ValueError("ta pozycja (albo inne okno pokazu) już działa — najpierw ją zatrzymaj")
        rid = time.strftime("%Y%m%d_%H%M%S") + "_" + job_id
        d = os.path.join(RUNS, rid)
        os.makedirs(d, exist_ok=False)                           # nowy katalog; istniejącego nie ruszamy
        argv = job["argv"](params)
        log = os.path.join(d, "log.txt")
        with open(os.path.join(d, "run.json"), "x") as f:
            json.dump(dict(id=rid, job=job_id, params=params, argv=argv, started=time.strftime("%Y-%m-%dT%H:%M:%S")), f,
                      indent=1, ensure_ascii=False)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
        lf = open(log, "xb")
        proc = subprocess.Popen(argv, cwd=d, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env,
                                start_new_session=True)
        lf.close()
        RUNS_MEM[rid] = dict(id=rid, job=job_id, title=job["title"], argv=argv, proc=proc, log=log, dir=d, params=params,
                             started=time.time(), ended=None, stopped=False, window=job["window"])
    return rid


def status(r):
    code = r["proc"].poll()
    if code is not None and r["ended"] is None:
        r["ended"] = time.time()
        try:
            with open(os.path.join(r["dir"], "result.json"), "x") as f:
                json.dump(dict(exit_code=code, stopped_by_user=r["stopped"], seconds=round(r["ended"] - r["started"], 1)), f)
        except OSError:
            pass
    state = "działa" if code is None else "zatrzymane" if r["stopped"] else "zakończone" if code == 0 else "błąd"
    return dict(id=r["id"], job=r["job"], title=r["title"], state=state, exit_code=code, window=r["window"], params=r["params"],
                seconds=round((r["ended"] or time.time()) - r["started"], 1), command=" ".join(os.path.relpath(a, ROOT) if a.startswith(ROOT) else a for a in r["argv"]),
                out_dir=os.path.relpath(r["dir"], ROOT))


def stop(rid):
    r = RUNS_MEM[rid]
    if r["proc"].poll() is not None:
        return
    r["stopped"] = True
    pg = os.getpgid(r["proc"].pid)
    os.killpg(pg, signal.SIGINT)                    # jak Ctrl+C: skrypt może posprzątać (okno, pamięć współdzielona)

    def harder():
        for sig, wait in ((signal.SIGTERM, 4), (signal.SIGKILL, 4)):
            try:
                r["proc"].wait(timeout=wait)
                return
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(pg, sig)
                except ProcessLookupError:
                    return
    threading.Thread(target=harder, daemon=True).start()


def stop_all():
    for rid in list(RUNS_MEM):
        try:
            stop(rid)
        except Exception:
            pass


# ------------------------------------------------------------------ HTTP
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
RID = re.compile(r"^\d{8}_\d{6}_[a-z0-9_]+$")


class H(BaseHTTPRequestHandler):
    server_version = "FlyMindPanel/1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _guard(self, post=False):
        if self.client_address[0] != "127.0.0.1" or self.headers.get("Host") not in ALLOWED_HOSTS:
            self._send(403, dict(error="tylko 127.0.0.1"))
            return False
        if post:
            o = self.headers.get("Origin")
            if (o is not None and o not in {"http://" + h for h in ALLOWED_HOSTS}) or self.headers.get("X-FlyMind-Panel") != "1":
                self._send(403, dict(error="żądanie spoza panelu"))
                return False
        return True

    def do_GET(self):
        if not self._guard():
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read(), CTYPE[".html"])
        if u.path == "/api/jobs":
            cat = [dict(id=k, group=j["group"], title=j["title"], desc=j["desc"], evidence=j["evidence"], window=j["window"],
                        params=j["params"], note=j.get("note", "")) for k, j in JOBS.items()]
            return self._send(200, dict(jobs=cat, media=[dict(key=k, title=t, kind="video" if rel.endswith(".mp4") else "image",
                                                              source="flymind/" + rel, exists=os.path.isfile(MEDIA_PATH[k])) for k, rel, t in MEDIA],
                                        conclusions=CONCLUSIONS))
        if u.path == "/api/runs":
            with LOCK:
                rs = [status(r) for r in RUNS_MEM.values()]
            return self._send(200, dict(runs=sorted(rs, key=lambda r: r["id"], reverse=True)))
        if u.path == "/api/log":
            rid = q.get("run", [""])[0]
            if not RID.match(rid) or rid not in RUNS_MEM:
                return self._send(404, dict(error="nie ma takiego uruchomienia"))
            try:
                off = max(0, int(q.get("from", ["0"])[0]))
            except ValueError:
                off = 0
            with open(RUNS_MEM[rid]["log"], "rb") as f:
                f.seek(off)
                data = f.read(200_000)
            return self._send(200, dict(text=data.decode("utf-8", "replace"), next=off + len(data)))
        if u.path == "/api/numbers":
            return self._send(200, dict(rows=numbers()))
        if u.path.startswith("/media/"):
            return self._media(u.path[len("/media/"):])
        self._send(404, dict(error="nie ma takiej strony"))

    def _media(self, key):
        p = MEDIA_PATH.get(key)                                  # tylko klucze z listy — żadnych ścieżek od użytkownika
        if p is None or not os.path.isfile(p):
            return self._send(404, dict(error="brak pliku"))
        size = os.path.getsize(p)
        a, b = 0, size - 1
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                a = int(m.group(1))
                b = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
            else:
                a = max(0, size - int(m.group(2)))
            if a > b or a >= size:
                return self._send(416, b"", extra={"Content-Range": f"bytes */{size}"})
        with open(p, "rb") as f:
            f.seek(a)
            data = f.read(b - a + 1)
        self.send_response(206 if m else 200)
        self.send_header("Content-Type", CTYPE[os.path.splitext(p)[1]])
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Accept-Ranges", "bytes")
        if m:
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if not self._guard(post=True):
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}") if 0 <= n <= 10_000 else None
            if not isinstance(body, dict):
                raise ValueError("złe żądanie")
            if self.path == "/api/run":
                job = body.get("job")
                if job not in JOBS:
                    raise ValueError("pozycja spoza listy")
                p = body.get("params") or {}
                if not isinstance(p, dict):
                    raise ValueError("złe parametry")
                return self._send(200, dict(run=start(job, p)))
            if self.path == "/api/stop":
                rid = body.get("run")
                if not isinstance(rid, str) or rid not in RUNS_MEM:
                    raise ValueError("nie ma takiego uruchomienia")
                stop(rid)
                return self._send(200, dict(ok=True))
            self._send(404, dict(error="nie ma takiej akcji"))
        except ValueError as e:
            self._send(400, dict(error=str(e)))


def main():
    if len(sys.argv) > 1:
        sys.exit("panel nie ma opcji: adres 127.0.0.1 i port %d są stałe" % PORT)
    for p in (PY, MJPY):
        if not os.path.exists(p):
            sys.exit(f"brak {p}")
    os.makedirs(RUNS, exist_ok=True)
    srv = ThreadingHTTPServer((HOST, PORT), H)
    assert srv.server_address[0] == "127.0.0.1"
    print(f"FlyMind panel: http://{HOST}:{PORT}   (zatrzymanie: Ctrl+C; zatrzymuje też uruchomione pokazy)", flush=True)
    signal.signal(signal.SIGTERM, lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_all()
        srv.server_close()
        print("panel zatrzymany")


if __name__ == "__main__":
    main()
