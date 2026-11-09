#!/bin/bash
# Etap 1 — testy z trwałym logiem (nie benchmark wydajności: żadnej serii 250/500 cykli).
#   run_validation.sh                         testy Etapu 1 (5 plików)            → validation_<data>.log
#   run_validation.sh regression              inni użytkownicy so101.SO101Sim       → regression_<data>.log
#                                             (bieżący so101.py oraz zamrożony sprzed Etapu 1; wyniki mają być identyczne)
#   run_validation.sh mutation                testy mutacyjne (mutate.py)           → mutation_<data>.log
# Wcześniejszych logów nie nadpisuje. Testy uruchamiane z katalogu tymczasowego: MuJoCo dopisuje ostrzeżenia
# o niestabilności do ./MUJOCO_LOG.TXT, a testy nie mogą nic zapisać w repozytorium.
set -u
R="$(cd "$(dirname "$0")/../../../.." && pwd)"
V="flymind/results/pick_place/validation"
PY="$R/.venv/bin/python"
LABEL="${1:-validation}"
LOG="$R/$V/${LABEL}_$(date +%Y%m%d_%H%M%S).log"
[ -e "$LOG" ] && { echo "log $LOG już istnieje"; exit 2; }
TMP="$(mktemp -d)"
OLD="flymind/validation/v5v4_frozen_code/so101.py"     # so101.py sprzed Etapu 1 (sha256 3ad95d38…, jak w manifestach V5)
case "$LABEL" in
  validation) CMDS=("flymind/test_pick_place.py" "flymind/test_pick_place_faults.py" "flymind/test_reach.py"
                    "flymind/test_safety.py" "flymind/test_so101.py --zgoda-sim") ;;
  regression) CMDS=("flymind/test_cl_runner.py" "flymind/demo/test_demo.py"
                    "$V/with_so101.py $R/$OLD $R/flymind/test_cl_runner.py"
                    "$V/with_so101.py $R/$OLD $R/flymind/demo/test_demo.py") ;;
  mutation)   CMDS=("$V/mutate.py") ;;
  *) echo "nieznany zestaw: $LABEL"; exit 2 ;;
esac
{
  echo "# Etap 1 — log testów: $LABEL (NIE benchmark wydajności)"
  echo "data: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "commit bazowy (HEAD): $(git -C "$R" rev-parse HEAD) ($(git -C "$R" branch --show-current))"
  echo "zmiany względem HEAD w plikach Etapu 1:"; git -C "$R" status --porcelain -- flymind/so101.py flymind/pick_place.py \
    flymind/test_pick_place.py flymind/test_pick_place_faults.py flymind/reach.py flymind/grip.py flymind/safety.py "$V" | sed 's/^/  /'
  echo "sha256 kodu i testów:"; (cd "$R" && shasum -a 256 flymind/so101.py flymind/pick_place.py flymind/reach.py flymind/grip.py \
    flymind/safety.py flymind/test_pick_place.py flymind/test_pick_place_faults.py flymind/test_reach.py flymind/test_safety.py \
    flymind/test_so101.py flymind/test_cl_runner.py flymind/demo/test_demo.py flymind/loop.py "$OLD" "$V/mutate.py" \
    "$V/with_so101.py" "$V/run_validation.sh" | sed 's/^/  /')
  echo "python: $("$PY" -c 'import sys; print(sys.version.split()[0])')"
  echo "mujoco: $("$PY" -c 'import mujoco; print(mujoco.__version__)')"
  echo "numpy:  $("$PY" -c 'import numpy; print(numpy.__version__)')"
  echo "katalog roboczy testów: $TMP"
  echo
} > "$LOG"
pass=0; fail=0; i=0
for c in "${CMDS[@]}"; do
  echo "## \$ .venv/bin/python -I -B $c" >> "$LOG"
  (cd "$TMP" && "$PY" -I -B $R/$c) > "$TMP/out$i.txt" 2>&1
  rc=$?
  cat "$TMP/out$i.txt" >> "$LOG"
  echo "## kod wyjścia: $rc" >> "$LOG"; echo >> "$LOG"
  if [ $rc -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); fi
  i=$((i+1))
done
if [ "$LABEL" = regression ]; then      # te same testy z bieżącym i z zamrożonym so101.py: wyjście bez czasu zegarowego
  for k in 0 1; do
    if diff <(sed -E 's/trial wall [0-9.]+ s/trial wall X s/' "$TMP/out$k.txt") \
            <(sed -E 's/trial wall [0-9.]+ s/trial wall X s/' "$TMP/out$((k+2)).txt") >> "$LOG"; then
      echo "## PORÓWNANIE ${CMDS[$k]}: wyjście z bieżącym so101.py IDENTYCZNE z wyjściem z zamrożonym" >> "$LOG"
    else
      echo "## PORÓWNANIE ${CMDS[$k]}: RÓŻNICE (powyżej)" >> "$LOG"; fail=$((fail+1))
    fi
  done
fi
{
  echo "## PODSUMOWANIE ($LABEL): polecenia uruchomione ${#CMDS[@]}, zaliczone $pass, niezaliczone $fail, pominięte 0"
  echo "## zmiany śledzonych plików po testach (ma być to samo co na górze logu):"
  git -C "$R" status --porcelain | grep -v '^??' | sed 's/^/##   /'
} >> "$LOG"
echo "$LOG"; tail -8 "$LOG"
[ $fail -eq 0 ]
