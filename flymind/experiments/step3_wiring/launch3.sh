#!/bin/bash
# launch3.sh OUT VERSION SEED POSES LIFTMAX ARMS...   arms: N K R S<i> (free shuffle, seed BASE_S+i) L<i> (layer shuffle, seed BASE_L+i)
O=$1; V=$2; SEED=$3; POSES=$4; LM=$5; shift 5
cd /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
PY=/Users/admin/so101_fly_project/.venv/bin/python
J=/Users/admin/so101_fly_project/flymind/experiments/step3_wiring/run3.py
JA="--joints 1,2,3 --roll --inputs padsT2,padsT1 --in-rule fl --rule pre --lift-max $LM"
for spec in "$@"; do
  arm=${spec%%:*}; g=${spec##*:}
  case $arm in
    S*) A="--arm S --kind free --shuffle-seed $((BASE_S + ${arm#S}))";;
    L*) A="--arm S --kind layer --shuffle-seed $((BASE_L + ${arm#L}))";;
    *)  A="--arm $arm";;
  esac
  $PY -I -B $J $A --glu $g --seed $SEED --poses $POSES $JA --version $V --tag ${V}_${arm}_g$g --out $O > $O/${V}_${arm}_g$g.log 2>&1 &
done
wait
