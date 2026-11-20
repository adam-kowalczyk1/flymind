#!/bin/bash
# T2c (PREREG_T2c.md): modele 003–008, napęd prawdziwy i potasowany, LPLC2 full (uprząż v2).
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=2
R=flymind/results/fly_eye_malecns_20261120; E=flymind/experiments/fly_eye_malecns; P=envs/flyvis/bin/python
for m in 3 4 5 6 7 8; do for w in real shuffle; do
  $P $E/t2_drive.py orig $w $m $R/t2_drive_${w}_$m.npz > $R/t2c_drive_${w}_$m.log 2>&1 &
done; [ $m = 5 ] && wait; done; wait
for g in "3 4 5" "6 7 8"; do for m in $g; do for w in real shuffle; do
  $P $E/t2_model.py $R/t2_drive_${w}_$m.npz LPLC2 full $R/t2c_LPLC2_full_${w}_$m.json > $R/t2c_model_${w}_$m.log 2>&1 &
done; done; wait; done
$P $E/t2c_eval.py > $R/t2c_eval.log 2>&1
