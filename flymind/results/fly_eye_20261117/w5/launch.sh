#!/bin/bash
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=data/flyvis
PY="envs/flyvis/bin/python -I"
E=flymind/experiments/fly_eye; R=flymind/results/fly_eye_20261117/w5; B=flymind/results/v1_camera/bridge_b1
($PY $E/w5_and.py discs $B/map_rot30.npz 20-29 $R/discs_rot30_20-29.npz && $PY $E/w5_and.py cam $B/map_rot30.npz 20-49 flymind/results/fly_eye_20261116/w0 $R/cam_20-49.npz) > $R/run_a.log 2>&1 &
($PY $E/w5_and.py discs $B/map_rot30.npz 30-39 $R/discs_rot30_30-39.npz && $PY $E/w5_and.py discs $B/map_rot210.npz 20-24 $R/discs_rot210_20-24.npz) > $R/run_b.log 2>&1 &
($PY $E/w5_and.py discs $B/map_rot30.npz 40-49 $R/discs_rot30_40-49.npz && $PY $E/w5_and.py discs $B/map_rot210.npz 25-29 $R/discs_rot210_25-29.npz) > $R/run_c.log 2>&1 &
wait
