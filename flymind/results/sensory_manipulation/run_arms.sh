#!/bin/bash
# Etap „czucie i manipulacja”: wszystkie ramiona na zestawie podstawowym (45 przedmiotów × 3 pozy), równolegle.
#   run_arms.sh [sufiks=v1]     wyniki i logi tylko w flymind/results/sensory_manipulation/
# Czasy obliczeń w tych plikach są mierzone POD OBCIĄŻENIEM (procesy równoległe) — do raportu służy osobny przebieg
# latency_<sufiks> wykonany na końcu pojedynczo.
set -u -o noclobber
R="$(cd "$(dirname "$0")/../../.." && pwd)"; SUF="${1:-v1}"
O="$R/flymind/results/sensory_manipulation"; LOG="$O/run_$SUF.log"; FRZ="$O/FREEZE_$SUF.txt"
PY="$R/.venv/bin/python"; P="$PY -I -B $R/flymind/sensory_manipulation.py"
TAGS=(N_null_search D_reflex_search B_fly_search_glu-1 B_fly_search_glu+1 C_fly_feco_search C_no_touch_search
      S_shuffle1_search S_shuffle2_search S_shuffle3_search B_fly_push D_reflex_push)
ARGS=("--arm N_null --trigger search" "--arm D_reflex --trigger search" "--arm B_fly --trigger search --glu -1"
      "--arm B_fly --trigger search --glu 1" "--arm C_fly_feco --trigger search" "--arm C_no_touch --trigger search"
      "--arm S_shuffle --trigger search --shuffle-seed 17100001" "--arm S_shuffle --trigger search --shuffle-seed 17100002"
      "--arm S_shuffle --trigger search --shuffle-seed 17100003" "--arm B_fly --trigger push" "--arm D_reflex --trigger push")
for f in "$LOG" "$FRZ"; do [ -e "$f" ] && { echo "istnieje $f — wybierz inny sufiks"; exit 2; }; done
for t in "${TAGS[@]}" latency; do [ -e "$O/${t}_$SUF.json" ] && { echo "istnieje ${t}_$SUF.json"; exit 2; }; done
CODE="flymind/sensory_manipulation.py flymind/object_handling.py flymind/fly_jaw.py flymind/leg_circuit.py flymind/alif.py flymind/alif_sparse.py flymind/snn_interface.py flymind/visual_path.py flymind/connectome.py flymind/pick_place.py flymind/so101.py flymind/reach.py flymind/grip.py flymind/safety.py assets/so101_upstream.xml data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather data/malecns/body-neurotransmitters-male-cns-v1.0.feather data/malecns/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
(cd "$R" && shasum -a 256 -c flymind/results/pick_place/validation/historical_sha256.txt > /dev/null) || { echo "Etap 1 ≠ manifest — stop"; exit 3; }
{ echo "# Zamrożenie przed przebiegiem ramion ($SUF)"; echo "data: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "commit odniesienia (HEAD): $(git -C "$R" rev-parse HEAD) ($(git -C "$R" branch --show-current))"
  echo "sha256:"; (cd "$R" && shasum -a 256 $CODE | sed 's/^/  /'); } > "$FRZ"
TMP="$(mktemp -d)"; cd "$TMP"; cat "$FRZ" > "$LOG"; echo "katalog roboczy: $TMP" >> "$LOG"
pids=()
for i in "${!TAGS[@]}"; do
  t="${TAGS[$i]}_$SUF"; echo "\$ sensory_manipulation.py ${ARGS[$i]} --tag $t" >> "$LOG"
  $P ${ARGS[$i]} --tag "$t" > "$O/${t}_stdout.txt" 2>&1 & pids+=($!)
done
for i in "${!TAGS[@]}"; do wait "${pids[$i]}"; echo "kod wyjścia ${TAGS[$i]}_$SUF: $?" >> "$LOG"; done
echo "\$ sensory_manipulation.py --arm C_fly_feco --trigger search --tag latency_$SUF   (pojedynczo, bez innych procesów)" >> "$LOG"
$P --arm C_fly_feco --trigger search --only cube_M/mid sphere/mid long/mid cyl/mid cube_S/mid --tag "latency_$SUF" > "$O/latency_${SUF}_stdout.txt" 2>&1
echo "kod wyjścia latency_$SUF: $?" >> "$LOG"
{ echo "data końca: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "MUJOCO_LOG.TXT w katalogu roboczym: $([ -f MUJOCO_LOG.TXT ] && grep -c WARNING MUJOCO_LOG.TXT || echo 0) ostrzeżeń"
  echo "kod po przebiegu: $(cd "$R" && shasum -a 256 $CODE | sed 's/^/  /' | diff - <(grep '^  ' "$FRZ") > /dev/null && echo IDENTYCZNY || echo RÓŻNY)"
  echo "Etap 1 (17 plików historycznych) OK: $(cd "$R" && shasum -a 256 -c flymind/results/pick_place/validation/historical_sha256.txt 2>/dev/null | grep -c ': OK$')"
  echo "## sha256 wyników:"; (cd "$R" && shasum -a 256 flymind/results/sensory_manipulation/*_"$SUF".json | sed 's/^/  /'); } >> "$LOG" 2>&1
tail -22 "$LOG"
