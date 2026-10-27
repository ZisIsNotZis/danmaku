# danmaku project status

## Classification

Closed experiment: a PyQt5 + X11 desktop danmaku (scrolling-comment) engine.

## Status

Closed as a milestone (2026-09-29). This is a small for-fun project; no further
development is planned. AI/roast overlay functionality was moved to
[Backseat](https://github.com/ZisIsNotZis/backseat) and removed from here.

## What the milestone contains

- [`../danmaku.py`](../danmaku.py) — one-shot overlay; text, font, duration and
  vertical position are CLI options.
- [`../danmaku_engine.py`](../danmaku_engine.py) — v2 engine with per-comment
  pixmap windows, lane allocation, two-lane large comments, a real-time JSON
  timeline player and a daemon exposing `Engine.push()`.
- [`../danmaku_storm.py`](../danmaku_storm.py) — high-density storm on one
  fullscreen window; the reference model the engine was measured against.
- [`../timeline_test.json`](../timeline_test.json) — sample feed exercising
  small, large, colored and burst comments.

## Evidence

- Verification scripts: `verify_flight.sh`, `verify_engine.sh`,
  `verify_storm.sh`, with captured frames (`eng_*.png`, `storm_*.png`). They
  check the empty X11 input shape (click-through), capture frames with
  `ffmpeg`, and sample engine CPU time from `/proc/<pid>/stat`.
- The captures were taken on a 2560×1440 X11 session and scaled to 1280 px wide
  by the scripts.
- Runtime dependencies are only Python 3, PyQt5, and an X11 session.

## Decisions and rejected branches

- **Rejected: one fullscreen translucent window repainted at 60 fps.** It
  showed the right picture but cleared and redrew a 2560×1440 ARGB surface
  every frame, so the animation stuttered. It survives only as the storm demo,
  which exists to make that comparison visible.
- **Accepted: one tiny window per comment.** Each comment is rasterized once
  into a pixmap; the animation only calls `move()`. Frames cost a handful of
  X11 move requests instead of a fullscreen repaint.
- **Accepted: fixed lifetime, catch-up-aware lane rule.** Every comment crosses
  in the same time, so speed scales with width. A lane admits a new comment
  only when
  `delta >= T * max(w_new, w_last) / (W + max(w_new, w_last))`; the gap hits
  zero exactly at the leader's exit, so lanes stay tight without collisions.
- **Accepted: two independent click-through mechanisms.** Qt's
  `WindowTransparentForInput` plus a raw `XShapeCombineRectangles` fallback.
  The fallback is cheap and covers Qt/the window manager not honoring the flag.
- **Rejected: packaging, CI and a network daemon protocol.** They would add
  maintenance to a closed for-fun project; `push()` is in-process.

## Boundaries

The click-through window behavior is X11-specific and is not portable to
Wayland or other display servers. There is no packaged release and no CI. The
engine has no persistent feed source; the daemon is an embedding API, not a
socket server.
