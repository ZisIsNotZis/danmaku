#!/usr/bin/env python3
"""Danmaku storm overlay.

Model (classic fixed-lifetime engines):
- Every comment fully crosses the screen in LIFETIME_MS, regardless of width.
  => speed = (W + w) / LIFETIME_MS  (longer comments fly faster)
- Lane allocation guarantees zero overlap. With equal lifetimes, a longer
  (faster) new comment can catch up to a shorter (slower) one ahead, so the
  safe entry rule is:
      delta >= T * max(w_prev, w_new) / (W + max(w_prev, w_new))
  (delta = time since the lane's most recent comment started; checking only
  the most recent one suffices by transitivity).
- One full-screen borderless translucent window; empty X11 input shape makes
  the whole layer click-through.
"""
import ctypes
import ctypes.util
import random
import sys

from PyQt5.QtCore import QElapsedTimer, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget

FONT_SIZE = 22            # was 64 in the first flight; ~3x smaller
OUTLINE = 2               # outline thickness around glyphs
LIFETIME_MS = 8000        # fixed lifetime: full crossing time for every comment
SPAWN_MS = 60             # spawn tick
SPAWN_PROB = 0.9          # ~15 comments/s
STORM_MS = 30000          # how long new comments keep spawning
LANE_TOP = 90
LANE_BOTTOM_GAP = 60
LANE_PAD = 8              # vertical padding around text inside a lane
ENTRY_MARGIN_MS = 100     # extra safety margin for lane entry rule

TEXTS_SHORT = ["233", "草", "awsl", "泪目", "妙啊", "爷青回", "名场面", "好活", "有内味了"]
TEXTS_MED = ["前方高能！", "下次一定", "一键三连", "万恶之源", "红红火火恍恍惚惚",
             "膝盖中了一箭", "这就是青春啊", "圣地巡礼打卡", "这就是传说中的弹幕吗"]
TEXTS_LONG = ["前方高能！非战斗人员请速速撤离！！",
              "此生无悔入华夏，来世还做中国人！",
              "小时候不懂曲中意，再听已是曲中人",
              "弹幕护体！弹幕护体！弹幕护体！弹幕护体！",
              "曾经有一份真诚的爱情放在我面前，我没有珍惜"]

# classic bilibili palette, white dominant
COLORS = ["#FFFFFF"] * 6 + ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00",
                            "#00FFFF", "#00A1D6", "#FF69B4", "#FF00FF"]


def random_text():
    r = random.random()
    if r < 0.35:
        return random.choice(TEXTS_SHORT)
    if r < 0.75:
        return random.choice(TEXTS_MED)
    if r < 0.92:
        return random.choice(TEXTS_LONG)
    # variable-length runs, very danmaku
    return random.choice([
        lambda: "w" * random.randint(4, 24),
        lambda: "哈" * random.randint(4, 16),
        lambda: "hhh" * random.randint(2, 8),
        lambda: "2333" * random.randint(1, 6),
    ])()


def force_empty_input_shape(xid):
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
    xext.XShapeCombineRectangles(
        ctypes.c_void_p(dpy), ctypes.c_uint(xid), ctypes.c_int(2),
        0, 0, None, 0, ctypes.c_int(0), ctypes.c_int(0),
    )
    x11.XCloseDisplay(ctypes.c_void_p(dpy))
    return True


class Storm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
            | Qt.WindowTransparentForInput
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.W = screen.width()

        self.font = QFont("Noto Sans CJK SC", FONT_SIZE)
        self.font.setBold(True)
        self.fm = QFontMetrics(self.font)

        # lanes
        lane_h = self.fm.height() + LANE_PAD
        n_lanes = (screen.height() - LANE_TOP - LANE_BOTTOM_GAP) // lane_h
        self.lanes = [{"y": LANE_TOP + i * lane_h, "last_start": None, "last_w": 0}
                      for i in range(n_lanes)]

        self.active = []          # dicts: pm, w, x, y, start, v
        self.skipped = 0
        self.placed = 0
        self.clock = QElapsedTimer()

        self.spawner = QTimer(self)
        self.spawner.setInterval(SPAWN_MS)
        self.spawner.timeout.connect(self.try_spawn)

        self.anim = QTimer(self)
        self.anim.setInterval(16)
        self.anim.timeout.connect(self.tick)

    def make_pixmap(self, text, color):
        pad = OUTLINE + 2
        w = self.fm.horizontalAdvance(text) + 2 * pad
        h = self.fm.height() + 2 * pad
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addText(pad, pad + self.fm.ascent(), self.font, text)
        p.strokePath(path, QPen(QColor(0, 0, 0), OUTLINE * 2,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.fillPath(path, QBrush(QColor(color)))
        p.end()
        return pm, w

    def try_spawn(self):
        now = self.clock.elapsed()
        if now > STORM_MS:
            self.spawner.stop()
            return
        if random.random() > SPAWN_PROB:
            return
        text, color = random_text(), random.choice(COLORS)
        pm, w = self.make_pixmap(text, color)
        # lane entry rule: fixed lifetime => catch-up aware
        lane_ids = list(range(len(self.lanes)))
        random.shuffle(lane_ids)
        for i in lane_ids:
            lane = self.lanes[i]
            if lane["last_start"] is None:
                ok = True
            else:
                m = max(w, lane["last_w"])
                ok = (now - lane["last_start"]) >= \
                     LIFETIME_MS * m / (self.W + m) + ENTRY_MARGIN_MS
            if ok:
                lane["last_start"] = now
                lane["last_w"] = w
                self.active.append({
                    "pm": pm, "w": w, "x": self.W, "y": lane["y"], "start": now,
                    "v": (self.W + w) / LIFETIME_MS,
                })
                self.placed += 1
                return
        self.skipped += 1  # no free lane; drop like real engines do

    def tick(self):
        now = self.clock.elapsed()
        keep = []
        for d in self.active:
            age = now - d["start"]
            if age >= LIFETIME_MS:
                continue
            d["x"] = self.W - d["v"] * age
            keep.append(d)
        self.active = keep
        self.update()  # schedule paintEvent at ~60fps
        if now > STORM_MS + LIFETIME_MS + 500 and not self.active:
            QApplication.quit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Clear)  # no ghost trails
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        for d in self.active:
            p.drawPixmap(int(d["x"]), d["y"], d["pm"])


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("danmaku-storm")
    storm = Storm()
    storm.setWindowTitle("danmaku-storm")
    storm.show()
    force_empty_input_shape(int(storm.winId()))
    print(int(storm.winId()), flush=True)
    storm.clock.start()
    storm.spawner.start()
    storm.anim.start()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
