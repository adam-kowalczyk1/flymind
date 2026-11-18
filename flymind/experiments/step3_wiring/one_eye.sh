#!/bin/bash
# one_eye.sh OUT ARM PERC COLOUR   (test „oko złożone”; sceny --seed 21993; plik ARM_PERC_COLOUR.json)
mkdir -p /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj && cd /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
O=$1; ARM=$2; PERC=$3; COL=$4; T=${ARM}_${PERC}_${COL}
[ -e "$O/$T.json" ] && { echo "istnieje $O/$T.json"; exit 1; }
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/eye_bench.py --arm "$ARM" --perc "$PERC" --colour "$COL" --seed 21993 --tag "$T" --out "$O" > "$O/$T.log" 2>&1
