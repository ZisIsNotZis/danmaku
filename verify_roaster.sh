#!/bin/bash
# Roaster integration test: agent + engine together, captures + CPU
cd /home/z/vibe/danmaku
pkill -f "danmaku_engine[.]py" 2>/dev/null
pkill -f "roaster[.]py" 2>/dev/null
rm -f /tmp/roaster.log
sleep 0.3
/home/z/.venv/bin/python3 roaster.py --interval 20 --duration 200 --model volcengine/glm-5.3-flash > /tmp/roaster_stdout.log 2>&1 &
RPID=$!
sleep 30
echo "--- capture t=30s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 roast_t30.png -y
U1=$(awk '{print $14+$15}' /proc/$RPID/stat 2>/dev/null)
sleep 10
U2=$(awk '{print $14+$15}' /proc/$RPID/stat 2>/dev/null)
echo "cpu% during 30-40s: $(python3 -c "print(f'{($U2-$U1)/10:.1f}')")"
sleep 60
echo "--- capture t=100s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 roast_t100.png -y
sleep 60
echo "--- capture t=160s ---"
ffmpeg -loglevel error -f x11grab -video_size 2560x1440 -i :1 -frames:v 1 -vf scale=1280:-2 roast_t160.png -y
wait $RPID
echo "roaster exit=$?"
echo "--- agent log ---"
cat /tmp/roaster.log 2>/dev/null
echo "--- engine stats ---"
tail -3 /tmp/roaster_stdout.log
