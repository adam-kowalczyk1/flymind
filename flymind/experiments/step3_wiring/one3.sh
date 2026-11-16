#!/bin/bash
# jedna seria testu: argumenty = opcje run3.py; ostatni argument = znacznik (--tag X)
cd /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad
export STEP3_FINAL_TEST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
for last; do :; done
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/run3.py --joints 1,2,3 --roll --inputs padsT2,padsT1 --in-rule fl --rule pre --lift-max 3 --seed 21201 --poses 3 --version arm3_test --out /Users/admin/so101_fly_project/flymind/results/step3_20261115/test "$@" > /Users/admin/so101_fly_project/flymind/results/step3_20261115/test/$last.log 2>&1
