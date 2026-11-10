#!/bin/bash
# Niezależna powtórka wycinka (6 przedmiotów × 3 położenia) trzech ramion + testy; wyniki porównuje repro_compare.py.
# Uruchamia się w katalogu tymczasowym (MuJoCo dopisuje tam MUJOCO_LOG.TXT). Tagi repro_check_* nie mogą już istnieć.
R="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$(mktemp -d)"; PY="$R/.venv/bin/python -I -B"
ONLY="cube_M/mid sphere/hard_slick long/heavy cyl/hard_grip cube_S/light wedge/mid"
$PY $R/flymind/sensory_manipulation.py --arm B_fly --trigger search --glu -1 --only $ONLY --tag repro_check_B_fly_search_v1 > repro_B.txt 2>&1 &
$PY $R/flymind/sensory_manipulation.py --arm C_fly_feco --trigger search --only $ONLY --tag repro_check_C_fly_feco_search_v1 > repro_C.txt 2>&1 &
$PY $R/flymind/object_handling.py single --set base --only $ONLY --tag repro_check_B_base_v2 > repro_A.txt 2>&1 &
$PY $R/flymind/test_sensory_manipulation.py > tests_sm.txt 2>&1 &
$PY $R/flymind/test_object_handling.py > tests_oh.txt 2>&1 &
wait
tail -3 tests_sm.txt tests_oh.txt; tail -2 repro_*.txt
$PY $R/flymind/results/sensory_manipulation/repro_compare.py $R/flymind/results/
