#!/bin/bash
cd /Users/admin/so101_fly_project; export FLYVIS_ROOT_DIR=data/flyvis; PY="envs/flyvis/bin/python -I"
E=flymind/experiments/fly_eye; R=flymind/results/fly_eye_20261117/w8; B=flymind/results/v1_camera/bridge_b1/map_rot30.npz
$PY $E/w7_run.py cam $B 20-49 $R/w0c/hard_slick $R/al_hard_slick.npz > $R/run_a.log 2>&1 &
$PY $E/w7_run.py cam $B 20-49 $R/w0c/mid $R/al_mid.npz > $R/run_b.log 2>&1 &
($PY $E/w5_and.py cam $B 20-49 $R/w0c/hard_slick $R/id_hard_slick.npz && $PY $E/w5_and.py cam $B 20-49 $R/w0c/mid $R/id_mid.npz) > $R/run_c.log 2>&1 &
wait
