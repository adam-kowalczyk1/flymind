#!/bin/bash
# Diagnostyka kamery nadgarstka (OV9281, „USB Camera”): lista trybów + PRAWDZIWE klatki/s w każdym trybie i formacie.
# Tylko odczyt kamery. Uruchamiać WKLEJAJĄC w Terminal (komendy uruchamiane przez Claude dostają 0 klatek — uprawnienia macOS).
# Wynik: ~/Desktop/kamera_diag.txt  (~2 min)
FF=/Users/admin/miniforge3/bin/ffmpeg; CAM="USB Camera"; OUT=~/Desktop/kamera_diag.txt
echo "Diagnostyka kamery $(date)" > "$OUT"
echo "== tryby, które kamera zgłasza macOS:" >> "$OUT"
"$FF" -hide_banner -f avfoundation -video_size 1x1 -i "$CAM" -t 0.1 -f null - 2>&1 | grep -E "fps|@" | sed 's/.*\]//' >> "$OUT"
echo "== pomiar (5 s na tryb; fps = ile klatek naprawdę przyszło):" >> "$OUT"
for m in "1280x800 120" "1280x800 60" "1280x800 30" "640x400 120" "640x400 60" "640x400 30" "320x200 120"; do
  for pf in default nv12 yuyv422; do
    set -- $m; PF=(); [ "$pf" != default ] && PF=(-pixel_format "$pf")
    printf "%-9s @%3s  %-8s : " "$1" "$2" "$pf" | tee -a "$OUT"
    LOG=$(mktemp)
    "$FF" -nostdin -hide_banner -f avfoundation -framerate "$2" -video_size "$1" "${PF[@]}" -i "$CAM" -t 5 -f null - > "$LOG" 2>&1 &
    P=$!; for i in $(seq 1 9); do kill -0 $P 2>/dev/null || break; sleep 1; done; kill -9 $P 2>/dev/null; wait $P 2>/dev/null
    R=$(tr '\r' '\n' < "$LOG" | grep -E "^frame=" | tail -1 | sed -E 's/.*frame= *([0-9]+).*fps= *([0-9.]+).*/klatek \1, \2 kl.\/s/')
    E=$(grep -m1 -iE "not supported|error|failed" "$LOG" | sed 's/.*\] //' | cut -c1-60)
    echo "${R:-0 klatek (wisi)} ${E}" | tee -a "$OUT"; rm -f "$LOG"
  done
done
echo "GOTOWE — wynik na biurku: kamera_diag.txt"
