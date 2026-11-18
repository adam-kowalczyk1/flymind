#!/bin/bash
# Etap „wzrok w pętli”: wszystkie ramiona na zestawie podstawowym (45 przedmiotów × 3 położenia), równolegle.
#   run_arms.sh [sufiks=v1]    wyniki i logi tylko w flymind/results/vision_manipulation/
# Czasy obliczeń w tych plikach są mierzone POD OBCIĄŻENIEM (procesy równoległe); do raportu służy osobny przebieg latency_<sufiks>.
set -u -o noclobber
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
R="$(cd "$(dirname "$0")/../../.." && pwd)"; SUF="${1:-v1}"
O="$R/flymind/results/vision_manipulation"; LOG="$O/run_$SUF.log"; FRZ="$O/FREEZE_$SUF.txt"
PY="$R/.venv/bin/python -I -B"; P="$PY $R/flymind/vision_manipulation.py bench"
ARMS="A_cam B_cam D_vis E_vis_touch E_blind_grasp F_vis_touch_feco"
for f in "$LOG" "$FRZ"; do [ -e "$f" ] && { echo "istnieje $f — wybierz inny sufiks"; exit 2; }; done
for a in $ARMS latency; do [ -e "$O/${a}_$SUF.json" ] && { echo "istnieje ${a}_$SUF.json"; exit 2; }; done
CODE="flymind/vision_manipulation.py flymind/test_vision_manipulation.py flymind/sensory_manipulation.py flymind/object_handling.py flymind/fly_jaw.py flymind/leg_circuit.py flymind/visual_path.py flymind/encoder.py flymind/decoder.py flymind/sensory.py flymind/alif.py flymind/alif_sparse.py flymind/snn_interface.py flymind/connectome.py flymind/pick_place.py flymind/so101.py flymind/reach.py flymind/grip.py flymind/safety.py assets/so101_upstream.xml data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather data/malecns/body-neurotransmitters-male-cns-v1.0.feather data/malecns/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
(cd "$R" && shasum -a 256 -c flymind/results/pick_place/validation/historical_sha256.txt > /dev/null) || { echo "Etap 1 ≠ manifest — stop"; exit 3; }
{ echo "# Zamrożenie przed przebiegiem ramion ($SUF)"; echo "data: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "HEAD: $(git -C "$R" rev-parse HEAD) ($(git -C "$R" branch --show-current))"
  echo "sha256:"; (cd "$R" && shasum -a 256 $CODE | sed 's/^/  /'); } > "$FRZ"
TMP="$(mktemp -d)"; cd "$TMP"; cat "$FRZ" > "$LOG"; echo "katalog roboczy: $TMP" >> "$LOG"
$PY "$R/flymind/test_vision_manipulation.py" > "$O/tests_$SUF.log" 2>&1; echo "testy: kod wyjścia $?" >> "$LOG"
pids=()
for a in $ARMS; do
  echo "\$ vision_manipulation.py bench --arm $a --tag ${a}_$SUF" >> "$LOG"
  $P --arm $a --tag "${a}_$SUF" > "$O/${a}_${SUF}_stdout.txt" 2>&1 & pids+=($!)
done
i=0; for a in $ARMS; do wait "${pids[$i]}"; echo "kod wyjścia ${a}_$SUF: $?" >> "$LOG"; i=$((i+1)); done
echo "\$ vision_manipulation.py bench --arm F_vis_touch_feco --only … --tag latency_$SUF   (pojedynczo, bez innych procesów)" >> "$LOG"
$P --arm F_vis_touch_feco --only cube_M/mid sphere/mid long/mid cyl/mid cube_S/mid --tag "latency_$SUF" > "$O/latency_${SUF}_stdout.txt" 2>&1
echo "kod wyjścia latency_$SUF: $?" >> "$LOG"
{ echo "data końca: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "kod po przebiegu: $(cd "$R" && shasum -a 256 $CODE | sed 's/^/  /' | diff - <(grep '^  ' "$FRZ") > /dev/null && echo IDENTYCZNY || echo RÓŻNY)"
  echo "Etap 1 (17 plików historycznych) OK: $(cd "$R" && shasum -a 256 -c flymind/results/pick_place/validation/historical_sha256.txt 2>/dev/null | grep -c ': OK$')"
  echo "## sha256 wyników:"; (cd "$R" && shasum -a 256 flymind/results/vision_manipulation/*_"$SUF".json | sed 's/^/  /'); } >> "$LOG" 2>&1
tail -14 "$LOG"
