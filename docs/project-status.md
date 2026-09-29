# danmaku project status

## Classification

Closed experiment: a PyQt5 + X11 desktop danmaku (scrolling-comment) engine.

## Status

Closed as a milestone (2026-09-29). This is a small for-fun project; no further
development is planned. AI/roast overlay functionality was moved to
[Backseat](https://github.com/ZisIsNotZis/backseat) and removed from here.

## Evidence

- Engine: [`../danmaku_engine.py`](../danmaku_engine.py) — lane allocation and
  push API; [`../danmaku.py`](../danmaku.py) one-shot overlay;
  [`../danmaku_storm.py`](../danmaku_storm.py) storm model.
- Verification scripts: `verify_engine.sh`, `verify_flight.sh`,
  `verify_storm.sh`, with captured frames (`eng_*.png`, `storm_*.png`).
- Runtime dependencies are only Python 3, PyQt5, and an X11 session.

## Boundaries

The click-through window behavior is X11-specific and is not portable to all
display servers. There is no packaged release, no CI, and no AI component in
this repository.
