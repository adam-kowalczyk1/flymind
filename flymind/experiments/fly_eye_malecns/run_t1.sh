#!/bin/bash
# T1: 4 procesy malecns + 2 shuffle; caffeinate, żeby Mac nie zasnął
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=2
R=flymind/results/fly_eye_malecns_20261120; P="envs/flyvis/bin/python flymind/experiments/fly_eye_malecns/t1_transplant.py"
$P malecns 0 12 $R/t1_malecns_a.json > $R/t1_a.log 2>&1 &
$P malecns 13 25 $R/t1_malecns_b.json > $R/t1_b.log 2>&1 &
$P malecns 26 37 $R/t1_malecns_c.json > $R/t1_c.log 2>&1 &
$P malecns 38 49 $R/t1_malecns_d.json > $R/t1_d.log 2>&1 &
$P shuffle 0 24 $R/t1_shuffle_a.json > $R/t1_sa.log 2>&1 &
$P shuffle 25 49 $R/t1_shuffle_b.json > $R/t1_sb.log 2>&1 &
wait
