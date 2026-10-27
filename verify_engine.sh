#!/bin/bash
# Engine v2 timeline test: input-shape check, captures and CPU measurement.
# Env: DISPLAY (default :1), PYTHON (default python3).
. "$(dirname "${BASH_SOURCE[0]}")/verify_common.sh"

pkill -f "danmaku_engine[.]py" 2>/dev/null
sleep 0.3
"$PYTHON" danmaku_engine.py script timeline_test.json --duration 30 > /tmp/eng.log 2>&1 &
EPID=$!
trap 'kill "$EPID" 2>/dev/null || true' EXIT
sleep 2

if command -v xdotool >/dev/null 2>&1; then
    W1=$(xdotool search --class danmaku 2>/dev/null | head -1)
    echo "--- one comment window (id=$W1) input shape ---"
    [ -n "$W1" ] && xwininfo -id "$W1" -shape 2>&1 | tail -5
else
    echo "--- xdotool not installed: skipping the window input-shape check ---"
fi

sleep 4
echo "--- capture t=6s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 eng_t6.png -y

U1=$(awk '{print $14+$15}' /proc/$EPID/stat 2>/dev/null)
sleep 10
U2=$(awk '{print $14+$15}' /proc/$EPID/stat 2>/dev/null)
echo "--- capture t=20s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 eng_t20.png -y
U3=$(awk '{print $14+$15}' /proc/$EPID/stat 2>/dev/null)
sleep 5
U4=$(awk '{print $14+$15}' /proc/$EPID/stat 2>/dev/null)

echo "cpu% during 8-18s: $("$PYTHON" -c "print(f'{($U2-$U1)/10:.1f}')")"
echo "cpu% during 25-30s: $("$PYTHON" -c "print(f'{($U4-$U3)/5:.1f}')")"

wait "$EPID"
trap - EXIT
echo "--- engine log ---"
cat /tmp/eng.log
