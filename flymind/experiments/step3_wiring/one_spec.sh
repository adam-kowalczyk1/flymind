#!/bin/bash
cd /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/spec_test.py /Users/admin/so101_fly_project/flymind/results/step3_20261115/spec "$@" > /Users/admin/so101_fly_project/flymind/results/step3_20261115/spec/log_g$1_$2_$3_$4.txt 2>&1
