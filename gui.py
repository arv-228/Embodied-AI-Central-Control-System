"""
gui.py  —  EmbodiedAI 主界面
修复：
  1. 标题栏三点有实际功能（红=关闭 黄=最小化 绿=最大/还原）
  2. Avatar/Camera/Split 三键真实切换视图
  3. 右键菜单浅色主题，完全可读
  4. 全局字体放大，所有控件高度/间距同步放大
"""
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QComboBox, QLineEdit, QPushButton, QLabel,
    QCheckBox, QFrame, QSizePolicy, QProgressBar,
    QApplication, QMenu, QAction, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QPainter, QBrush

# ── 色彩 token ──────────────────────────────────────────────────────────────────
BG_PAGE    = "#f5f4f0"
BG_WHITE   = "#ffffff"
BG_SURFACE = "#fafaf8"
BG_HOVER   = "#f0efe9"

BORDER_LIGHT = "#e8e5de"
BORDER_MID   = "#d8d5cc"

TEXT_PRIMARY   = "#1a1a18"
TEXT_SECONDARY = "#6b6b64"
TEXT_MUTED     = "#aaa89e"

ACCENT_BLACK = "#1a1a18"
ACCENT_OK    = "#1e8a3e"
ACCENT_INFO  = "#1a6ab5"
ACCENT_WARN  = "#c96a10"
ACCENT_ERR   = "#c0392b"
ACCENT_SYS   = "#888880"

DOT_RED    = "#ff5f56"
DOT_YELLOW = "#febc2e"
DOT_GREEN  = "#28c840"

# ── 字体 / 尺寸 token ──────────────────────────────────────────────────────────
FS_XS   = "11px"
FS_SM   = "14px"
FS_BASE = "15px"
FS_LG   = "18px"

H_INPUT    = 44
H_VOICE    = 44
H_COMBO    = 36
H_TITLEBAR = 52
H_LOG_HDR  = 48
H_SYS_BAR  = 52
H_CTRL     = 200

# ── 右键菜单 QSS（浅色） ────────────────────────────────────────────────────────
MENU_QSS = f"""
QMenu {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 8px;
    padding: 4px;
    color: {TEXT_PRIMARY};
    font-size: {FS_SM};
}}
QMenu::item {{
    padding: 8px 22px 8px 14px;
    border-radius: 5px;
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QMenu::item:selected {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QMenu::item:disabled {{
    color: {TEXT_MUTED};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER_LIGHT};
    margin: 4px 8px;
}}
"""

GLOBAL_QSS = f"""
QWidget {{
    font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", Arial, sans-serif;
    font-size: {FS_SM};
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QScrollBar:vertical {{
    width: 6px; background: transparent; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_LIGHT}; border-radius: 3px; min-height: 40px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QComboBox {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 7px;
    padding: 5px 12px;
    color: {TEXT_PRIMARY};
    font-size: {FS_SM};
    min-height: {H_COMBO}px;
}}
QComboBox:hover {{ border-color: {BORDER_MID}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 7px;
    selection-background-color: {BG_HOVER};
    selection-color: {TEXT_PRIMARY};
    outline: none;
    font-size: {FS_SM};
    padding: 4px;
}}
QToolTip {{
    background: {BG_WHITE};
    border: 1px solid {BORDER_LIGHT};
    color: {TEXT_PRIMARY};
    font-size: {FS_SM};
    padding: 5px 10px;
    border-radius: 5px;
}}
"""


# ── 辅助组件 ────────────────────────────────────────────────────────────────────
class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER_LIGHT}; border: none;")


class _VDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFixedWidth(1)
        self.setStyleSheet(f"background: {BORDER_LIGHT}; border: none;")


