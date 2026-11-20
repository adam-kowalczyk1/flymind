#!/bin/bash
# Kąt widzenia kamery nadgarstka (20 XI). Ustawienie: kamera leży na stole, obiektyw prosto na ścianę, szkło obiektywu
# DOKŁADNIE 15 cm od ściany. Na ścianie, na wysokości obiektywu, poziomo przyklejona miarka zwijana (~80 cm), jej środek
# naprzeciw obiektywu. Zdjęcia w obu trybach (640x400 = ten, którego używa mucha; może być wycinkiem albo całym kadrem).
# Uruchamiać WKLEJAJĄC w Terminal:  bash /Users/admin/so101_fly_project/hardware/sensors/kamera_fov.sh [cm do ściany, domyślnie 15]
FF=/Users/admin/miniforge3/bin/ffmpeg; D=${1:-15}
for m in "1280x800 30" "640x400 120"; do set -- $m
  "$FF" -nostdin -hide_banner -loglevel error -f avfoundation -framerate "$2" -video_size "$1" -i "USB Camera" \
        -frames:v 30 -update 1 -y ~/Desktop/kamera_fov_$1.png &
  P=$!; for i in $(seq 1 12); do kill -0 $P 2>/dev/null || break; sleep 1; done; kill -9 $P 2>/dev/null; wait $P 2>/dev/null
  ls -l ~/Desktop/kamera_fov_$1.png 2>/dev/null || echo "BRAK zdjęcia $1"
done
echo "$(date): odległość do ściany $D cm" > ~/Desktop/kamera_fov.txt
echo "GOTOWE — zdjęcia ~/Desktop/kamera_fov_*.png; napisz Claude, ile cm od ściany była kamera"
