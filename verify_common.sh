#!/bin/bash
# Shared setup for verify_*.sh. Source this file; do not execute it directly.
# Resolves the repository root, the Python interpreter and the X11 display, so
# the verification scripts work from any directory and any screen size.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR" || exit 1

PYTHON="${PYTHON:-python3}"
DISPLAY="${DISPLAY:-:1}"
export DISPLAY

if ! xdpyinfo >/dev/null 2>&1; then
    echo "cannot open X11 display '$DISPLAY'; set DISPLAY to your session" >&2
    exit 1
fi
SCREEN_SIZE="$(xdpyinfo | awk '/dimensions:/ {print $2; exit}')"
