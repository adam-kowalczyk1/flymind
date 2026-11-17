#!/bin/zsh
# G2-ALIF: dane + 40 tasowań, najwyżej 3 procesy naraz (flyvis innej sesji też liczy)
cd /Users/admin/so101_fly_project/flymind/results/fly_eye_20261116
PY="/Users/admin/so101_fly_project/.venv/bin/python -I -B"
G=/Users/admin/so101_fly_project/flymind/experiments/fly_eye/g2_alif.py
jobs_list=("data data_glu-1.npz")
for k in $(seq 1 40); do jobs_list+=("shuffle $((23503000+k)) $(printf shuf_%02d.npz $k)"); done
printf '%s\n' "${jobs_list[@]}" | xargs -P 3 -L 1 sh -c 'OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 '"$PY $G"' "$@" > "${@: -1}.log" 2>&1' _
echo KONIEC $(date)
