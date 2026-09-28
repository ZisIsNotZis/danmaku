#!/bin/bash
# Launch danmaku storm and capture verification evidence
cd /home/z/vibe/danmaku
pkill -f "danmaku_storm[.]py" 2>/dev/null   # bracket trick: won't match this shell
sleep 0.3
/home/z/.venv/bin/python3 danmaku_storm.py > /tmp/storm.log 2>&1 &
DPID=$!
sleep 2
WID=$(grep -E '^[0-9]+$' /tmp/storm.log | head -1)
echo "winId=$WID"
echo "--- input shape (must be empty => click-through) ---"
xwininfo -id "$WID" -shape 2>&1
sleep 4
echo "--- capture t=6s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 storm_t6.png -y
sleep 10
echo "--- capture t=16s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 storm_t16.png -y
sleep 10
echo "--- capture t=26s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 storm_t26.png -y
wait $DPID
echo "storm exit=$?"
tail -3 /tmp/storm.log
