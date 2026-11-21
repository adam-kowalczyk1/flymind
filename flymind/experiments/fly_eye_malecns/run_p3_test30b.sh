#!/bin/bash
# P3 test 2 (21 XI, Mac bez gry): 15 min jak test 1 (num_workers 0), potem 15 min z 4 wątkami danych.
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=8
R=$PWD/flymind/results/fly_eye_malecns_20261120
for w in 0 4; do
  P3_WORKERS=$w /usr/bin/time -l perl -e 'alarm 900; exec @ARGV' envs/flyvis/bin/python flymind/experiments/fly_eye_malecns/p3_train.py \
    ensemble_and_network_id=9100/00$w task_name=p3_test30 train=true resume=false delete_if_exists=true description=p3_test30b_w$w \
    task.n_iters=4000 task.seed=24107000 \
    network.connectome.file=$R/malecns_flyvis.json network.connectome.n_syn_fill=0 \
    network.edge_config.syn_strength.scale=0.00507 > $R/p3_test30b_w$w.log 2>&1
done
