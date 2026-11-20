#!/bin/bash
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=2
R=flymind/results/fly_eye_malecns_20261120; P="envs/flyvis/bin/python flymind/experiments/fly_eye_malecns/t1_transplant.py"
for a in "0 4 a" "5 9 b" "10 14 c" "15 19 d"; do set -- $a; $P shape $1 $2 $R/t1b_shape_$3.json > $R/t1b_$3.log 2>&1 & done
$P shape_shuffle 0 4 $R/t1b_shuf_a.json > $R/t1b_sa.log 2>&1 &
$P shape_shuffle 5 9 $R/t1b_shuf_b.json > $R/t1b_sb.log 2>&1 &
wait
