"""Testy mutacyjne Etapu 1: czy testy wykrywają celowo zepsuty kod. Każda mutacja = zamiana JEDNEGO fragmentu w kopii
kodu w katalogu tymczasowym (repo nietknięte), potem test_pick_place_faults.py na tej kopii. „WYKRYTY” = test kończy się
błędem. Mutacje M* to pojedyncze zmiany BIEŻĄCEGO kodu — żadna nie jest kopią historycznej wersji pliku.

Uruchom (z katalogu tymczasowego):  .venv/bin/python -I -B flymind/results/pick_place/validation/mutate.py
Kod wyjścia 0 tylko, gdy wszystkie mutacje wykryte."""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 4))
S, P = "so101.py", "pick_place.py"
M = {
    # pomiar czasu
    "M1 reset() nie dolicza czasu sprzed resetu": (S, "        self.t_offset += d.time          # reset", "        pass  # reset"),
    "M2 auto-reset bez doliczenia czasu": (S, "                self.t_offset += t       # wykonany", "                pass  # wykonany"),
    "M3 auto-reset i BADQPOS/BADQVEL nie są błędem": (S, "        if bad or auto or not", "        if bad.get('BADQACC') or not"),
    "M4 start cyklu z d.time": (P, "s0, w0, a0 = sim.sim_time,", "s0, w0, a0 = sim.d.time,"),
    "M4b koniec cyklu z d.time": (P, "cycle_sim=sim.sim_time - s0", "cycle_sim=sim.d.time - s0"),
    "M6 podwójne liczenie przy resecie": (S, "        self.t_offset += d.time          # reset", "        self.t_offset += 2 * d.time          # reset"),
    "M9 auto-reset wykrywany tylko przez cofnięcie czasu": (S, "if d.time <= t or (t == 0.0 and warn()):", "if d.time < t:"),
    # kontrole cyklu
    "M7 zwolnienie bez kontroli dotyku": (P, "if max(self.obs.touch[:2]) > GripCfg().f_contact:", "if False:"),
    "M8 brak kontroli strefy odłożenia": (P, "if self.where() != dst:", "if False:"),
    # recovery i klasy błędów
    "M10 recover() zwraca True bez sprawdzenia stanu": (P, "        return self.not_ready() or True", "        return True"),
    "M11 not_ready() nie sprawdza szczęki": (P, "        if o.q[5] < c.q_clear:\n            return f\"jaw_not_open", "        if False:\n            return f\"jaw_not_open"),
    "M12 not_ready() nie sprawdza kostki": (P, "        if self.where() is None:\n            return f\"cube_lost", "        if False:\n            return f\"cube_lost"),
    "M13 recover() rusza ramię po kolizji / złej komendzie": (P, 'NO_MOTION = ("table_collision", "bad_command", "sim_error")', "NO_MOTION = ()"),
    "M14 recover() sam kasuje zatrzaśnięty błąd": (P, "            return f\"safety_latched: {self.safety.fault}\"\n        if self.sim.stopped or reason in NO_MOTION:",
                                                    "            self.safety.clear(\"auto\")\n        if self.sim.stopped or reason in NO_MOTION:"),
    "M15 seria nie staje po zatrzaśniętym błędzie": (P, "                if cell.safety.fault:\n", "                if False:\n"),
    "M16 reset sceny kasuje zatrzask (nowa SafetyLayer)": (P, "        self.safety.prev = None  ", "        self.safety = SafetyLayer(self.lim)  # "),
    "M17 zła komenda raportowana jako sim_error": (P, 'raise Fail("bad_command", str(e)) from e', 'raise Fail("sim_error", str(e)) from e'),
    "M18 _qd_prev nie odświeżany po resecie": (P, "        self._qd_prev = self.obs.qd[:5].copy()            # bez fałszywego", "        pass  # bez fałszywego"),
    # zapis wyników
    "M19 wyjątek nie oznacza serii jako przerwanej": (P, '            stopped_by = f"exception: {e!r}"', "            pass"),
    "M20 main() nie sprawdza, czy wynik już istnieje": (P, "    if any(os.path.exists(p) for p in paths): ", "    if False:  # "),
}


def main():
    tmp = tempfile.mkdtemp(prefix="pp_mut_")
    missed = []
    for name, (f, a, b) in M.items():
        d = os.path.join(tmp, "w")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(os.path.join(d, "flymind", "results", "pick_place"))
        for src in glob.glob(os.path.join(R, "flymind", "*.py")):
            shutil.copy(src, os.path.join(d, "flymind"))
        os.symlink(os.path.join(R, "assets"), os.path.join(d, "assets"))
        shutil.copy(os.path.join(R, "flymind", "results", "pick_place", "S0_baseline.json"),   # wzorzec dla testu P1.2
                    os.path.join(d, "flymind", "results", "pick_place"))
        p = os.path.join(d, "flymind", f)
        s = open(p).read()
        assert s.count(a) == 1, f"{name}: fragment występuje {s.count(a)}× w {f} — mutacja nieaktualna"
        open(p, "w").write(s.replace(a, b))
        r = subprocess.run([sys.executable, "-I", "-B", os.path.join(d, "flymind", "test_pick_place_faults.py")],
                           capture_output=True, text=True, cwd=tmp)
        last = ([x for x in (r.stdout + r.stderr).splitlines() if x.strip()] or [""])[-1]
        if not r.returncode:
            missed.append(name)
        print(f"{name}: {'WYKRYTY' if r.returncode else 'NIEWYKRYTY'} | {last[:140]}", flush=True)
    print(f"mutacje: {len(M)}, wykryte {len(M) - len(missed)}, niewykryte {len(missed)} {missed}")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
