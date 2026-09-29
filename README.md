# danmaku

> **Status: closed (milestone).** A small, self-contained PyQt5 danmaku
> (scrolling-comment) engine for X11 desktops. No further development is planned.

A small collection of Python desktop overlays for animated Chinese danmaku
(scrolling comments). The demos use PyQt5 and X11 to keep the text window
transparent, always on top, and click-through; `danmaku.py` is the one-shot
overlay, with separate engine and storm experiments alongside it.

This repository is deliberately only the danmaku engine. The earlier
AI/roast overlay that watched the screen and generated comments has moved to
[Backseat](https://github.com/ZisIsNotZis/backseat); no AI code remains here.

## Requirements

- Python 3
- PyQt5
- An X11 desktop session (the click-through fallback uses X11/Xext)
- The `Noto Sans CJK SC` font for the intended typography

Run a demo with `python3 danmaku.py` from this directory. Other experiments are
in `danmaku_engine.py` and `danmaku_storm.py`. The `verify_*.sh` scripts exercise
their corresponding demos or logic checks.

This is an experimental desktop project; the X11-specific window behavior is not
portable to all display servers. See
[`docs/project-status.md`](docs/project-status.md) for evidence and boundaries.
