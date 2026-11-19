#!/bin/bash
# test avoid r1: 3 tory równolegle (RAM ~7 GB na proces)
cd /Users/admin/so101_fly_project/flymind/experiments/step3_wiring
P=/Users/admin/so101_fly_project/.venv/bin/python
D=../../results/step3_20261115/avoid_r1/test
S=21949001,21949002,21949003,21949004,21949005
run() { n=$1; shift; $P avoid.py --noise 2 --out-dir $D --noise-seeds $S "$@" > $D/$n.log 2>&1; echo "$(date +%H:%M:%S) done $n $?" >> $D/progress.txt; }
( run N --glu -1 --net N --conds full,frozen,numb,blind,lesion --modes hw2p:palm:somato,sim3:palm:-,hw2:tips:somato
  run Ng1 --glu 1 --net N --conds full,frozen --modes hw2p:palm:somato ) &
( for s in 21949901 21949902; do run F$s --glu -1 --net F --shuffle-seed $s --conds full --modes hw2p:palm:somato,sim3:palm:-; done
  run L21949911 --glu -1 --net L --shuffle-seed 21949911 --conds full --modes hw2p:palm:somato,sim3:palm:- ) &
( for s in 21949903 21949904; do run F$s --glu -1 --net F --shuffle-seed $s --conds full --modes hw2p:palm:somato,sim3:palm:-; done
  run L21949912 --glu -1 --net L --shuffle-seed 21949912 --conds full --modes hw2p:palm:somato,sim3:palm:- ) &
wait
echo "$(date +%H:%M:%S) ALL DONE" >> $D/progress.txt
