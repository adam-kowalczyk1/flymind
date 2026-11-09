"""Uruchamia skrypt testowy z INNĄ wersją so101.py (np. zamrożoną sprzed Etapu 1); reszta kodu bieżąca.
Użycie (z katalogu tymczasowego):  .venv/bin/python -I -B with_so101.py <so101.py> <test.py>
Podmiana tylko w pamięci tego procesu (kopia w katalogu tymczasowym, assets jako dowiązanie) — repo bez zmian."""
import importlib.util
import os
import runpy
import shutil
import sys
import tempfile

old, test = (os.path.abspath(p) for p in sys.argv[1:3])
R = os.path.dirname(os.path.dirname(os.path.abspath(test)))
while not os.path.isdir(os.path.join(R, "assets")):
    R = os.path.dirname(R)
d = tempfile.mkdtemp(prefix="so101_other_")
os.makedirs(os.path.join(d, "flymind"))
shutil.copy(old, os.path.join(d, "flymind", "so101.py"))
os.symlink(os.path.join(R, "assets"), os.path.join(d, "assets"))
sys.path.insert(0, os.path.join(R, "flymind"))
spec = importlib.util.spec_from_file_location("so101", os.path.join(d, "flymind", "so101.py"))
m = importlib.util.module_from_spec(spec)
sys.modules["so101"] = m
spec.loader.exec_module(m)
sys.argv = [test]
runpy.run_path(test, run_name="__main__")
