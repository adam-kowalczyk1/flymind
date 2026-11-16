#!/bin/bash
# Test końcowy kroku 3 (LOOP_TARGET_arm3_r1.md): 27 serii × 135 prób, najwyżej 9 naraz. Uruchamiany RAZ.
# (Pierwsza wersja tego skryptu nie uruchomiła żadnej serii: xargs -I „command line cannot be assembled, too long”.)
xargs -P 9 -L 1 /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad/one3.sh < /private/tmp/claude-501/-Users-admin-so101-fly-project/91a9f7f1-070f-417c-851e-52c17a1b7e28/scratchpad/test3_jobs.txt
echo "koniec testu: $(ls /Users/admin/so101_fly_project/flymind/results/step3_20261115/test/*.json 2>/dev/null | wc -l) plików JSON"
