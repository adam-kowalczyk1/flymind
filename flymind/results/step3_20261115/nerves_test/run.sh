#!/bin/bash
# TEST nerwów (LOOP_TARGET_nerves_r1.md) — RAZ; linie z jobs.txt, najwyżej 3 naraz, 6 póz
cd /Users/admin/so101_fly_project
O=flymind/results/step3_20261115/nerves_test
export NERVES_FINAL_TEST=1
while read -r L; do
  [ -z "$L" ] && continue
  set -- $L; T=${@: -1}
  while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 2; done
  .venv/bin/python -I -B flymind/experiments/step3_wiring/nerves_run.py "$@" --poses 6 --out $O > $O/$T.log 2>&1 &
done < $O/jobs.txt
wait
