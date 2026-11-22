#!/bin/bash
# 22 XI: wstrzymaj modele 001–003 po zapisie chkpt_00005, potem uruchom kontrolę K0 (flyvis od zera). PREREG_P3.md.
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis
R=$PWD/flymind/results/fly_eye_malecns_20261120
for k in 1 2 3; do
  until [ -d data/flyvis/results/p3_malecns/9200/00$k/chkpts/chkpt_00005 ]; do sleep 30; done
  sleep 120                                   # zapis do końca
  pkill -f "ensemble_and_network_id=9200/00$k " && echo "$(date) wstrzymany 00$k po chkpt_00005" >> $R/p3_pause.log
done
OMP_NUM_THREADS=6 caffeinate -s -i envs/flyvis/bin/python flymind/experiments/fly_eye_malecns/p3_train.py \
  ensemble_and_network_id=9300/000 task_name=p3_ctrl train=true resume=false delete_if_exists=false description=p3_ctrl_flyvis \
  task.n_iters=250000 task.seed=24107010 >> $R/p3_ctrl.log 2>&1
