<p align="right"><a href="README.md">English</a> | 简体中文</p>

<p align="center"><img src="assets/logo.svg" width="112" height="112" alt="danmaku 标志"></p>

<h1 align="center">danmaku</h1>

<p align="center"><sub>一个跑在 X11 桌面上的小型 PyQt5 弹幕引擎</sub></p>

<p align="center"><b>B 站式弹幕从桌面划过——背景透明、始终置顶、鼠标可穿透。</b></p>

![真实 X11 桌面上的弹幕风暴](storm_t16.png)

<p align="center"><i>第 16 秒的风暴演示（2560×1440 桌面）。整层弹幕是一个点击穿透的全屏窗口，
底下的终端仍可正常操作。</i></p>

## 快速开始

需要 Python 3、PyQt5、X11 会话，以及一款中文字体。演示默认使用
`Noto Sans CJK SC`（Debian/Ubuntu 上是 `fonts-noto-cjk` 包）；`danmaku.py` 也接受
`--font FAMILY` 换成别的字体。

```bash
git clone https://github.com/ZisIsNotZis/danmaku.git
cd danmaku
python3 -m pip install -r requirements.txt
python3 danmaku.py
```

一条弹幕会在 10 秒内横穿屏幕，然后浮层自动退出。换成自己的文字和节奏：

```bash
python3 danmaku.py "前方高能！" --duration 6 --font-size 48 --vertical 0.5
```

没有窗口边框，没有背景，也不占任务栏：屏幕上只有带描边的文字从右向左飞过，
鼠标点击照常落到下层应用。

## 现在能做什么

- **按需放出一条弹幕。** `danmaku.py` 接受文字、字体、字号、横穿时长和垂直位置。
- **按时间轴播放。** `danmaku_engine.py script timeline_test.json` 实时播放 JSON
  时间轴，条目可以是小字或大字，可以是白色或彩色。
- **嵌入自己的程序。** `Engine.push(text, color, size)` 是对外接口；
  `danmaku_engine.py daemon` 让引擎常驻，供宿主代码调用。
- **紧贴排布。** 弹幕进入最靠上、且不会追尾的那条轨道；前一条离场时，间距刚好收为零。
- **大字弹幕。** 大字占用两条轨道（没有空位时退回小字），不会压到下一行。
- **点击穿透。** Qt 的 `WindowTransparentForInput` 加一层原生 X11
  输入区域兜底；验证脚本会打印空的输入区域。
- **弹幕风暴。** `danmaku_storm.py` 在一块全屏窗口上以约每秒 15 条的速度铺满屏幕，
  这是引擎开发时用来对照的参考模型。
- **可复现的截图。** 三个脚本负责启动演示、检查窗口并用 `ffmpeg` 抓帧，其中
  `verify_engine.sh` 还会从 `/proc` 采样引擎的 CPU 时间。

## 架构

引擎绕开了常见的全屏重绘。最直观的做法——一块半透明 ARGB 全屏窗口，每秒重绘
60 次——每一帧都要清屏并重画整块屏幕。这里每条弹幕只**栅格化一次**，放进自己的
小 pixmap 窗口；定时器只移动这些窗口，X11 侧就是一条 `XMoveWindow` 请求，既不重绘
文字，也不重新排版。

两条规则保证轨道干净：

- 每条弹幕都用固定的存活时间 `T` 横穿全屏，所以宽度越长速度越快：
  `speed = (W + w) / T`。
- 只有当
  `delta >= T * max(w_new, w_last) / (W + max(w_new, w_last))`
  成立时，轨道才接纳新弹幕。前一条离开的瞬间间距刚好归零，因此轨道既紧凑又不会
  追尾；由传递性可知，只检查该轨道最近一条弹幕就够了。

`danmaku.py` 与 `danmaku_storm.py` 使用同一套点击穿透机制：让 X11 输入区域为空，
先通过 Qt 设置，再用 `XShapeCombineRectangles` 兜底。

| 文件 | 作用 |
| --- | --- |
| `danmaku.py` | 单条弹幕浮层，也是最小的完整示例。 |
| `danmaku_engine.py` | 轨道分配、大字弹幕、pixmap 窗口、时间轴播放与常驻模式。 |
| `danmaku_storm.py` | 单块全屏窗口上的高密度风暴。 |
| `timeline_test.json` | 示例时间轴：小字、大字、彩色和连发弹幕。 |
| `verify_*.sh` | 启动、检查并截图各自的演示。 |
| `assets/logo.svg` | 上方标志。 |
| `docs/project-status.md` | 里程碑证据、设计取舍与边界。 |

## 如何开发

项目没有构建步骤、锁文件、CI 或测试套件。三个演示和三个验证脚本就是测试手段。

```bash
python3 danmaku.py                    # 单条弹幕浮层
python3 danmaku_engine.py script timeline_test.json --duration 30
python3 danmaku_engine.py daemon      # 引擎常驻，供嵌入代码调用
python3 danmaku_storm.py              # 30 秒内约每秒 15 条
```

检查并截图：

```bash
./verify_flight.sh    # -> shot_t2.png, shot_t5.png
./verify_engine.sh    # -> eng_t6.png, eng_t20.png，以及 CPU 采样
./verify_storm.sh     # -> storm_t6.png, storm_t16.png, storm_t26.png
```

脚本需要 `ffmpeg`、`xwininfo` 和 `xdpyinfo`；如果装了 `xdotool`，
`verify_engine.sh` 也会用它检查窗口。会话不是 `:1` 时设置 `DISPLAY`；
`python3` 不是装有 PyQt5 的解释器时设置 `PYTHON`。运行脚本会覆盖仓库里已提交的截图。

点击穿透依赖 X11 输入区域，因此这个浮层只支持 X11，不能在 Wayland 或其他显示
服务器上运行。

## 如何贡献

欢迎小修复和可移植性补丁，见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。请保持 X11
原生实现，运行时依赖只保留 PyQt5，并在提交 PR 前运行相关的验证脚本。项目使用
AGPL-3.0 许可。

## 路线图

### 已实现

- 单条弹幕浮层，支持文字、字体、字号、时长和位置参数。
- 引擎 v2：每条弹幕一个 pixmap 窗口、紧贴排布、双轨道大字、时间轴播放与常驻接口。
- 单块全屏窗口上的风暴参考模型。
- Qt 加原生 X11 输入区域的点击穿透。
- 三个演示的验证脚本与已提交截图。

### 计划中

没有。这是一个已完结的里程碑（2026-09-29），以完整可用的状态保留，不再持续开发。
曾在这里的 AI 吐槽浮层已移至
[Backseat](https://github.com/ZisIsNotZis/backseat)，本仓库不再包含 AI 代码。

### 未来设想

如果后来有人接手，真正有意义的下一步是用 `wlr-layer-shell` 支持 Wayland——那是替换
X11 输入区域的实现，而不是在它外面再包一层。另一个方向是给常驻模式加一个轻量的
输入适配器（标准输入或本地套接字上的 JSON 行），这样不嵌入 Python 也能喂弹幕。
这两项都没有排期，也不构成承诺；以它原本的目标衡量，现在的引擎已经完整。

## 许可证

[GNU AGPL v3](LICENSE.md)，© 2026 ZisIsNotZis。
