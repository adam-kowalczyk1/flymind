#!/bin/bash
# one_reflex_r2.sh OUT SEED NET GLU [SHUFFLE_SEED]   (krok 4 r2; 6 póz; pliki x{SEED}_{NET}{SS%100}_g{GLU})
mkdir -p /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj && cd /private/tmp/claude-501/-Users-admin--claude-spares-spare-TxLTiM/c4a3802b-e574-4d1b-a065-a1c25c934953/scratchpad/mj
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
O=$1; SEED=$2; NET=$3; G=$4; SS=$5
if [ -n "$SS" ]; then A="--shuffle-seed $SS"; T="x${SEED}_${NET}$((SS % 100))_g$G"; else A=""; T="x${SEED}_N_g$G"; fi
[ -e "$O/$T.json" ] && { echo "istnieje $O/$T.json"; exit 1; }
/Users/admin/so101_fly_project/.venv/bin/python -I -B /Users/admin/so101_fly_project/flymind/experiments/step3_wiring/reflex.py --net $NET $A --glu $G --seed $SEED --poses 6 --tag $T --out $O > $O/$T.log 2>&1
