#!/bin/bash
# linie z jobs.txt, najwyżej 3 naraz; sceny treningowe etapu 1 (21421, 3 pozy)
cd /Users/admin/so101_fly_project
O=${O:-flymind/results/step3_20261115/nerves_train}; SEED=${SEED:-21421}; POSES=${POSES:-3}
while read -r L; do
  [ -z "$L" ] && continue
  set -- $L; T=${@: -1}
  while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 2; done
  .venv/bin/python -I -B flymind/experiments/step3_wiring/nerves_run.py "$@" --seed $SEED --poses $POSES --out $O > $O/$T.log 2>&1 &
done < $O/jobs.txt
wait
