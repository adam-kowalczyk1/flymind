#!/bin/bash
cd /private/tmp/claude-501/-Users-admin--claude-spares-spare-6yVq0X/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
PY=/Users/admin/so101_fly_project/.venv/bin/python
J=/Users/admin/so101_fly_project/flymind/experiments/step2_whole_arm/joint_net.py
for L in 3 10; do
  $PY -I -B $J --arm N --glu 1 --seed 20953 --poses 1 --joints 2 --inputs padsT2,padsT1 --in-rule fl --lift-max $L --version c_diag --tag c_diag_N_g1_liftmax$L --out /Users/admin/so101_fly_project/flymind/results/verification_step2_20261114/elbow_diag > /Users/admin/so101_fly_project/flymind/results/verification_step2_20261114/elbow_diag/c_diag_N_g1_liftmax$L.log 2>&1 &
done
wait
