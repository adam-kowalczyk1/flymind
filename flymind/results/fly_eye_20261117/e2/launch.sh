#!/bin/bash
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=data/flyvis
E=flymind/results/fly_eye_20261117/e2
S="w0d=$E/w0d/heavy hard_slick=flymind/results/fly_eye_20261117/w8/w0c/hard_slick mid=flymind/results/fly_eye_20261117/w8/w0c/mid"
for r in 0-16 17-33 34-49; do
  envs/flyvis/bin/python -I flymind/experiments/fly_eye/e2_lpi.py flymind/results/v1_camera/bridge_b1/map_rot30.npz $r $E $S > $E/run_$r.log 2>&1 &
done
wait
echo DONE > $E/DONE
