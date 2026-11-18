#!/bin/bash
# jeden przebieg: nazwa + argumenty avoid.py; szum 2 mV, ziarno 21946002 wspólne dla wszystkich
cd /Users/admin/so101_fly_project/flymind/experiments/step3_wiring
D=../../results/step3_20261115/avoid_explore/r2
n=$1; shift
/Users/admin/so101_fly_project/.venv/bin/python avoid.py "$@" --noise 2 --noise-seed 21946002 --out $D/$n.json > $D/$n.log 2>&1
echo "done $n $?"
