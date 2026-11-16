#!/bin/bash
# one_dose.sh GLU FAMILY FIRST LAST — jedno zadanie testu dawki (xargs -L 1)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
H=/Users/admin/so101_fly_project/flymind
O=$H/results/step3_20261115/dose
/Users/admin/so101_fly_project/.venv/bin/python -I -B $H/experiments/step3_wiring/dose_test.py $O $1 $2 $3 $4 > $O/dose_g$1_$2_$3_$4.log 2>&1
