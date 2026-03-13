import os
import time
import threading
import subprocess
import pyautogui
import pyperclip
import webbrowser
from screen_parser import ScreenParser

# 🚨 pywinauto 只做存在检测，不在模块级 import
# 实际使用时在工作线程内部 import，避免 CoInitialize(MTA) 污染 PyQt5 主线程
try:
    import importlib.util
    HAS_PYWINAUTO = importlib.util.find_spec("pywinauto") is not None
except Exception:
    HAS_PYWINAUTO = False

Application = None  # 延迟加载占位

# ============================================================
# 🦾 三层 RPA 架构：
#   第一层 pywinauto  — 原生 Win32 窗口控件 API，最稳最准
#   第二层 OCR视觉    — RapidOCR 截图识字，覆盖自定义 UI
#   第三层 pyautogui  — 鼠标键盘模拟，最后兜底
# ============================================================

class WindowManager:
    """封装 pywinauto 的窗口管理能力，方法内部才 import 避免污染主线程 COM"""

    def __init__(self, logger_func=None):
        self.logger = logger_func

    def _log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def find_window(self, title_keyword: str, timeout: float = 5.0):
        if not HAS_PYWINAUTO:
            return None
        import re as _re
        try:
            from pywinauto import Application
        except ImportError:
            return None
        for backend in ("uia", "win32"):
            try:
                app = Application(backend=backend).connect(
                    title_re=f".*{_re.escape(title_keyword)}.*", timeout=timeout
                )
                win = app.top_window()
                self._log(f"🪟 [pywinauto/{backend}] 找到窗口: {win.window_text()}")
                return win
            except Exception:
                continue
        self._log(f"⚠️ [pywinauto] 未找到窗口: [{title_keyword}]")
        return None

    def activate_window(self, title_keyword: str, timeout: float = 5.0) -> bool:
        win = self.find_window(title_keyword, timeout)
        if win:
            try:
                win.set_focus()
                time.sleep(0.3)
                self._log(f"✅ [pywinauto] 窗口激活: {title_keyword}")
                return True
            except Exception as e:
                self._log(f"⚠️ 激活失败: {e}")
        return False

    def click_control(self, title_keyword: str, control_text: str) -> bool:
        if not HAS_PYWINAUTO:
            return False
        win = self.find_window(title_keyword)
        if not win:
            return False
        try:
            ctrl = win.child_window(title=control_text, found_index=0)
            ctrl.click_input()
            self._log(f"🖱️ [pywinauto] 精确控件点击: [{control_text}]")
            return True
        except Exception:
            pass
        try:
            for ctrl in win.descendants():
                try:
                    if control_text.lower() in (ctrl.window_text() or "").lower():
                        ctrl.click_input()
                        self._log(f"🖱️ [pywinauto] 模糊控件命中: [{ctrl.window_text()}]")
                        return True
                except Exception:
                    continue
        except Exception as e:
            self._log(f"⚠️ [pywinauto] 控件遍历失败: {e}")
        return False

    def type_to_window(self, title_keyword: str, text: str) -> bool:
        if not HAS_PYWINAUTO:
            return False
        if not self.activate_window(title_keyword):
            return False
        try:
            from pywinauto.keyboard import send_keys
            pyperclip.copy(text)
            time.sleep(0.2)
            send_keys("^v")
            self._log(f"⌨️ [pywinauto] 输入: [{text[:30]}]")
            return True
        except Exception as e:
            self._log(f"⚠️ [pywinauto] 输入失败: {e}")
            return False

    def send_hotkey_to_window(self, title_keyword: str, hotkey_str: str) -> bool:
        if not HAS_PYWINAUTO:
            return False
        if not self.activate_window(title_keyword):
            return False
        try:
            from pywinauto.keyboard import send_keys
            key_map = {"ctrl": "^", "alt": "%", "shift": "+"}
            parts = hotkey_str.lower().split()
            converted = ""
            for p in parts:
                converted += key_map.get(p, p if len(p) == 1 else f"{{{p.upper()}}}")
            send_keys(converted)
            self._log(f"⌨️ [pywinauto] 快捷键: [{hotkey_str}] → [{converted}]")
            return True
        except Exception as e:
            self._log(f"⚠️ [pywinauto] 快捷键失败: {e}")
            return False

    def list_windows(self) -> list:
        if not HAS_PYWINAUTO:
            return []
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            return [w.window_text() for w in desktop.windows() if w.window_text()]
        except Exception:
            return []


