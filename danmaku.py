#!/usr/bin/env python3
"""One-shot danmaku overlay: text flies right -> left across the screen.

- No background, no border: ARGB translucent window sized exactly to the text.
- Click-through: empty X11 input shape region (Qt flag + raw X11 fallback),
  so mouse events pass through to whatever is underneath.
- Topmost via X11BypassWindowManagerHint: no decorations, no taskbar, no focus.
"""
import ctypes
import ctypes.util
import sys

from PyQt5.QtCore import QElapsedTimer, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QApplication, QWidget

TEXT = "前方高能！非战斗人员请速速撤离！！"
FONT_FAMILY = "Noto Sans CJK SC"
FONT_SIZE = 64
DURATION_MS = 10000
OUTLINE_PX = 4
V_POSITION = 0.18  # vertical band where danmaku comments normally live


def force_empty_input_shape(xid):
    """Raw X11 fallback: set an empty input shape so clicks pass through."""
    x11_path = ctypes.util.find_library("X11")
    xext_path = ctypes.util.find_library("Xext")
    if not (x11_path and xext_path):
        return False
    x11 = ctypes.CDLL(x11_path)
    xext = ctypes.CDLL(xext_path)
    x11.XOpenDisplay.restype = ctypes.c_void_p
    dpy = x11.XOpenDisplay(None)
    if not dpy:
        return False
    # ShapeInput=2, ShapeSet=0, Unsorted=0, no rectangles => empty input region
    xext.XShapeCombineRectangles(
        ctypes.c_void_p(dpy), ctypes.c_uint(xid), ctypes.c_int(2),
        0, 0, None, 0, ctypes.c_int(0), ctypes.c_int(0),
    )
    x11.XCloseDisplay(ctypes.c_void_p(dpy))
    return True


class Danmaku(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
            | Qt.WindowTransparentForInput  # xcb sets empty XShape input region
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        font = QFont(FONT_FAMILY, FONT_SIZE)
        font.setBold(True)
        self.font = font
        fm = QFontMetrics(font)
        pad = OUTLINE_PX + 2
        self.pad = pad
        self.setFixedSize(fm.horizontalAdvance(TEXT) + 2 * pad,
                          fm.height() + 2 * pad)

        screen = QApplication.primaryScreen().geometry()
        self.y = int(screen.height() * V_POSITION)
        self.start_x = screen.left() + screen.width()
        self.end_x = screen.left() - self.width()

        self.clock = QElapsedTimer()
        self.anim = QTimer(self)
        self.anim.setInterval(16)  # ~60 fps
        self.anim.timeout.connect(self.tick)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addText(self.pad, self.pad + QFontMetrics(self.font).ascent(),
                     self.font, TEXT)
        # black outline first, then solid white fill -> classic danmaku look
        p.strokePath(path, QPen(QColor(0, 0, 0), OUTLINE_PX * 2,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.fillPath(path, QBrush(QColor(255, 255, 255)))

    def tick(self):
        elapsed = self.clock.elapsed()
        if elapsed >= DURATION_MS:
            self.anim.stop()
            self.close()
            QApplication.quit()
            return
        f = elapsed / DURATION_MS
        self.move(int(self.start_x + (self.end_x - self.start_x) * f), self.y)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("danmaku")
    danmaku = Danmaku()
    danmaku.setWindowTitle("danmaku")
    danmaku.show()
    # belt and braces: raw X11 shape call regardless of the Qt flag
    force_empty_input_shape(int(danmaku.winId()))
    print(int(danmaku.winId()), flush=True)
    danmaku.clock.start()
    danmaku.anim.start()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
