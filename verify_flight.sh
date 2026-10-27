#!/bin/bash
# Launch danmaku and capture verification evidence mid-flight.
# Env: DISPLAY (default :1), PYTHON (default python3).
. "$(dirname "${BASH_SOURCE[0]}")/verify_common.sh"

pkill -f "danmaku[.]py" 2>/dev/null   # bracket trick: matches the demo, not this script
sleep 0.3
"$PYTHON" danmaku.py > /tmp/dan.log 2>&1 &
DPID=$!
trap 'kill "$DPID" 2>/dev/null || true' EXIT
sleep 2

WID=$(grep -E '^[0-9]+$' /tmp/dan.log | head -1)
echo "winId=$WID"
echo "--- xwininfo -shape (input shape must be empty => click-through) ---"
[ -n "$WID" ] && xwininfo -id "$WID" -shape 2>&1

echo "--- capture t=2s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 shot_t2.png -y
sleep 3
echo "--- capture t=5s ---"
ffmpeg -loglevel error -f x11grab -video_size "$SCREEN_SIZE" -i "$DISPLAY" \
    -frames:v 1 -vf scale=1280:-2 shot_t5.png -y

wait "$DPID"
trap - EXIT
echo "danmaku exit=$?"
