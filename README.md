<p align="center"><img src="assets/logo.svg" width="96" height="96" alt="danmaku logo"></p>

<h1 align="center">danmaku</h1>

<p align="center"><b>Bilibili-style scrolling comments over any X11 desktop — transparent, always on top, and invisible to the mouse.</b></p>

Danmaku draws Chinese scrolling comments straight onto your screen. There is no
window frame, no background and no taskbar entry: only the outlined text, flying
right to left, while every click reaches the application underneath. The whole
thing is a few hundred lines of Python and PyQt5.

![Storm demo: dense danmaku over terminals](storm_t16.png)

<p align="center"><i>Storm demo at t=16&nbsp;s on a 2560×1440 X11 desktop. The terminals
underneath kept taking input while these comments crossed them.</i></p>

## Why it exists

A danmaku layer is a strange window: it must cover the screen, stay above
everything, let input through, and not cost a frame. The first version did the
obvious thing — one translucent fullscreen window repainted at 60 fps — and it
stuttered, because every frame cleared and redrew a 2560×1440 ARGB surface.

This engine does the opposite. Each comment is rasterized **once** into its own
tiny pixmap-backed window; a frame only moves those windows. No fullscreen
repaint, no re-rasterization, no per-frame text layout.

## Quick start

Requirements: Python 3, PyQt5, an X11 session, and the
`Noto Sans CJK SC` font.

```bash
git clone https://github.com/ZisIsNotZis/danmaku.git
cd danmaku
python3 -m pip install -r requirements.txt
python3 danmaku.py                       # one comment flies across in 10 s
python3 danmaku.py "Hello from danmaku" --duration 6
```

`danmaku.py` prints its X11 window id so the verification scripts can inspect
the input shape.

## The three programs

| File | What it is | Run it |
| --- | --- | --- |
| `danmaku.py` | One-shot overlay: a single comment crosses the screen. | `python3 danmaku.py` |
| `danmaku_engine.py` | The engine: per-comment windows, lane allocation, large two-lane comments, timed JSON feed or daemon API. | `python3 danmaku_engine.py script timeline_test.json` |
| `danmaku_storm.py` | High-density storm on one fullscreen window — the reference model the engine was compared against. | `python3 danmaku_storm.py` |

`danmaku.py` accepts the text as an argument plus `--font`, `--font-size`,
`--duration` (seconds) and `--vertical` (0 = top, 1 = bottom). For example:

```bash
python3 danmaku.py "前方高能！" --font-size 48 --vertical 0.5 --duration 8
```

The engine's timeline is JSON, sorted by time; a minimal entry looks like this:

```json
[
  {"t": 0.5, "text": "engine v2 上线测试", "color": "#FFFFFF"},
  {"t": 1.5, "text": "大字占两行！", "color": "#FFD700", "size": "large"}
]
```

```bash
python3 danmaku_engine.py script timeline_test.json --duration 30
python3 danmaku_engine.py daemon        # Engine.push(text, color, size) for embedding code
```

## How it avoids stutter

- **One window per comment.** The text is painted once into a `QPixmap`; the
  animation loop only calls `move()`, which reaches X11 as `XMoveWindow`.
- **Lane entry without overlap and without slack.** With a fixed lifetime `T`,
  comment width `w` and screen width `W`, a lane accepts a new comment only if
  `delta >= T * max(w_new, w_last) / (W + max(w_new, w_last))`. The gap reaches
  zero exactly when the leader leaves; nothing catches up, nothing is wasted.
- **Large comments occupy two lanes** (falling back to small when no band is
  free), so big text never collides with the lane below.
- **Click-through.** Qt's `WindowTransparentForInput` gets an empty X11 input
  shape, with a raw `XShapeCombineRectangles` fallback for good measure.
- **Fixed lifetime means speed scales with width:** a long comment flies faster
  than a short one, which is what makes classic danmaku look right.

## Verification

Each script starts a demo, checks the X11 input shape, captures frames with
`ffmpeg`, and (for the engine) samples CPU time from `/proc`.

```bash
./verify_flight.sh    # one-shot overlay  -> shot_t2.png, shot_t5.png
./verify_engine.sh    # engine timeline   -> eng_t6.png, eng_t20.png, CPU %
./verify_storm.sh     # storm             -> storm_t6.png, storm_t16.png, storm_t26.png
```

They need `ffmpeg`, `xwininfo` and `xdpyinfo`; `verify_engine.sh` also uses
`xdotool` when available. Set `DISPLAY` if your session is not `:1`, and
`PYTHON` if `python3` is not the interpreter with PyQt5 installed. The captures
in this repository were produced by these scripts at 2560×1440, scaled to
1280 px wide.

## Requirements

- Python 3
- PyQt5 (see `requirements.txt`)
- X11 desktop session — the click-through fallback uses X11/Xext
- `Noto Sans CJK SC` for the intended typography (change `--font` or the
  `FONT_FAMILY` constant otherwise)

## Status

**Closed milestone.** This repository is the complete, working danmaku engine;
it is kept as a small for-fun project rather than an actively developed one.

- Done: one-shot overlay, v2 engine with pixel-perfect lane packing, storm
  demo, click-through input shape, verification scripts and captured frames.
- Not done: packaging, CI, Wayland support, a network protocol for the daemon
  (the `push()` API is in-process).
- Out of scope: the AI/roast overlay that watched the screen and generated
  comments. It now lives in
  [Backseat](https://github.com/ZisIsNotZis/backseat); no AI code remains here.
- Next: nothing — the milestone is closed. See
  [`docs/project-status.md`](docs/project-status.md) for evidence and boundaries.

## Repository layout

```
danmaku.py           one-shot overlay
danmaku_engine.py    v2 engine + timeline player / daemon
danmaku_storm.py     fullscreen storm reference model
timeline_test.json   sample feed for the engine
requirements.txt     the only Python dependency (PyQt5)
verify_*.sh          start, inspect and capture each demo
eng_*.png            engine captures
storm_*.png          storm captures
assets/logo.svg      README mark
docs/                project status and evidence
```

## License

[GNU AGPL v3](LICENSE.md).
