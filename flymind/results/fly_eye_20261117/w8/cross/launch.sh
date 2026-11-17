#!/bin/bash
cd /Users/admin/so101_fly_project; export FLYVIS_ROOT_DIR=data/flyvis; PY="envs/flyvis/bin/python -I"
E=flymind/experiments/fly_eye; R=flymind/results/fly_eye_20261117/w8/cross; B=flymind/results/v1_camera/bridge_b1/map_rot30.npz; W=flymind/results/fly_eye_20261117/w8/w0c
$PY $E/w7_run.py cam $B 0-19 $W/hard_slick $R/al_hard_slick_m00-19.npz > $R/run_a.log 2>&1 &
$PY $E/w7_run.py cam $B 0-19 $W/mid $R/al_mid_m00-19.npz > $R/run_b.log 2>&1 &
$PY $E/w7_run.py cam $B 20-49 flymind/results/fly_eye_20261116/w0 $R/al_W0_m20-49.npz > $R/run_c.log 2>&1 &
wait
