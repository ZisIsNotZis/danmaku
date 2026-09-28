#!/usr/bin/env python3
"""Roast/snark agent V1 — a VLM watches your screen on an interval (with
memory) and sends the most critical/funny danmaku it can.

Design (per spec):
- Separate program; engine is a library (danmaku_engine.py).
- ONE VLM call per frame (no multi-turn reasoning), memory injected as a
  compact digest -> agent stays stateful without extra round trips.
- Real-time async: frames are captured at interval t; the engine allocates
  lanes when the push arrives; no lookahead anywhere.
- The agent picks its own color and size (small / large 2-row).
- Style: humorous but stern — critical, exaggerated, hits the nail; never
  vicious, roasts the on-screen situation, not the person.
- V1: single agent. (V2 idea: N personas + mutual visibility + arguments.)

Usage:
  roaster.py [--interval 20] [--duration 300] [--model volcengine/glm-5.3-flash]
"""
import argparse
import base64
import collections
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from PIL import Image

from danmaku_engine import Engine

BASE = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000")
KEY = os.environ.get("LITELLM_API_KEY", "")
DISPLAY = os.environ.get("DISPLAY", ":1")

SYSTEM_PROMPT = """你是「弹幕君」，一条飘在用户屏幕上的弹幕。你看用户的屏幕截图，然后说出最损但最准的那句话。

风格（严格遵守）：
- 幽默但严厉：夸张、一针见血、Critical。像B站观众里最懂行又最嘴毒的那个，吐槽要"命中要害"。
- 不恶毒、不人身攻击：吐槽的对象是屏幕上的事情（代码、报错、工作流、进度、拖延、重复失败、离谱的文件名），不是人的身份和外貌。
- 具体 > 空泛：必须引用画面里真实可见的东西。看不清或没素材就选择沉默，宁可不说话也不要瞎编。
- 中文为主，可夹杂程序员梗和英文缩写。长度：小字不超过22个字，大字不超过14个字。
- 你有记忆（下面给出最近几轮的屏幕摘要和你说过的话）。不许重复自己；同一个东西再次出现且更糟时，可以callback前文，前后呼应是最高级的梗。

频率控制：
- 大多数帧没什么可吐槽的 → action="nothing"。沉默是合法且正确的选择，不要硬找梗。
- 屏幕上真有好素材（新报错、离谱代码、明显摸鱼、卡住的进度条、反复出现的问题）→ action="roast"。
- 连续沉默之后实在想说话 → 偶尔允许 action="joke"，一句话冷笑话或神吐槽，不要连续两条joke。

输出：只输出一个JSON，不要markdown代码块，不要解释：
{"note": "一句话概括画面里最值得注意的东西（20字内）",
 "action": "roast 或 joke 或 nothing",
 "text": "弹幕内容，action=nothing时留空字符串",
 "color": "#RRGGBB",
 "size": "small 或 large"}
- color随情绪：白#FFFFFF默认，红#FF4D4D=怒其不争，黄#FFD700=高能，绿#4ADE80=嘲讽，粉#FF7EB9=阴阳怪气，青#22D3EE=震惊。
- size="large"（占两行的大字）只留给真正狠的、值得全屏看见的吐槽，十次里最多一两次。"""


def capture_screen(path="/tmp/roast_frame.jpg"):
    r = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-video_size", "2560x1440",
         "-i", DISPLAY, "-frames:v", "1", "-vf", "scale=1600:-2", "-q:v", "6", path, "-y"],
        capture_output=True, timeout=20)
    if r.returncode != 0:
        return None
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def is_blank(jpg):
    """True if the frame is (nearly) all black — DPMS/screen blanking."""
    try:
        img = Image.open(io.BytesIO(jpg)).convert("L").resize((64, 36))
        return img.getextrema()[1] < 16
    except Exception:
        return False


