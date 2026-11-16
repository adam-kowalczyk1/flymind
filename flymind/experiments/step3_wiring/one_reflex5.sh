#!/bin/bash
# one_reflex.sh OUT SEED POSES TAGPREFIX NET GLU [SHUFFLE_SEED]
cd /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
O=$1; SEED=$2; POSES=$3; PRE=$4; NET=$5; G=$6; SS=$7
if [ -n "$SS" ]; then A="--shuffle-seed $SS"; T="${PRE}_${NET}$((SS % 100))_g$G"; else A=""; T="${PRE}_N_g$G"; fi
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/reflex5.py --net $NET $A --glu $G --seed $SEED --poses $POSES --tag $T --out $O > $O/$T.log 2>&1