class Automation:
    def __init__(self):
        self.logger = None
        self.eye = ScreenParser()
        self.wm = WindowManager()
        self._active_target = ""   # 当前宏目标程序名，供 click_text 使用

    def set_logger(self, logger_func):
        self.logger = logger_func
        self.eye.set_logger(logger_func)
        self.wm.logger = logger_func

    def _log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    # ----------------------------------------------------------
    # 🎯 三层 click_text 降级策略
    # ----------------------------------------------------------
    def _smart_click_text(self, target_text: str) -> bool:
        # 第一层：pywinauto 控件树
        if HAS_PYWINAUTO and self._active_target:
            if self.wm.click_control(self._active_target, target_text):
                return True
            self._log(f"  ⬇️ pywinauto 未命中，降级到 OCR 层...")

        # 第二层：OCR 视觉识别
        coords = self.eye.find_text_and_click_coords(target_text)
        if coords:
            pyautogui.moveTo(coords[0], coords[1], duration=0.3)
            pyautogui.click()
            self._log(f"  🎯 OCR 命中 [{target_text}] → {coords}")
            return True

        self._log(f"  ❌ 三层搜索全败，无法点击: [{target_text}]")
        return False

    # ----------------------------------------------------------
    # 🦾 主宏执行引擎
    # ----------------------------------------------------------
    def execute_dynamic_macro(self, target: str, macro_str: str):
        self._log(f"🦾 [万能机械臂] 正在接管，目标: {target}...")
        self._log(f"📜 载入动作序列: {macro_str}")
        self._active_target = target

        time.sleep(0.5)

        macro_str = (macro_str.replace('，', ',').replace('；', ',')
                              .replace(';', ',').replace('、', ','))
        actions = [a.strip() for a in macro_str.split(',')]

        for action in actions:
            if not action:
                continue
            try:
                al = action.lower()

                # wait N
                if al.startswith("wait"):
                    parts = action.split()
                    sec = float(parts[1]) if len(parts) > 1 else 1.0
                    time.sleep(sec)
                    self._log(f"  ⏱️ 等待 {sec}s")

                # focus 窗口标题  ← 新动作，把指定窗口拉到前台
                elif al.startswith("focus"):
                    win_title = action[5:].strip()
                    if not self.wm.activate_window(win_title):
                        self._log(f"  ⚠️ focus 失败: [{win_title}]")

                # win_click 控件文字  ← 新动作，直接操控 Win32 控件
                elif al.startswith("win_click"):
                    ctrl_text = action[9:].strip()
                    if not self.wm.click_control(self._active_target, ctrl_text):
                        self._log(f"  ⚠️ win_click 未找到控件: [{ctrl_text}]")

                # click_text 屏幕文字（三层降级）
                elif al.startswith("click_text"):
                    target_text = action[10:].strip()
                    if target_text:
                        self._smart_click_text(target_text)

                # type 文字（pywinauto 优先，降级剪贴板）
                elif al.startswith("type"):
                    text = action[4:].strip()
                    if text:
                        typed = False
                        if HAS_PYWINAUTO and self._active_target:
                            typed = self.wm.type_to_window(self._active_target, text)
                        if not typed:
                            pyperclip.copy(text)
                            time.sleep(0.3)
                            pyautogui.hotkey('ctrl', 'v')
                            self._log(f"  ⌨️ [剪贴板] 输入: [{text[:30]}]")

                # hotkey 键1 键2（pywinauto 优先）
                elif al.startswith("hotkey"):
                    keys = action.split()[1:]
                    hk_str = " ".join(keys)
                    used_pw = False
                    if HAS_PYWINAUTO and self._active_target:
                        used_pw = self.wm.send_hotkey_to_window(self._active_target, hk_str)
                    if not used_pw:
                        pyautogui.hotkey(*keys)
                        self._log(f"  ⌨️ [pyautogui] 快捷键: {keys}")

                # press 单键
                elif al.startswith("press"):
                    parts = action.split()
                    if len(parts) > 1:
                        pyautogui.press(parts[1])
                        self._log(f"  🔘 按键: [{parts[1]}]")

                # screenshot  ← 新动作，截图存到 debug_screenshots/
                elif al.startswith("screenshot"):
                    try:
                        import datetime
                        os.makedirs("debug_screenshots", exist_ok=True)
                        fname = f"debug_screenshots/{datetime.datetime.now().strftime('%H%M%S')}.png"
                        pyautogui.screenshot(fname)
                        self._log(f"  📸 截图: {fname}")
                    except Exception as se:
                        self._log(f"  ⚠️ 截图失败: {se}")

                # run 程序路径  ← 新动作，subprocess 启动
                elif al.startswith("run"):
                    prog = action[3:].strip()
                    try:
                        subprocess.Popen(prog, shell=True)
                        self._log(f"  🚀 启动: [{prog}]")
                    except Exception as re_e:
                        self._log(f"  ❌ 启动失败: {re_e}")

                else:
                    self._log(f"  ⚠️ 未知动作（跳过）: [{action}]")

                self._log(f"  👉 动作完成: [{action}]")
                time.sleep(0.8)

            except Exception as e:
                self._log(f"  ❌ 动作异常 [{action}]: {e}")

        self._active_target = ""
        self._log("✅ 通用自动化操作流已全部执行完毕！")