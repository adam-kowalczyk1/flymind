#!/bin/bash
# Etap 1 — POWTÓRZENIE serii S0–S4 i S3×500 poprawionym kodem, pod NOWYMI nazwami (<tag>_<sufiks>). Te same polecenia,
# ziarna i parametry co run_sweep.sh / seria 500 (zmienia się tylko --tag). Historycznych plików nie dotyka:
# pick_place.py odmawia zapisu, gdy tag istnieje, a ten skrypt sprawdza to przed startem i ma włączone noclobber.
# Uruchamiane z katalogu tymczasowego (MuJoCo pisze ostrzeżenia do ./MUJOCO_LOG.TXT).
#   run_postfix.sh [sufiks=postfix_v1]   → wyniki w flymind/results/pick_place/, log w validation/benchmarks_<sufiks>.log
set -u -o noclobber
R="$(cd "$(dirname "$0")/../../../.." && pwd)"
SUF="${1:-postfix_v1}"
O="$R/flymind/results/pick_place"; V="$O/validation"; LOG="$V/benchmarks_$SUF.log"
PY="$R/.venv/bin/python"
P="$PY -I -B $R/flymind/pick_place.py"
HM="-0.065 -0.17 0.179 1.512 1.571 0.93"
S="--seeds 1 2 3 4 5 --cycles 50"
TAGS=(S0_baseline S1_v1.45 S2_v1.45_jaw0.65 S3_v1.45_jaw0.65_homemid S4_v1.0_jaw0.65_homemid S3_long500_seed6)
ARGS=("$S" "$S --v 1.45 --a 8" "$S --v 1.45 --a 8 --q-pre 0.65" "$S --v 1.45 --a 8 --q-pre 0.65 --home $HM"
      "$S --q-pre 0.65 --home $HM" "--seeds 6 --cycles 500 --v 1.45 --a 8 --q-pre 0.65 --home $HM")
for t in "${TAGS[@]}"; do
  for f in "$O/${t}_$SUF.json" "$O/${t}_$SUF.INCOMPLETE.json" "$O/${t}_${SUF}_stdout.txt"; do
    [ -e "$f" ] && { echo "istnieje $f — wybierz inny sufiks"; exit 2; }
  done
done
[ -e "$LOG" ] && { echo "istnieje $LOG — wybierz inny sufiks"; exit 2; }
(cd "$R" && shasum -a 256 -c "$V/historical_sha256.txt" > /dev/null) || { echo "historyczne wyniki ≠ manifest — stop"; exit 3; }
TMP="$(mktemp -d)"
{
  echo "# Etap 1 — powtórzenie benchmarków poprawionym kodem, sufiks $SUF"
  echo "data startu: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "commit bazowy (HEAD): $(git -C "$R" rev-parse HEAD) ($(git -C "$R" branch --show-current)); kod niezacommitowany:"
  git -C "$R" status --porcelain -- flymind/so101.py flymind/pick_place.py flymind/reach.py flymind/grip.py flymind/safety.py | sed 's/^/  /'
  echo "sha256 kodu:"; (cd "$R" && shasum -a 256 flymind/so101.py flymind/pick_place.py flymind/reach.py flymind/grip.py flymind/safety.py | sed 's/^/  /')
  echo "python $("$PY" -c 'import sys; print(sys.version.split()[0])'), mujoco $("$PY" -c 'import mujoco; print(mujoco.__version__)'), numpy $("$PY" -c 'import numpy; print(numpy.__version__)')"
  echo "historyczne wyniki przed startem: 17/17 zgodne z validation/historical_sha256.txt"
  echo "katalog roboczy: $TMP (6 serii równolegle; czasy zegarowe nieporównywalne z historycznymi)"
  echo
} > "$LOG"
cd "$TMP"
pids=()
for i in "${!TAGS[@]}"; do
  t="${TAGS[$i]}_$SUF"
  echo "\$ .venv/bin/python -I -B flymind/pick_place.py ${ARGS[$i]} --tag $t" >> "$LOG"
  $P ${ARGS[$i]} --tag "$t" > "$O/${t}_stdout.txt" 2>&1 &
  pids+=($!)
done
fail=0
for i in "${!TAGS[@]}"; do
  wait "${pids[$i]}"; rc=$?
  echo "kod wyjścia ${TAGS[$i]}_$SUF: $rc" >> "$LOG"
  [ $rc -eq 0 ] || fail=$((fail+1))
done
{
  echo "data końca: $(date '+%Y-%m-%d %H:%M:%S %z'); serie nieudane (kod ≠ 0): $fail"
  echo "MUJOCO_LOG.TXT w katalogu roboczym: $([ -f MUJOCO_LOG.TXT ] && grep -c WARNING MUJOCO_LOG.TXT || echo 0) ostrzeżeń"
  echo; echo "## historyczne wyniki po przebiegu (shasum -c):"
  (cd "$R" && shasum -a 256 -c "$V/historical_sha256.txt" 2>&1 | sed 's/^/  /')
  echo; echo "## sha256 nowych wyników:"
  (cd "$R" && shasum -a 256 flymind/results/pick_place/*_"$SUF".json flymind/results/pick_place/*_"${SUF}"_stdout.txt | sed 's/^/  /')
  echo; echo "## porównanie ze starymi seriami (compare_postfix.py $SUF):"
  "$PY" -I -B "$V/compare_postfix.py" "$SUF" 2>&1
  echo "## kod wyjścia porównania: $?"
} >> "$LOG" 2>&1
tail -3 "$LOG"
[ $fail -eq 0 ]
