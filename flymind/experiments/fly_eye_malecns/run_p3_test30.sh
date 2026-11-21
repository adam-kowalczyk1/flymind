#!/bin/bash
# P3: test 30 min na Macu (Adam 21 XI) — czy uczenie oka na połączeniach MaleCNS rusza: czas kroku, strata, pamięć.
# To NIE jest próba G0 z planu (50 000 kroków); twarde zatrzymanie po 40 min.
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=8
R=$PWD/flymind/results/fly_eye_malecns_20261120
/usr/bin/time -l perl -e 'alarm 2400; exec @ARGV' envs/flyvis/bin/python envs/flyvis/lib/python3.12/site-packages/flyvis_cli/training/train_single.py \
  ensemble_and_network_id=9100/000 task_name=p3_test30 train=true resume=false delete_if_exists=true description=p3_test30 \
  task.n_iters=4000 task.seed=24107000 \
  network.connectome.file=$R/malecns_flyvis.json network.connectome.n_syn_fill=0 \
  network.edge_config.syn_strength.scale=0.00507 > $R/p3_test30.log 2>&1