class _SysDot(QPushButton):
    """macOS 风格圆点，有实际功能"""
    def __init__(self, color: str, tip: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tip)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 7px;
                border: 0.5px solid rgba(0,0,0,0.10);
            }}
            QPushButton:hover {{
                border: 1.5px solid rgba(0,0,0,0.25);
            }}
        """)


class _StatBar(QWidget):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"font-size: {FS_XS}; color: {TEXT_MUTED};")
        self._val = QLabel("—")
        self._val.setStyleSheet(f"font-size: {FS_XS}; color: {TEXT_MUTED};")
        top.addWidget(self._lbl)
        top.addStretch()
        top.addWidget(self._val)
        lay.addLayout(top)

        self._bar = QProgressBar()
        self._bar.setFixedHeight(4)
        self._bar.setTextVisible(False)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setStyleSheet(f"""
            QProgressBar {{ background: {BORDER_LIGHT}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
        """)
        lay.addWidget(self._bar)

    def update_stat(self, value: int, text: str = ""):
        self._bar.setValue(max(0, min(100, value)))
        self._val.setText(text or f"{value}%")


class _WaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 22)
        self._phase = 0.0
        self._active = True
        self._heights = [6, 12, 18, 10, 15, 8]
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(80)

    def _tick(self):
        import math
        self._phase += 0.25
        self._heights = [int(5 + 13 * abs(math.sin(self._phase + i * 0.55))) for i in range(6)]
        self.update()

    def set_active(self, v: bool):
        self._active = v

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(ACCENT_INFO) if self._active else QColor(TEXT_MUTED)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        bw, gap = 4, 3
        total = 6 * bw + 5 * gap
        x0 = (self.width() - total) // 2
        cy = self.height() // 2
        for i, h in enumerate(self._heights):
            p.drawRoundedRect(x0 + i * (bw + gap), cy - h // 2, bw, h, 2, 2)
        p.end()


class _AvatarWidget(QWidget):
    """
    Avatar 区域，持有外部 camera_label 引用。
    三种模式：
      MODE_AVATAR(0)  — 只显示 Avatar 圆框，camera_label 隐藏
      MODE_CAMERA(1)  — 只显示 camera_label，Avatar 圆框隐藏
      MODE_SPLIT(2)   — Avatar 圆框 + camera_label 同时显示（上下各半）
    """
    MODE_AVATAR = 0
    MODE_CAMERA = 1
    MODE_SPLIT  = 2

    def __init__(self, camera_label: QLabel, parent=None):
        super().__init__(parent)
        self._camera_label = camera_label
        self._mode = self.MODE_AVATAR
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build()
        # 初始应用模式
        self._apply_mode()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        container = QWidget()
        container.setStyleSheet(f"background: {BG_WHITE};")
        root.addWidget(container)

        lay = QVBoxLayout(container)
        lay.setContentsMargins(20, 16, 20, 12)
        lay.setSpacing(0)

        # HUD 顶行
        hud = QHBoxLayout()
        self._hud_left  = QLabel("AVATAR · CAM")
        self._live_dot  = QLabel("● LIVE")
        self._hud_right = QLabel("YOLOv8  待机")
        for w in (self._hud_left, self._hud_right):
            w.setStyleSheet(f"font-size: {FS_XS}; color: {TEXT_MUTED}; background: transparent; border: none;")
        self._live_dot.setStyleSheet(f"font-size: {FS_XS}; color: {ACCENT_OK}; background: transparent; border: none;")
        self._hud_right.setAlignment(Qt.AlignRight)
        hud.addWidget(self._hud_left)
        hud.addWidget(self._live_dot)
        hud.addStretch()
        hud.addWidget(self._hud_right)
        lay.addLayout(hud)
        lay.addStretch()

        # 中央 Avatar 部分（可被整体 show/hide）
        self._avatar_center = QWidget()
        self._avatar_center.setStyleSheet("background: transparent;")
        ac = QVBoxLayout(self._avatar_center)
        ac.setAlignment(Qt.AlignCenter)
        ac.setSpacing(16)

        ring = QWidget()
        ring.setFixedSize(190, 190)
        ring.setStyleSheet(f"""
            QWidget {{
                background: {BG_WHITE};
                border: 2px solid {BORDER_MID};
                border-radius: 95px;
            }}
        """)
        rl = QVBoxLayout(ring)
        rl.setAlignment(Qt.AlignCenter)
        rl.setContentsMargins(0, 0, 0, 0)
        emoji = QLabel("🤖")
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 64px; border: none; background: transparent;")
        rl.addWidget(emoji)

        ch = QHBoxLayout()
        ch.setAlignment(Qt.AlignCenter)
        ch.addWidget(ring)
        ac.addLayout(ch)

        self._name_lbl = QLabel("小智")
        self._name_lbl.setAlignment(Qt.AlignCenter)
        self._name_lbl.setStyleSheet(
            f"font-size: {FS_LG}; font-weight: 500; color: {TEXT_PRIMARY}; "
            f"letter-spacing: 1px; border: none; background: transparent;"
        )
        self._state_lbl = QLabel("LISTENING")
        self._state_lbl.setAlignment(Qt.AlignCenter)
        self._state_lbl.setStyleSheet(
            f"font-size: {FS_XS}; color: {TEXT_MUTED}; letter-spacing: 2px; "
            f"border: none; background: transparent;"
        )
        ac.addWidget(self._name_lbl)
        ac.addWidget(self._state_lbl)

        center_h = QHBoxLayout()
        center_h.setAlignment(Qt.AlignCenter)
        center_h.addWidget(self._avatar_center)
        lay.addLayout(center_h)
        lay.addStretch()

        # 视图切换 tabs
        tab_wrap = QWidget()
        tab_wrap.setStyleSheet(f"""
            QWidget {{
                background: {BG_PAGE};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 9px;
            }}
        """)
        tab_inner = QHBoxLayout(tab_wrap)
        tab_inner.setContentsMargins(4, 4, 4, 4)
        tab_inner.setSpacing(2)

        self._view_tabs = []
        for i, name in enumerate(["Avatar", "Camera", "Split"]):
            btn = QPushButton(name)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._switch_mode(idx))
            self._view_tabs.append(btn)
            tab_inner.addWidget(btn)

        tab_row = QHBoxLayout()
        tab_row.setAlignment(Qt.AlignCenter)
        tab_row.addWidget(tab_wrap)
        lay.addLayout(tab_row)
        lay.addSpacing(8)

        self._refresh_tab_styles()

    def _switch_mode(self, mode: int):
        self._mode = mode
        self._refresh_tab_styles()
        self._apply_mode()

    def _refresh_tab_styles(self):
        for i, btn in enumerate(self._view_tabs):
            if i == self._mode:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {BG_WHITE};
                        color: {TEXT_PRIMARY};
                        border: 1px solid {BORDER_LIGHT};
                        border-radius: 6px;
                        font-size: {FS_SM};
                        font-weight: 500;
                        padding: 0 18px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {TEXT_MUTED};
                        border: none;
                        border-radius: 6px;
                        font-size: {FS_SM};
                        padding: 0 18px;
                    }}
                    QPushButton:hover {{
                        color: {TEXT_SECONDARY};
                        background: rgba(0,0,0,0.04);
                    }}
                """)

    def _apply_mode(self):
        cam = self._camera_label
        av  = self._avatar_center

        if self._mode == self.MODE_AVATAR:
            av.show()
            cam.hide()
        elif self._mode == self.MODE_CAMERA:
            av.hide()
            cam.show()
        else:  # SPLIT
            av.show()
            cam.show()

    def set_state(self, state: str):
        self._state_lbl.setText(state.upper())


# ── 主窗口 ─────────────────────────────────────────────────────────────────────
class EmbodiedUI(QWidget):
    language_changed      = pyqtSignal(str)
    text_input_sent       = pyqtSignal(str)
    skill_import_requested = pyqtSignal(str)   # 用户手动导入 skill，传入路径

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EmbodiedAI")
        self.resize(1360, 860)
        self.setMinimumSize(960, 640)
        self._setup_ui()
        self._set_vision_state(True)

    def _setup_ui(self):
        self.setObjectName("root")
        self.setStyleSheet(GLOBAL_QSS + f"#root {{ background: {BG_PAGE}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_titlebar())
        root.addWidget(_Divider())
        root.addLayout(self._build_body(), 1)

    # ── 标题栏 ──────────────────────────────────────────────────────────────────
    def _build_titlebar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(H_TITLEBAR)
        bar.setStyleSheet(f"background: {BG_WHITE};")

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(8)

        # 三点按钮 —— 有实际操作
        dot_red = _SysDot(DOT_RED,    "关闭窗口")
        dot_yel = _SysDot(DOT_YELLOW, "最小化")
        dot_grn = _SysDot(DOT_GREEN,  "最大化 / 还原")
        dot_red.clicked.connect(self.close)
        dot_yel.clicked.connect(self.showMinimized)
        dot_grn.clicked.connect(self._toggle_maximize)
        lay.addWidget(dot_red)
        lay.addWidget(dot_yel)
        lay.addWidget(dot_grn)
        lay.addSpacing(12)

        title = QLabel("EmbodiedAI")
        title.setStyleSheet(
            f"font-size: {FS_BASE}; font-weight: 500; color: {TEXT_PRIMARY}; letter-spacing: 0.3px;"
        )
        lay.addWidget(title)
        lay.addStretch()

        self._model_badge = QLabel("—")
        self._model_badge.setStyleSheet(f"""
            background: {BG_PAGE};
            border: 1px solid {BORDER_LIGHT};
            border-radius: 6px;
            padding: 4px 14px;
            font-size: {FS_SM};
            color: {TEXT_SECONDARY};
        """)
        lay.addWidget(self._model_badge)

        self._clock = QLabel()
        self._clock.setStyleSheet(f"font-size: {FS_SM}; color: {TEXT_MUTED};")
        self._clock.setFixedWidth(70)
        self._clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self._clock)

        clk = QTimer(self)
        clk.timeout.connect(self._tick_clock)
        clk.start(1000)
        self._tick_clock()
        return bar

    def _toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def _tick_clock(self):
        self._clock.setText(time.strftime("%H:%M:%S"))

    # ── 主体 ────────────────────────────────────────────────────────────────────
    def _build_body(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(self._build_left(), 7)
        lay.addWidget(_VDivider())
        lay.addLayout(self._build_right(), 3)
        return lay

    # ── 左侧 ────────────────────────────────────────────────────────────────────
    def _build_left(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # camera_label 先建，传给 _AvatarWidget 管理
        self.camera_label = QLabel("摄像头未启动")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet(
            f"background: {BG_WHITE}; color: {TEXT_MUTED}; font-size: {FS_BASE};"
        )
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_label.hide()

        # _AvatarWidget 内部管理两个 widget 的显示/隐藏
        self._avatar_widget = _AvatarWidget(self.camera_label)

        # 容器：让 avatar_widget 和 camera_label 在同一竖直空间里
        view_box = QWidget()
        view_box.setStyleSheet(f"background: {BG_WHITE};")
        vb_lay = QVBoxLayout(view_box)
        vb_lay.setContentsMargins(0, 0, 0, 0)
        vb_lay.setSpacing(0)
        vb_lay.addWidget(self._avatar_widget)
        vb_lay.addWidget(self.camera_label)

        lay.addWidget(view_box, 1)
        lay.addWidget(_Divider())
        lay.addWidget(self._build_input_zone())
        return lay

    # ── 输入区 ──────────────────────────────────────────────────────────────────
    def _build_input_zone(self) -> QWidget:
        zone = QWidget()
        zone.setFixedHeight(136)
        zone.setStyleSheet(f"background: {BG_SURFACE};")

        lay = QVBoxLayout(zone)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(12)

        # 语音状态行
        voice_row = QWidget()
        voice_row.setFixedHeight(H_VOICE)
        voice_row.setStyleSheet(f"""
            QWidget {{
                background: {BG_WHITE};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 9px;
            }}
        """)
        vr = QHBoxLayout(voice_row)
        vr.setContentsMargins(12, 0, 10, 0)
        vr.setSpacing(10)

        self._wave = _WaveWidget()
        vr.addWidget(self._wave)

        self._voice_status = QLabel("zh-CN · 待命中...")
        self._voice_status.setStyleSheet(
            f"font-size: {FS_SM}; color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        vr.addWidget(self._voice_status, 1)

        # 隐藏 QCheckBox（main.py 用 isChecked() 判断视觉开关）
        self.vision_switch = QCheckBox()
        self.vision_switch.hide()

        vis_wrap = QWidget()
        vis_wrap.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border: 1px solid {BORDER_LIGHT};
                border-radius: 7px;
            }}
        """)
        vi = QHBoxLayout(vis_wrap)
        vi.setContentsMargins(0, 0, 0, 0)
        vi.setSpacing(0)

        self.btn_vision_on  = QPushButton("ON")
        self.btn_vision_off = QPushButton("OFF")
        for b in (self.btn_vision_on, self.btn_vision_off):
            b.setFixedSize(50, 34)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_vision_on.clicked.connect(lambda: self._set_vision_state(True))
        self.btn_vision_off.clicked.connect(lambda: self._set_vision_state(False))
        vi.addWidget(self.btn_vision_on)
        vi.addWidget(self.btn_vision_off)
        vr.addWidget(vis_wrap)
        lay.addWidget(voice_row)

        # 文字输入行
        cmd = QHBoxLayout()
        cmd.setSpacing(10)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入指令，或直接说话...")
        self.chat_input.setFixedHeight(H_INPUT)
        self.chat_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_WHITE};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 9px;
                padding: 0 16px;
                font-size: {FS_BASE};
                color: {TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border-color: {BORDER_MID}; }}
        """)
        self.chat_input.returnPressed.connect(self._send_text)

        self.btn_send = QPushButton("执行")
        self.btn_send.setFixedSize(80, H_INPUT)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_BLACK};
                color: white;
                border: none;
                border-radius: 9px;
                font-size: {FS_BASE};
                font-weight: 500;
            }}
            QPushButton:hover   {{ background: #2e2e2c; }}
            QPushButton:pressed {{ background: #000000; }}
        """)
        self.btn_send.clicked.connect(self._send_text)

        cmd.addWidget(self.chat_input)
        cmd.addWidget(self.btn_send)
        lay.addLayout(cmd)
        return zone

    # ── 右侧 ────────────────────────────────────────────────────────────────────
    def _build_right(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 日志头
        log_hdr = QWidget()
        log_hdr.setFixedHeight(H_LOG_HDR)
        log_hdr.setStyleSheet(f"background: {BG_WHITE};")
        hh = QHBoxLayout(log_hdr)
        hh.setContentsMargins(18, 0, 18, 0)
        lbl_h = QLabel("SYSTEM LOG")
        lbl_h.setStyleSheet(
            f"font-size: {FS_XS}; font-weight: 500; color: {TEXT_MUTED}; letter-spacing: 1.5px;"
        )
        self._log_count = QLabel("0 条")
        self._log_count.setStyleSheet(f"font-size: {FS_XS}; color: {TEXT_MUTED};")
        hh.addWidget(lbl_h)
        hh.addStretch()
        hh.addWidget(self._log_count)
        lay.addWidget(log_hdr)
        lay.addWidget(_Divider())

        # 日志体
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_WHITE};
                border: none;
                padding: 10px 16px;
                font-family: "Consolas", "JetBrains Mono", "Courier New", monospace;
                font-size: {FS_SM};
                color: {TEXT_SECONDARY};
                line-height: 1.6;
            }}
        """)
        self.log_box.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        # 浅色自定义右键菜单
        self.log_box.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_box.customContextMenuRequested.connect(self._show_log_menu)

        self._log_lines = 0
        lay.addWidget(self.log_box, 1)
        lay.addWidget(_Divider())
        lay.addWidget(self._build_controls())
        lay.addWidget(_Divider())
        lay.addWidget(self._build_sys_bar())
        return lay

    def _show_log_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)

        has_sel = self.log_box.textCursor().hasSelection()

        act_copy = QAction("复制", self)
        act_copy.setEnabled(has_sel)
        act_copy.triggered.connect(self.log_box.copy)

        act_all = QAction("全选", self)
        act_all.triggered.connect(self.log_box.selectAll)

        act_clear = QAction("清空日志", self)
        act_clear.triggered.connect(self._clear_log)

        menu.addAction(act_copy)
        menu.addAction(act_all)
        menu.addSeparator()
        menu.addAction(act_clear)
        menu.exec_(self.log_box.mapToGlobal(pos))

    def _clear_log(self):
        self.log_box.clear()
        self._log_lines = 0
        self._log_count.setText("0 条")

    # ── 控件区 ──────────────────────────────────────────────────────────────────
    def _build_controls(self) -> QWidget:
        ctrl = QWidget()
        ctrl.setFixedHeight(H_CTRL)
        ctrl.setStyleSheet(f"background: {BG_WHITE};")
        lay = QVBoxLayout(ctrl)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        def _row(lbl_txt, widget):
            r = QHBoxLayout()
            r.setSpacing(10)
            lb = QLabel(lbl_txt)
            lb.setFixedWidth(40)
            lb.setStyleSheet(f"font-size: {FS_SM}; color: {TEXT_MUTED};")
            r.addWidget(lb)
            r.addWidget(widget)
            return r

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["zh-CN (小晓)", "zh-HK (粤语)", "en-US"])
        self.lang_combo.currentTextChanged.connect(
            lambda t: self.language_changed.emit(t.split()[0])
        )
        lay.addLayout(_row("语音", self.lang_combo))

        self.model_combo = QComboBox()
        lay.addLayout(_row("大脑", self.model_combo))

        # ── Skill 区域 ──────────────────────────────────────────────────────────
        skill_row = QHBoxLayout()
        skill_row.setSpacing(8)

        lb_skill = QLabel("技能")
        lb_skill.setFixedWidth(40)
        lb_skill.setStyleSheet(f"font-size: {FS_SM}; color: {TEXT_MUTED};")

        self.skill_combo = QComboBox()
        self.skill_combo.addItem("── 无加载技能 ──")
        self.skill_combo.setToolTip("当前已扫描到的 Skill 列表")

        self._import_btn = QPushButton("导入")
        self._import_btn.setFixedSize(62, H_COMBO)
        self._import_btn.setCursor(Qt.PointingHandCursor)
        self._import_btn.setToolTip("导入 .skill 文件或含 SKILL.md 的文件夹")
        self._import_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER_MID};
                border-radius: 7px;
                font-size: {FS_SM};
                color: {TEXT_SECONDARY};
            }}
            QPushButton:hover {{ background: {BG_HOVER}; }}
        """)
        self._import_btn.clicked.connect(self._on_import_skill)

        skill_row.addWidget(lb_skill)
        skill_row.addWidget(self.skill_combo)
        skill_row.addWidget(self._import_btn)
        lay.addLayout(skill_row)

        # Skill 描述标签（选中 skill 时显示 description）
        self._skill_desc = QLabel("")
        self._skill_desc.setWordWrap(True)
        self._skill_desc.setStyleSheet(
            f"font-size: {FS_XS}; color: {TEXT_MUTED}; "
            f"padding: 4px 6px; background: {BG_SURFACE}; "
            f"border-radius: 5px; border: 1px solid {BORDER_LIGHT};"
        )
        self._skill_desc.setVisible(False)
        lay.addWidget(self._skill_desc)
        self.skill_combo.currentTextChanged.connect(self._on_skill_selected)

        mr = QHBoxLayout()
        mr.setSpacing(8)
        lb2 = QLabel("路径")
        lb2.setFixedWidth(40)
        lb2.setStyleSheet(f"font-size: {FS_SM}; color: {TEXT_MUTED};")

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("手动挂载模型路径...")
        self.input_path.setFixedHeight(H_COMBO)
        self.input_path.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_SURFACE};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 7px;
                padding: 0 10px;
                font-size: {FS_SM};
                color: {TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border-color: {BORDER_MID}; }}
        """)

        self.btn_connect = QPushButton("挂载")
        self.btn_connect.setFixedSize(62, H_COMBO)
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER_MID};
                border-radius: 7px;
                font-size: {FS_SM};
                color: {TEXT_SECONDARY};
            }}
            QPushButton:hover {{ background: {BG_HOVER}; }}
        """)
        mr.addWidget(lb2)
        mr.addWidget(self.input_path)
        mr.addWidget(self.btn_connect)
        lay.addLayout(mr)
        return ctrl

    def _on_import_skill(self):
        """弹出文件对话框，支持选 .skill 文件或含 SKILL.md 的文件夹"""
        # 先尝试选文件
        path, _ = QFileDialog.getOpenFileName(
            self, "导入 Skill 文件", "",
            "Skill 文件 (*.skill);;所有文件 (*)"
        )
        if not path:
            # 用户取消或想选文件夹
            path = QFileDialog.getExistingDirectory(
                self, "或选择含 SKILL.md 的文件夹", ""
            )
        if path:
            self.skill_import_requested.emit(path)

    def _on_skill_selected(self, display_name: str):
        """skill 下拉切换时，更新描述标签"""
        if display_name.startswith("──"):
            self._skill_desc.setVisible(False)
            return
        try:
            from skill_manager import skill_manager as _sm
            skill = _sm.get_by_display_name(display_name)
            if skill:
                desc = skill.description[:120] + ("…" if len(skill.description) > 120 else "")
                self._skill_desc.setText(desc)
                self._skill_desc.setVisible(True)
                return
        except Exception:
            pass
        self._skill_desc.setVisible(False)

    # ── 公开接口：供 main.py 调用 ────────────────────────────────────────────────
    def add_skill_item(self, display_name: str):
        """后台扫描完成后，往 skill_combo 里添加一条"""
        # 移除占位项
        if self.skill_combo.count() == 1 and self.skill_combo.itemText(0).startswith("──"):
            self.skill_combo.clear()
        # 去重
        all_items = [self.skill_combo.itemText(i) for i in range(self.skill_combo.count())]
        if display_name not in all_items:
            self.skill_combo.addItem(display_name)

    # ── 资源条 ──────────────────────────────────────────────────────────────────
    def _build_sys_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(H_SYS_BAR)
        bar.setStyleSheet(f"background: {BG_SURFACE};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(14)
        self._stat_cpu = _StatBar("CPU", ACCENT_INFO)
        self._stat_ram = _StatBar("RAM", ACCENT_OK)
        self._stat_gpu = _StatBar("GPU", ACCENT_WARN)
        lay.addWidget(self._stat_cpu)
        lay.addWidget(_VDivider())
        lay.addWidget(self._stat_ram)
        lay.addWidget(_VDivider())
        lay.addWidget(self._stat_gpu)
        return bar

    # ── 公开接口 ─────────────────────────────────────────────────────────────────
    def add_log(self, text: str):
        ts = time.strftime("%H:%M:%S")

        if any(k in text for k in ("✅", "已打开", "已启动", "就绪", "完成", "成功", "注入")):
            color = ACCENT_OK
        elif any(k in text for k in ("❌", "失败", "异常", "错误", "crash")):
            color = ACCENT_ERR
        elif any(k in text for k in ("⚠️", "切换", "接管", "RPA", "正在", "🔄", "🦾")):
            color = ACCENT_WARN
        elif any(k in text for k in ("🤖", "💬", "回复", "回答")):
            color = ACCENT_INFO
        elif any(k in text for k in ("具身", "启动", "控制台", "初始化")):
            color = ACCENT_SYS
        else:
            color = TEXT_SECONDARY

        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = (
            f'<span style="color:{TEXT_MUTED};font-size:{FS_XS};">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};font-size:{FS_SM};">{safe}</span>'
        )
        self.log_box.append(html)
        self._log_lines += 1
        self._log_count.setText(f"{self._log_lines} 条")
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

        if any(k in text for k in ("大脑已就绪", "大脑就绪", "切换大脑")):
            try:
                cur = self.model_combo.currentText()
                if cur:
                    self._model_badge.setText(cur)
            except Exception:
                pass

    def update_sys_stats(self, cpu: int, ram_gb: float, gpu: int):
        self._stat_cpu.update_stat(cpu, f"{cpu}%")
        self._stat_ram.update_stat(int(min(ram_gb / 32 * 100, 100)), f"{ram_gb:.1f}G")
        self._stat_gpu.update_stat(gpu, f"{gpu}%")

    def set_voice_status(self, text: str):
        self._voice_status.setText(text)

    def set_avatar_state(self, state: str):
        self._avatar_widget.set_state(state)

    # ── 内部逻辑 ─────────────────────────────────────────────────────────────────
    def _set_vision_state(self, state: bool):
        self.vision_switch.setChecked(state)
        self._wave.set_active(state)

        on_active = f"""
            QPushButton {{
                background: {ACCENT_OK}; color: white; border: none;
                border-top-left-radius: 6px; border-bottom-left-radius: 6px;
                font-size: {FS_SM}; font-weight: 500;
            }}
        """
        off_active = f"""
            QPushButton {{
                background: {ACCENT_ERR}; color: white; border: none;
                border-top-right-radius: 6px; border-bottom-right-radius: 6px;
                font-size: {FS_SM}; font-weight: 500;
            }}
        """
        inactive_l = f"""
            QPushButton {{
                background: transparent; color: {TEXT_MUTED}; border: none;
                border-top-left-radius: 6px; border-bottom-left-radius: 6px;
                font-size: {FS_SM};
            }}
            QPushButton:hover {{ color: {TEXT_SECONDARY}; background: rgba(0,0,0,0.04); }}
        """
        inactive_r = f"""
            QPushButton {{
                background: transparent; color: {TEXT_MUTED}; border: none;
                border-top-right-radius: 6px; border-bottom-right-radius: 6px;
                font-size: {FS_SM};
            }}
            QPushButton:hover {{ color: {TEXT_SECONDARY}; background: rgba(0,0,0,0.04); }}
        """
        if state:
            self.btn_vision_on.setStyleSheet(on_active)
            self.btn_vision_off.setStyleSheet(inactive_r)
        else:
            self.btn_vision_on.setStyleSheet(inactive_l)
            self.btn_vision_off.setStyleSheet(off_active)

    def _send_text(self):
        text = self.chat_input.text().strip()
        if text:
            self.text_input_sent.emit(text)
            self.chat_input.clear()