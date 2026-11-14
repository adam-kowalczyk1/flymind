#!/bin/bash
# Audyt FeCO + audyt kontaktu: wszystkie warianty równolegle, w katalogu tymczasowym. run_all.sh [sufiks=v1]
R="$(cd "$(dirname "$0")/../../.." && pwd)"; SUF="${1:-v1}"; PY="$R/.venv/bin/python -I -B"; cd "$(mktemp -d)"
F="$R/flymind/results/feco_audit"; C="$R/flymind/results/contact_audit"
(cd "$R" && shasum -a 256 flymind/sensory_manipulation.py flymind/object_handling.py flymind/fly_jaw.py flymind/leg_circuit.py "$F/feco_audit.py" "$C/contact_audit.py") > "$F/FREEZE_$SUF.txt"
for v in scale_0.25 scale_0.5 claw_only hook_only swap; do $PY "$F/feco_audit.py" $v $SUF > "$F/${v}_${SUF}_stdout.txt" 2>&1 & done
for a in A B; do $PY "$C/contact_audit.py" $a $SUF > "$C/stiff_${a}_${SUF}_stdout.txt" 2>&1 & done
wait; cat "$F"/*_"$SUF"_stdout.txt "$C"/*_"$SUF"_stdout.txt
(cd "$R" && shasum -a 256 -c flymind/results/pick_place/validation/historical_sha256.txt 2>/dev/null | grep -c ': OK$')
