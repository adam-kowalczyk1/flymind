#!/bin/bash
# 10 przetasowanych sieci z wyrównaną siłą, równolegle, w katalogu tymczasowym. run_all.sh [sufiks=v1]
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
R="$(cd "$(dirname "$0")/../../.." && pwd)"; SUF="${1:-v1}"; O="$R/flymind/results/shuffle_matched"; cd "$(mktemp -d)"
(cd "$R" && shasum -a 256 flymind/sensory_manipulation.py flymind/object_handling.py flymind/fly_jaw.py flymind/leg_circuit.py flymind/visual_path.py "$O/shuffle_matched.py") > "$O/FREEZE_$SUF.txt"
for i in $(seq 11 20); do s=$((17100000+i)); "$R/.venv/bin/python" -I -B "$O/shuffle_matched.py" $s $SUF > "$O/shuffle_${s}_${SUF}_stdout.txt" 2>&1 & done
wait; cat "$O"/shuffle_*_"$SUF"_stdout.txt
