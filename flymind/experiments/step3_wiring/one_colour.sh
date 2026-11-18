#!/bin/bash
# one_colour.sh OUT ARM PERC COLOUR [ONLY...]   (benchmark kolor×położenie; sceny --seed 21991; plik ARM_PERC_COLOUR.json)
mkdir -p /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj && cd /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
O=$1; ARM=$2; PERC=$3; COL=$4; shift 4
T=${ARM}_${PERC}_${COL}
[ -e "$O/$T.json" ] && { echo "istnieje $O/$T.json"; exit 1; }
if [ $# -gt 0 ]; then ONLY="--only $*"; else ONLY=""; fi
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/colour_bench.py --arm $ARM --perc $PERC --colour $COL --seed 21991 $ONLY --tag $T --out $O > $O/$T.log 2>&1
