#!/bin/bash
cd /Users/admin/so101_fly_project
O=flymind/results/step3_20261115/loud_train; S=flymind/experiments/step3_wiring
run() { while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 2; done; "$@" & }
for g in 1 -1; do
  run sh -c ".venv/bin/python -I -B $S/reflex.py --net N --glu $g --seed 21401 --poses 3 --tag N_g$g --out $O > $O/N_g$g.log 2>&1"
  for x in F:21100001:F1 F:21100002:F2 L:21100006:L6 L:21100007:L7; do IFS=: read k s t <<< "$x"
    run sh -c ".venv/bin/python -I -B $S/loud.py reflex $O/calib_${k}_g$g.json --net $k --shuffle-seed $s --glu $g --seed 21401 --poses 3 --tag ${t}m_g$g --out $O > $O/${t}m_g$g.log 2>&1"
  done
done
wait
