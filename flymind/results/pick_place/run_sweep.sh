#!/bin/bash
# Etap 1: porównanie wariantów prędkości/szczęki/pozy domowej na tych samych ziarnach (1–5, 50 cykli każde).
cd "$(dirname "$0")/../../.."
P=".venv/bin/python -I -B flymind/pick_place.py --seeds 1 2 3 4 5 --cycles 50"
HM="-0.065 -0.17 0.179 1.512 1.571 0.93"   # ik(cs_fixed → (0,22; 0; 0,10) m, oś w dół), szczęka 0,93
O=flymind/results/pick_place
$P --tag S0_baseline > $O/S0_baseline_stdout.txt 2>&1 &
$P --v 1.45 --a 8 --tag S1_v1.45 > $O/S1_v1.45_stdout.txt 2>&1 &
$P --v 1.45 --a 8 --q-pre 0.65 --tag S2_v1.45_jaw0.65 > $O/S2_v1.45_jaw0.65_stdout.txt 2>&1 &
$P --v 1.45 --a 8 --q-pre 0.65 --home $HM --tag S3_v1.45_jaw0.65_homemid > $O/S3_v1.45_jaw0.65_homemid_stdout.txt 2>&1 &
$P --q-pre 0.65 --home $HM --tag S4_v1.0_jaw0.65_homemid > $O/S4_v1.0_jaw0.65_homemid_stdout.txt 2>&1 &
wait
