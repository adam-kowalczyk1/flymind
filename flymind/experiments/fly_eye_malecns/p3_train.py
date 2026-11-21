"""P3: flyvis train_single z opcjonalnym równoległym ładowaniem danych (P3_WORKERS > 0 → DataLoader num_workers).
Argumenty jak flyvis train_single (hydra)."""
import os
import runpy
import sys

import torch.utils.data as tud

W = int(os.environ.get("P3_WORKERS", "0"))
if W > 0:
    _init = tud.DataLoader.__init__

    def _patched(self, *a, **k):
        if not k.get("num_workers"):
            k.update(num_workers=W, persistent_workers=True)
        _init(self, *a, **k)

    tud.DataLoader.__init__ = _patched
F = "/Users/admin/so101_fly_project/envs/flyvis/lib/python3.12/site-packages/flyvis_cli/training/train_single.py"
sys.argv = [F, *sys.argv[1:]]
runpy.run_path(F, run_name="__main__")
