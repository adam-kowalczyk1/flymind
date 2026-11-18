#!/bin/bash
cd /Users/admin/so101_fly_project
O=flymind/results/step3_20261115/loud_test; S=flymind/experiments/step3_wiring
run() { while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 2; done; "$@" & }
for sd in 21874 21875 21876; do for g in 1 -1; do
  run sh -c ".venv/bin/python -I -B $S/reflex.py --net N --glu $g --seed $sd --poses 6 --tag x${sd}_N_g$g --out $O > $O/x${sd}_N_g$g.log 2>&1"
  for i in 1 2 3 4 5; do
    run sh -c ".venv/bin/python -I -B $S/loud.py reflex $O/calib_F_g$g.json --net F --shuffle-seed 2187700$i --glu $g --seed $sd --poses 6 --tag x${sd}_F${i}_g$g --out $O > $O/x${sd}_F${i}_g$g.log 2>&1"
    run sh -c ".venv/bin/python -I -B $S/loud.py reflex $O/calib_L_g$g.json --net L --shuffle-seed 2187800$i --glu $g --seed $sd --poses 6 --tag x${sd}_L${i}_g$g --out $O > $O/x${sd}_L${i}_g$g.log 2>&1"
  done
done; done
wait
