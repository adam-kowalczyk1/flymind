"""F1 manifest: sha256 of protocol, F1 code, frozen FlyMind dependencies and data files used. Writes manifest_<label>.json (mode "x").
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/manifest.py <label>"""
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OWN = ["PROTOCOL.md", "protocol.json", "SEED_REGISTRY.md", "stimulus.py", "systems.py", "runner.py", "analysis_core.py", "analysis.py",
       "manifest.py", "tests/test_f1.py", "tests/test_analysis.py", "integrity_pre_snapshot.json"]
DEPS = ["encoder.py", "alif.py", "visual_path.py", "loop.py", "so101.py", "block_shuffle.py", "side_shuffle.py", "sensory.py",
        "snn_interface.py", "connectome.py", "safety.py", "latency.py", "decoder.py", "v4_open_loop.py"]
DATA = ["body-annotations-male-cns-v1.0-minconf-0.5.feather", "body-neurotransmitters-male-cns-v1.0.feather",
        "connectome-weights-male-cns-v1.0-minconf-0.5.feather"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    label = sys.argv[1]
    own = OWN + [f for f in ("pilot_r1.json", "confirm_params.json", "figures.py") if os.path.exists(os.path.join(HERE, f))]
    sys.path.insert(0, os.path.join(ROOT, "flymind"))
    import latency  # noqa: E402
    m = dict(label=label, time=time.strftime("%Y-%m-%dT%H:%M:%S"),
             git_head=subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
             git_dirty_files=len(subprocess.run(["git", "-C", ROOT, "status", "--porcelain"], capture_output=True, text=True).stdout.splitlines()),
             sha256={f: sha(os.path.join(HERE, f)) for f in own},
             deps_sha256={f: sha(os.path.join(ROOT, "flymind", f)) for f in DEPS},
             data_sha256={f: sha(os.path.join(ROOT, "data", "malecns", f)) for f in DATA},
             env=latency.env_info(), python_flags=dict(isolated=sys.flags.isolated, dont_write_bytecode=sys.flags.dont_write_bytecode))
    p = os.path.join(HERE, f"manifest_{label}.json")
    with open(p, "x") as fh:
        json.dump(m, fh, indent=1, default=str)
    print(p, sha(p))
