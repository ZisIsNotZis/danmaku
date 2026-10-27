# Contributing

This repository is a closed milestone: it is complete and working, but not
actively developed. Small fixes and portability patches are welcome. Large
feature branches are unlikely to be merged, because they would reopen a project
that was deliberately closed.

## Ground rules

- Keep the overlay X11-native. Wayland needs a different mechanism, not a shim.
- Keep the runtime dependency list at PyQt5. No packaging, framework or CI
  additions.
- Keep the code small. The engine is intentionally a handful of files.
- Do not add AI, screen watching, or comment generation. That code lives in
  [Backseat](https://github.com/ZisIsNotZis/backseat).

## Trying a change

Start the demo you touched:

```bash
python3 danmaku.py
python3 danmaku_engine.py script timeline_test.json
python3 danmaku_storm.py
```

Then run the matching verification script, which checks the X11 input shape and
captures frames:

```bash
./verify_flight.sh
./verify_engine.sh
./verify_storm.sh
```

They need `ffmpeg`, `xwininfo` and `xdpyinfo`; `xdotool` is optional. Set
`DISPLAY` if your session is not `:1`, and `PYTHON` if `python3` is not the
interpreter with PyQt5. The scripts overwrite the committed captures, so commit
the new frames only if the change is meant to alter them.

If a change affects behavior, update the matching paragraph in the README and
the evidence in [`docs/project-status.md`](docs/project-status.md).

## Reporting a bug

Include your distribution, desktop environment or window manager, X server,
screen size, Python and PyQt5 versions, the exact command, and what you saw. If
click-through is involved, include the output of:

```bash
xwininfo -id <window-id> -shape
```

## License

By contributing you agree that your contribution is licensed under the
[GNU AGPL v3](LICENSE.md).
