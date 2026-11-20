#!/bin/bash
# T2 v2 (PREREG_T2.md): T1 i T1b FAILED → liczby oka flyvis ("orig"), hybryda. Napęd → warstwa komórek zbliżania.
cd /Users/admin/so101_fly_project
export FLYVIS_ROOT_DIR=$PWD/data/flyvis OMP_NUM_THREADS=2
R=flymind/results/fly_eye_malecns_20261120; E=flymind/experiments/fly_eye_malecns; P=envs/flyvis/bin/python
for m in 0 1 2; do (
  $P $E/t2_model.py $R/t2_drive_real_$m.npz LPLC2 full $R/v2_LPLC2_full_real_$m.json
  $P $E/t2_model.py $R/t2_drive_shuffle_$m.npz LPLC2 full $R/v2_LPLC2_full_shuffle_$m.json
  $P $E/t2_model.py $R/t2_drive_real_$m.npz LPLC2 nolpi $R/v2_LPLC2_nolpi_real_$m.json
  $P $E/t2_model.py $R/t2_drive_real_$m.npz LPLC2 untrained $R/v2_LPLC2_untrained_real_$m.json
  $P $E/t2_model.py $R/t2_drive_real_$m.npz LC4 full $R/v2_LC4_full_real_$m.json
) > $R/v2_model_$m.log 2>&1 & done; wait
