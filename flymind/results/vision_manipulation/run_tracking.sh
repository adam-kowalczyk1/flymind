#!/bin/bash
# Testy śledzenia: trzy warunki równolegle, w katalogu tymczasowym. run_tracking.sh [sufiks=v1]
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
R="$(cd "$(dirname "$0")/../../.." && pwd)"; SUF="${1:-v1}"; O="$R/flymind/results/vision_manipulation"; cd "$(mktemp -d)"
for c in snn classical snn_swap; do
  "$R/.venv/bin/python" -I -B "$O/tracking.py" $c $SUF > "$O/tracking_${c}_${SUF}_stdout.txt" 2>&1 &
done
wait; cat "$O"/tracking_*_"$SUF"_stdout.txt
