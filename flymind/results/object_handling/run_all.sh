#!/bin/bash
# Benchmark obsługi przedmiotów — pełny przebieg z trwałym logiem. Wyniki tylko w flymind/results/object_handling/.
#   run_all.sh [sufiks=v1]
# Kolejność: zamrożenie (skróty kodu) → testy (Etap A) → B pojedyncze przedmioty → C serie mieszane → D zestaw trudny
# → seria nagrana (klatki do katalogu tymczasowego, film do media/) → kontrola integralności Etapu 1.
# Wszystko uruchamiane z katalogu tymczasowego (MuJoCo dopisuje ostrzeżenia do ./MUJOCO_LOG.TXT). Niczego nie nadpisuje:
# object_handling.py odmawia zapisu, gdy tag istnieje; ten skrypt sprawdza to przed startem i ma noclobber.
set -u -o noclobber
R="$(cd "$(dirname "$0")/../../.." && pwd)"
SUF="${1:-v1}"
O="$R/flymind/results/object_handling"; LOG="$O/run_$SUF.log"; FRZ="$O/FREEZE_$SUF.txt"
PY="$R/.venv/bin/python"; P="$PY -I -B $R/flymind/object_handling.py"
S1="$R/flymind/results/pick_place"
TAGS=(B_base C_mixed D_hard D_hard_series C_perm1_recorded)
ARGS=("single --set base --poses 3 --seed 100" "series --set base --perm 1 2 --n 9"
      "single --set hard --poses 3 --seed 200" "series --set hard --perm 1 --n 8" "series --set base --perm 1 --n 9")
for t in "${TAGS[@]}"; do
  for f in "$O/${t}_$SUF.json" "$O/${t}_$SUF.INCOMPLETE.json" "$O/${t}_${SUF}_stdout.txt"; do
    [ -e "$f" ] && { echo "istnieje $f — wybierz inny sufiks"; exit 2; }
  done
done
for f in "$LOG" "$FRZ" "$O/tests_$SUF.log" "$O/stage1_sha256_before_$SUF.txt" "$O/media/C_perm1_series0_$SUF.mp4"; do
  [ -e "$f" ] && { echo "istnieje $f — wybierz inny sufiks"; exit 2; }
done
CODE="flymind/object_handling.py flymind/test_object_handling.py flymind/pick_place.py flymind/so101.py flymind/reach.py flymind/grip.py flymind/safety.py assets/so101_upstream.xml"
(cd "$R" && shasum -a 256 -c "$S1/validation/historical_sha256.txt" > /dev/null) || { echo "Etap 1: historyczne wyniki ≠ manifest — stop"; exit 3; }
(cd "$R" && git ls-files flymind/results/pick_place | xargs shasum -a 256) > "$O/stage1_sha256_before_$SUF.txt"
{
  echo "# Zamrożenie kodu przed pomiarami ($SUF)"
  echo "data: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "commit odniesienia (HEAD): $(git -C "$R" rev-parse HEAD) ($(git -C "$R" branch --show-current))"
  echo "sha256:"; (cd "$R" && shasum -a 256 $CODE | sed 's/^/  /')
  echo "python $("$PY" -c 'import sys; print(sys.version.split()[0])'), mujoco $("$PY" -c 'import mujoco; print(mujoco.__version__)'), numpy $("$PY" -c 'import numpy; print(numpy.__version__)')"
} > "$FRZ"
TMP="$(mktemp -d)"; cd "$TMP"
{ cat "$FRZ"; echo "katalog roboczy: $TMP"; echo "MUJOCO_LOG.TXT repo przed: $(shasum -a 256 "$R/MUJOCO_LOG.TXT" 2>/dev/null | cut -c1-64)"; echo; } > "$LOG"
echo "\$ .venv/bin/python -I -B flymind/test_object_handling.py" >> "$LOG"
$PY -I -B "$R/flymind/test_object_handling.py" > "$O/tests_$SUF.log" 2>&1; rc=$?
echo "kod wyjścia testów: $rc ($(grep -c ': OK' "$O/tests_$SUF.log") testów OK)" >> "$LOG"
[ $rc -eq 0 ] || { echo "testy nie przeszły — pomiarów nie uruchamiam" | tee -a "$LOG"; exit 4; }
fail=0
for i in "${!TAGS[@]}"; do
  t="${TAGS[$i]}_$SUF"; extra=""
  [ "${TAGS[$i]}" = C_perm1_recorded ] && extra="--record $TMP/frames"
  echo "\$ .venv/bin/python -I -B flymind/object_handling.py ${ARGS[$i]} $extra --tag $t   [start $(date '+%H:%M:%S')]" >> "$LOG"
  $P ${ARGS[$i]} $extra --tag "$t" > "$O/${t}_stdout.txt" 2>&1; rc=$?
  echo "kod wyjścia $t: $rc" >> "$LOG"
  [ $rc -eq 0 ] || fail=$((fail+1))
done
/Users/admin/miniforge3/bin/ffmpeg -loglevel error -framerate 25 -i "$TMP/frames/f%05d.png" -pix_fmt yuv420p "$O/media/C_perm1_series0_$SUF.mp4" >> "$LOG" 2>&1
{
  echo "klatek nagranych: $(ls "$TMP/frames" | wc -l | tr -d ' ') (co 40 ms symulacji → film 25 kl./s = czas symulacji 1:1)"
  echo "data końca: $(date '+%Y-%m-%d %H:%M:%S %z'); serie z kodem ≠ 0 (niekompletne): $fail"
  echo "MUJOCO_LOG.TXT w katalogu roboczym: $([ -f MUJOCO_LOG.TXT ] && grep -c WARNING MUJOCO_LOG.TXT || echo 0) ostrzeżeń"
  echo "MUJOCO_LOG.TXT repo po:    $(shasum -a 256 "$R/MUJOCO_LOG.TXT" 2>/dev/null | cut -c1-64)"
  echo; echo "## kod po przebiegu względem zamrożenia:"
  (cd "$R" && shasum -a 256 $CODE | sed 's/^/  /' | diff - <(grep '^  ' "$FRZ" | head -8) > /dev/null && echo "  IDENTYCZNY" || echo "  RÓŻNY")
  echo "## Etap 1 po przebiegu: manifest historyczny (17 plików) i wszystkie śledzone pliki results/pick_place:"
  (cd "$R" && shasum -a 256 -c "$S1/validation/historical_sha256.txt" 2>&1 | tail -1 | sed 's/^/  ostatni: /'; shasum -a 256 -c "$S1/validation/historical_sha256.txt" 2>/dev/null | grep -c ': OK$' | sed 's/^/  OK: /')
  (cd "$R" && shasum -a 256 -c "$O/stage1_sha256_before_$SUF.txt" 2>/dev/null | grep -vc ': OK$' | sed 's/^/  pliki Etapu 1 zmienione: /')
  echo "## sha256 nowych wyników:"; (cd "$R" && shasum -a 256 flymind/results/object_handling/*_"$SUF".json flymind/results/object_handling/media/*_"$SUF".mp4 2>/dev/null | sed 's/^/  /')
} >> "$LOG" 2>&1
tail -14 "$LOG"; echo "klatki: $TMP/frames"
[ $fail -eq 0 ]
