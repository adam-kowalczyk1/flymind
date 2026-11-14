"""pad_so101/settings.py — ustawienia pada (settings.json) + lokalna strona ustawień.

  .venv/bin/python pad_so101/settings.py      # otwiera http://127.0.0.1:8101 (settings.html)

run.py wczytuje settings.json przy starcie i co sekundę sprawdza zmiany (można zmieniać w trakcie jazdy).
Tylko stdlib. Każdy zapis przechodzi przez validate(): zakresy liczb, przyciski bez powtórzeń.
"""
import copy
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "settings.json")
PAGE = os.path.join(HERE, "settings.html")
PORT = 8101

BUTTONS = ("A", "B", "X", "Y", "BACK", "START", "LEFTSTICK", "RIGHTSTICK", "LB", "RB",
           "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT")
# akcja → przycisk fizyczny. Wartości domyślne = nazwy, których używa control.py (pad.py tłumaczy przez tę mapę).
DEFAULTS = {
    "deadzone": 0.15,
    "expo": 2.0,
    "invert": {"lx": False, "ly": False, "rx": False, "ry": False},
    "swap_triggers": False,
    "gears": [[0.35, 0.04], [0.8, 0.10], [1.4, 0.20]],     # [rad/s, m/s] dla biegów 1–3
    "start_gear": 2,
    "grip_speed": 1.2,
    "buttons": {"mode": "X", "home": "Y", "goto": "A", "save": "B", "stop": "BACK", "play": "START",
                "record": "RIGHTSTICK", "gear_up": "DPAD_UP", "gear_down": "DPAD_DOWN",
                "slot_prev": "DPAD_LEFT", "slot_next": "DPAD_RIGHT", "pitch_up": "RB", "pitch_down": "LB"},
    "rumble": True,
    "max_lead": 0.25,
    "grip_kp": 3.0,
    "real_sign": [1, 1, 1, 1, 1],
    "real_grip_open": 100,
}
# zakresy; prędkość stawów ≤ 1,5 rad/s = v_max warstwy bezpieczeństwa flymind/safety.py
NUM = {"deadzone": (0.02, 0.4), "expo": (1.0, 3.0), "grip_speed": (0.2, 3.0), "max_lead": (0.05, 0.5),
       "grip_kp": (0.5, 6.0)}
GEAR_RAD, GEAR_M = (0.05, 1.5), (0.01, 0.3)


def _num(x, lo, hi, name):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not lo <= x <= hi:
        raise ValueError(f"{name}: oczekiwano liczby {lo}–{hi}, jest {x!r}")
    return float(x)


def _bool(x, name):
    if not isinstance(x, bool):
        raise ValueError(f"{name}: oczekiwano tak/nie")
    return x


def validate(d):
    """Pełne ustawienia (brakujące klucze = domyślne). Błąd → ValueError z opisem po polsku."""
    if not isinstance(d, dict):
        raise ValueError("ustawienia muszą być obiektem JSON")
    extra = set(d) - set(DEFAULTS)
    if extra:
        raise ValueError(f"nieznane ustawienia: {sorted(extra)}")
    s = copy.deepcopy(DEFAULTS)
    for k, (lo, hi) in NUM.items():
        if k in d:
            s[k] = _num(d[k], lo, hi, k)
    if "invert" in d:
        inv = d["invert"]
        if not isinstance(inv, dict) or set(inv) - set(s["invert"]):
            raise ValueError("invert: klucze lx, ly, rx, ry")
        s["invert"].update({k: _bool(v, f"invert.{k}") for k, v in inv.items()})
    for k in ("swap_triggers", "rumble"):
        if k in d:
            s[k] = _bool(d[k], k)
    if "gears" in d:
        g = d["gears"]
        if not (isinstance(g, list) and len(g) == 3 and all(isinstance(r, list) and len(r) == 2 for r in g)):
            raise ValueError("gears: 3 biegi po [rad/s, m/s]")
        s["gears"] = [[_num(r, *GEAR_RAD, f"bieg {i + 1} rad/s"), _num(m, *GEAR_M, f"bieg {i + 1} m/s")]
                      for i, (r, m) in enumerate(g)]
    if "start_gear" in d:
        if d["start_gear"] not in (1, 2, 3) or isinstance(d["start_gear"], bool):
            raise ValueError("start_gear: 1, 2 albo 3")
        s["start_gear"] = int(d["start_gear"])
    if "buttons" in d:
        b = d["buttons"]
        if not isinstance(b, dict) or set(b) - set(s["buttons"]):
            raise ValueError(f"buttons: dozwolone akcje {sorted(s['buttons'])}")
        s["buttons"].update(b)
        bad = [v for v in s["buttons"].values() if v not in BUTTONS]
        if bad:
            raise ValueError(f"buttons: nieznane przyciski {bad}")
        used = list(s["buttons"].values())
        dup = sorted({v for v in used if used.count(v) > 1})
        if dup:
            raise ValueError(f"buttons: przycisk przypisany do kilku akcji: {dup}")
    if "real_sign" in d:
        r = d["real_sign"]
        if not (isinstance(r, list) and len(r) == 5 and all(v in (1, -1) and not isinstance(v, bool) for v in r)):
            raise ValueError("real_sign: 5 wartości 1 albo −1")
        s["real_sign"] = [int(v) for v in r]
    if "real_grip_open" in d:
        if d["real_grip_open"] not in (0, 100) or isinstance(d["real_grip_open"], bool):
            raise ValueError("real_grip_open: 0 albo 100")
        s["real_grip_open"] = int(d["real_grip_open"])
    return s


def load():
    """Ustawienia z pliku; brak pliku → domyślne. Uszkodzony plik → ValueError (nie zgadujemy)."""
    if not os.path.exists(PATH):
        return copy.deepcopy(DEFAULTS)
    with open(PATH) as f:
        return validate(json.load(f))


def save(d):
    s = validate(d)
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f, indent=1)
    os.replace(tmp, PATH)                          # atomowo: run.py nigdy nie czyta pół pliku
    return s


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(PAGE, "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/settings":
            try:
                self._send(200, {"settings": load(), "defaults": DEFAULTS})
            except (ValueError, json.JSONDecodeError) as e:
                self._send(200, {"settings": DEFAULTS, "defaults": DEFAULTS, "warning": f"settings.json: {e}"})
        else:
            self._send(404, {"error": "brak"})

    def do_POST(self):
        # tylko ta strona może zapisywać: inna witryna nie wyśle JSON-a bez zgody CORS, a Origin musi być nasz
        origin = self.headers.get("Origin")
        if origin not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self._send(403, {"error": "obce źródło"})
        if self.path != "/api/settings" or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._send(400, {"error": "oczekiwano JSON na /api/settings"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 65536:
            return self._send(413, {"error": "za duże"})
        try:
            self._send(200, {"settings": save(json.loads(self.rfile.read(n)))})
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, {"error": str(e)})

    def log_message(self, *a):
        pass


def demo():
    s = validate({})
    assert s == DEFAULTS
    assert validate({"buttons": {"mode": "LEFTSTICK"}})["buttons"]["mode"] == "LEFTSTICK"
    for bad in ({"deadzone": 0.9}, {"buttons": {"mode": "A"}}, {"gears": [[9, 0.1]] * 3}, {"x": 1},
                {"real_sign": [1, 1, 1, 1, 0]}, {"rumble": "tak"}, {"deadzone": True}):
        try:
            validate(bad)
            raise AssertionError(f"przepuszczono {bad}")
        except ValueError:
            pass


if __name__ == "__main__":
    demo()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Ustawienia pada: {url}  (Ctrl+C kończy)")
    webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
