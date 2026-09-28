#!/bin/bash
# Launch danmaku and capture verification evidence mid-flight
cd /home/z/vibe/danmaku
pkill -f "danmaku[.]py" 2>/dev/null   # bracket trick: regex matches "danmaku.py" but not this literal line
sleep 0.3
/home/z/.venv/bin/python3 danmaku.py > /tmp/dan.log 2>&1 &
DPID=$!
sleep 2
WID=$(grep -E '^[0-9]+$' /tmp/dan.log | head -1)
echo "winId=$WID"
echo "--- xwininfo -shape (input shape must be empty => click-through) ---"
xwininfo -id "$WID" -shape 2>&1
echo "--- capture t=2s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 shot_t2.png -y
sleep 3
echo "--- capture t=5s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 shot_t5.png -y
wait $DPID
echo "danmaku exit=$?"
