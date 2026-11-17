#!/bin/bash
cd /Users/admin/so101_fly_project; export FLYVIS_ROOT_DIR=data/flyvis; PY="envs/flyvis/bin/python -I"
E=flymind/experiments/fly_eye; R=flymind/results/fly_eye_20261117/w7; B=flymind/results/v1_camera/bridge_b1
($PY $E/w7_run.py discs $B/map_rot30.npz 0-6 $R/discs_rot30_00-06.npz && $PY $E/w7_run.py cam $B/map_rot30.npz 0-19 flymind/results/fly_eye_20261116/w0 $R/cam_00-19.npz) > $R/run_a.log 2>&1 &
($PY $E/w7_run.py discs $B/map_rot30.npz 7-13 $R/discs_rot30_07-13.npz && $PY $E/w7_run.py discs $B/map_rot210.npz 0-2 $R/discs_rot210_00-02.npz) > $R/run_b.log 2>&1 &
($PY $E/w7_run.py discs $B/map_rot30.npz 14-19 $R/discs_rot30_14-19.npz && $PY $E/w7_run.py discs $B/map_rot210.npz 3-4 $R/discs_rot210_03-04.npz) > $R/run_c.log 2>&1 &
wait
