#!/bin/bash
# Kamera OV9281 (U20CAM-9281M): stałe krótkie naświetlanie (uvc-util, jak zaleca producent) + pomiar prawdziwych kl./s.
# Uruchamiać WKLEJAJĄC w Terminal:  bash hardware/sensors/kamera_szybko.sh [ms naświetlania, domyślnie 5] [gain 0–64, domyślnie 40]
# „auto” zamiast ms przywraca auto-naświetlanie. Ustawienie znika po wyjęciu kamery. Wynik: ~/Desktop/kamera_szybko.txt
U=/Users/admin/tools/uvc-util/src/uvc-util; FF=/Users/admin/miniforge3/bin/ffmpeg; OUT=~/Desktop/kamera_szybko.txt
MS=${1:-5}; GAIN=${2:-40}
if [ "$MS" = auto ]; then "$U" -I 0 -s auto-exposure-mode=8; else
  "$U" -I 0 -s auto-exposure-mode=1 -s exposure-time-abs=$(python3 -c "print(round($MS*10))") -s gain=$GAIN; fi
{ echo "kamera_szybko $(date): naświetlanie $MS ms, gain $GAIN"; "$U" -I 0 -g auto-exposure-mode -g exposure-time-abs -g gain; } > "$OUT"
for m in "640x400 120" "320x200 120"; do set -- $m
  printf "%-8s @%s : " "$1" "$2" | tee -a "$OUT"; LOG=$(mktemp)
  "$FF" -nostdin -hide_banner -f avfoundation -framerate "$2" -video_size "$1" -i "USB Camera" -t 5 -f null - > "$LOG" 2>&1 &
  P=$!; for i in $(seq 1 9); do kill -0 $P 2>/dev/null || break; sleep 1; done; kill -9 $P 2>/dev/null; wait $P 2>/dev/null
  R=$(tr '\r' '\n' < "$LOG" | grep -E "^frame=" | tail -1 | sed -E 's/.*frame= *([0-9]+).*fps= *([0-9.]+).*/klatek \1, \2 kl.\/s/')
  echo "${R:-0 klatek (wisi)}" | tee -a "$OUT"; rm -f "$LOG"
done
"$FF" -nostdin -hide_banner -loglevel error -f avfoundation -framerate 120 -video_size 640x400 -i "USB Camera" -frames:v 20 -update 1 -y ~/Desktop/kamera_szybko.png
{ echo "po pomiarze (czy macOS nie przywrócił auto):"; "$U" -I 0 -g auto-exposure-mode -g exposure-time-abs; } >> "$OUT"
cat "$OUT"; echo "GOTOWE — zdjęcie: ~/Desktop/kamera_szybko.png"
