#!/bin/bash
cd /Users/admin/so101_fly_project; export FLYVIS_ROOT_DIR=data/flyvis; PY="envs/flyvis/bin/python -I"; E=flymind/experiments/fly_eye; R=flymind/results/fly_eye_20261117/w6
$PY $E/w6_gate.py 0-16 $R/gate_00-16.json > $R/gate_a.log 2>&1 &
$PY $E/w6_gate.py 17-33 $R/gate_17-33.json > $R/gate_b.log 2>&1 &
$PY $E/w6_gate.py 34-49 $R/gate_34-49.json > $R/gate_c.log 2>&1 &
wait