def active_window_title():
    try:
        r = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                           capture_output=True, text=True, timeout=5)
        return (r.stdout or "").strip()[:80] or "unknown"
    except Exception:
        return "unknown"


def call_model(model, messages, max_tokens=2500, disable_thinking=False):
    # NOTE: this GLM route always reasons and rejects thinking:{disabled} with
    # HTTP 400, so reasoning tokens must be budgeted via max_tokens.
    body = {"model": model, "messages": messages,
            "temperature": 1.0, "max_tokens": max_tokens}
    if disable_thinking:
        body["thinking"] = {"type": "disabled"}
    for attempt in range(6):
        req = urllib.request.Request(
            BASE + "/v1/chat/completions", data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=90))
            return r["choices"][0]["message"].get("content") or ""
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(10 * (attempt + 1))
                continue
            if e.code == 400 and disable_thinking:
                disable_thinking = False   # route may not accept the flag
                body.pop("thinking", None)
                continue
            raise
    return ""


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


def agent_loop(eng, args, log):
    mem = collections.deque(maxlen=8)
    deadline = time.time() + args.duration
    blank_streak = 0
    while time.time() < deadline:
        time.sleep(args.interval)
        if args.keep_awake:  # demo/test: 1px jiggle so the screen stays on
            subprocess.run(["xdotool", "mousemove_relative", "--", "1", "0"], timeout=5)
            time.sleep(0.05)
            subprocess.run(["xdotool", "mousemove_relative", "--", "-1", "0"], timeout=5)
        jpg = capture_screen()
        if not jpg:
            log("frame capture failed")
            continue
        if is_blank(jpg):
            blank_streak += 1
            if blank_streak % 5 != 0:   # mostly skip VLM on blank screens;
                log(f"blank screen #{blank_streak}, skipping VLM")
                continue                 # every 5th still gets its chance
        else:
            blank_streak = 0
        uri = "data:image/jpeg;base64," + base64.b64encode(jpg).decode()
        ts = time.strftime("%H:%M")
        digest = "\n".join(
            f"- [{m['t']}] 屏幕: {m['note']} | 你说: {m['said']}" for m in mem
        ) or "（这是第一帧，还没有记忆）"
        user_text = (f"当前时间 {ts}，活动窗口: {active_window_title()}\n"
                     f"【最近记忆（旧→新）】\n{digest}\n看图，输出JSON。")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": uri}},
                {"type": "text", "text": user_text}]},
        ]
        try:
            raw = call_model(args.model, messages)
        except Exception as e:
            log(f"model error: {type(e).__name__}: {e}")
            continue
        obj = parse_json(raw)
        if not obj:
            log(f"unparseable model output: {raw[:120]!r}")
            continue
        note = str(obj.get("note", ""))[:30]
        action = obj.get("action", "nothing")
        text = str(obj.get("text", "")).strip()
        said = ""
        if action in ("roast", "joke") and text:
            color = str(obj.get("color", "#FFFFFF"))
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                color = "#FFFFFF"
            size = "large" if obj.get("size") == "large" else "small"
            text = text[:14] if size == "large" else text[:22]
            eng.push(text, color, size)
            said = text
        mem.append({"t": ts, "note": note, "said": said})
        log(f"[{ts}] action={action:7s} note={note!r} said={said!r}")
    eng.close_feed()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=20)
    ap.add_argument("--duration", type=float, default=300,
                    help="seconds of roasting before clean shutdown")
    ap.add_argument("--model", default="volcengine/glm-5.3-flash")
    ap.add_argument("--keep-awake", action="store_true",
                    help="jiggle mouse 1px per interval so the screen stays on (tests)")
    ap.add_argument("--log", default="/tmp/roaster.log")
    args = ap.parse_args()

    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("danmaku")
    eng = Engine()
    eng.start()

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(args.log, "a") as f:
            f.write(line + "\n")

    t = threading.Thread(target=agent_loop, args=(eng, args, log), daemon=True)
    t.start()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
