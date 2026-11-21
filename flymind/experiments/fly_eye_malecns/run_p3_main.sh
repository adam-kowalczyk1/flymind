#!/bin/bash
# P3 główne uczenie (PREREG_P3.md): 2 prawdziwe + 2 potasowane, 250 000 kroków, naraz. Wznowienie: RESUME=true ./run_p3_main.sh
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=2
R=$PWD/flymind/results/fly_eye_malecns_20261120
RES=${RESUME:-false}
for k in 0 1 2 3; do
  C=$R/malecns_flyvis.json; [ $k -ge 2 ] && C=$R/malecns_flyvis_shuf$((k-2)).json
  envs/flyvis/bin/python flymind/experiments/fly_eye_malecns/p3_train.py \
    ensemble_and_network_id=9200/00$k task_name=p3_malecns train=true resume=$RES delete_if_exists=false description=p3_main_$k \
    task.n_iters=250000 task.seed=$((24107000+k)) \
    network.connectome.file=$C network.connectome.n_syn_fill=0 \
    network.edge_config.syn_strength.scale=0.00507 >> $R/p3_main_$k.log 2>&1 &
done
wait
