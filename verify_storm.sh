#!/bin/bash
# Launch the storm demo and capture verification evidence.
# Env: DISPLAY (default :1), PYTHON (default python3).
. "$(dirname "${BASH_SOURCE[0]}")/verify_common.sh"

pkill -f "danmaku_storm[.]py" 2>/dev/null   # bracket trick: matches the demo, not this script
sleep 0.3
"$PYTHON" danmaku_storm.py > /tmp/storm.log 2>&1 &
DPID=$!
trap 'kill "$DPID" 2>/dev/null || true' EXIT
sleep 2

WID=$(grep -E '^[0-9]+$' /tmp/storm.log | head -1)
echo "winId=$WID"
echo "--- input shape (must be empty => click-through) ---"
[ -n "$WID" ] && xwininfo -id "$WID" -shape 2>&1

sleep 4
echo "--- capture t=6s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 storm_t6.png -y
sleep 10
echo "--- capture t=16s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 storm_t16.png -y
sleep 10
echo "--- capture t=26s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 storm_t26.png -y

wait "$DPID"
trap - EXIT
echo "storm exit=$?"
tail -3 /tmp/storm.log
