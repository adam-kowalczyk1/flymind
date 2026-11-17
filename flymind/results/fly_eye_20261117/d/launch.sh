#!/bin/bash
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=data/flyvis
O=flymind/results/fly_eye_20261117/d
for r in 0-16 17-33 34-49; do
  envs/flyvis/bin/python -I flymind/experiments/fly_eye/d_ideal.py run flymind/results/v1_camera/bridge_b1/map_rot30.npz $r $O/d_$r.npz > $O/run_$r.log 2>&1 &
done
wait
echo DONE > $O/DONE
