#!/bin/bash
# Test „placebo”: fazy A (kalibracja) → B (P1 test + trening P2) → D (wybór P2) → E (P2 test). Glu +1, symulacja, 3 naraz.
cd /Users/admin/so101_fly_project
O=flymind/results/placebo_20261122; S=flymind/experiments/step3_wiring; PY=".venv/bin/python -I -B"
export OMP_NUM_THREADS=1
run() { while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 2; done; "$@" & }
fs=$(seq -f "27121%03g" 1 10); ls_=$(seq -f "27122%03g" 1 10)
[ -f $O/calib_F_g1.json ] || $PY $S/loud.py calib $O/calib_F_g1.json 1 F $fs > $O/calib_F.log 2>&1 &
[ -f $O/calib_L_g1.json ] || $PY $S/loud.py calib $O/calib_L_g1.json 1 L $ls_ > $O/calib_L.log 2>&1 &
wait
net() { # nazwa -> argumenty
  case $1 in N) echo "none|--net N";; F*) echo "$O/calib_F_g1.json|--net F --shuffle-seed 27121$(printf %03d $((10#${1:1})))";;
             L*) echo "$O/calib_L_g1.json|--net L --shuffle-seed 27122$(printf %03d $((10#${1:1})))";; esac; }
job() { # nazwa m scena poses prefix outdir
  local a=$(net $1); local c=${a%%|*}; local r=${a#*|}; local tag=$5_$1_m$2
  [ -f $6/$tag.json ] && return
  run sh -c "nice -n 10 $PY $S/placebo.py $c $2 $r --glu 1 --seed $3 --poses $4 --tag $tag --out $6 > $6/$tag.log 2>&1"
}
ALL="N $(seq -f 'F%02g' 1 10) $(seq -f 'L%02g' 1 10)"
P2="N $(seq -f 'F%02g' 1 6) $(seq -f 'L%02g' 1 6)"
for n in $ALL; do for sd in 27111 27112 27113; do job $n 1.0 $sd 6 $sd $O/test; done; done
for n in $P2; do for m in 0.6 0.8 1.0 1.25 1.6; do job $n $m 27131 4 tr $O/train; done; done
wait
$PY $S/analyze_placebo.py select $O/train $O/select_p2.json
for n in $P2; do m=$($PY -c "import json;print(json.load(open('$O/select_p2.json'))['$n']['m'])"); for sd in 27111 27112 27113; do job $n $m $sd 6 $sd $O/test; done; done
wait
$PY $S/analyze_placebo.py test $O/test $O/select_p2.json $O/analysis_placebo.json > $O/analysis_placebo.log 2>&1
echo KONIEC > $O/DONE
