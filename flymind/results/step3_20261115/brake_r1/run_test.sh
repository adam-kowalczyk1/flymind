#!/bin/sh
# Test „hamulec” r1 — uruchamiać RAZ, po zapisaniu PRE_TEST_HASH.txt. Ziarna 21 954 001–005.
cd "$(dirname "$0")/../../../experiments/step3_wiring" || exit 1
PY=/Users/admin/so101_fly_project/.venv/bin/python
T=../../results/step3_20261115/brake_r1
S=21954001,21954002,21954003,21954004,21954005
( $PY diag_vision.py --out $T/raw --tag N --conds full --seeds $S && \
  $PY diag_vision.py --out $T/raw --tag S --silence $T/silence_S.json --conds full,numb --seeds $S ) > $T/run_a.log 2>&1 &
( for k in 1 2 3; do $PY diag_vision.py --out $T/raw --tag C$k --silence $T/silence_C$k.json --conds full --seeds $S; done ) > $T/run_b.log 2>&1 &
wait
$PY analyze_diag.py $T/raw --brake > $T/analysis.json
