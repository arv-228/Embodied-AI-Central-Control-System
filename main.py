import sys, os, time, threading, queue, re, string, json, winreg
import ctypes 
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# 🚨 pywinauto 必须在主线程 CoInitialize 之前只做模块检查，不实际导入
# 否则它的 CoInitialize(MTA) 会破坏 PyQt5 的 STA COM 模型，导致 log_box 文本无法选中
try:
    import importlib.util
    HAS_PYWINAUTO = importlib.util.find_spec("pywinauto") is not None
except Exception:
    HAS_PYWINAUTO = False

import pyautogui
import pyperclip
import cv2

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from win32com.client import Dispatch

from gui import EmbodiedUI
from embodied_ai_model import brain_manager
from resource_manager import ResourceManager
from camera import CameraStream
from voice import VoiceRecognizer
from tts import TextToSpeech
from browser import BrowserControl

from permissions import check_permissions
from log_manager import OperationLogger
from commands import CommandLibrary
from network import NetworkAccess
from page_parser import PageParser
from code_detector import CodeDetector
from automation import Automation
from command_learning import CommandLearning
from ai_generator import AIGenerator
from model_config import ModelConfig
from model_selector import ModelSelector
from ai_training_guide import AITrainingGuide
# 🚨 缝合迭代版特性：导入技能管理器
from skill_manager import skill_manager

try: 
    import pynvml
    pynvml.nvmlInit()
    HAS_NVIDIA = True
except: 
    HAS_NVIDIA = False

VOICE_CORRECTION = {"地盘": "D盘", "第一盘": "D盘", "吸盘": "C盘", "洗盘": "C盘", "系统盘": "C盘", "西盘": "C盘"}

class MainController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ui = EmbodiedUI()
        
        self.voice_rec = VoiceRecognizer()
        self.tts = TextToSpeech()
        self.browser = BrowserControl()
        self.camera = CameraStream()
        self.res_manager = ResourceManager()
        
        self.logger = OperationLogger()
        self.cmd_lib = CommandLibrary()
        self.network = NetworkAccess()
        self.parser = PageParser()
        self.code_detector = CodeDetector()
        self.auto = Automation()
        self.learning = CommandLearning()
        self.ai_gen = AIGenerator()
        self.config = ModelConfig()
        self.model_selector = ModelSelector()
        self.guide = AITrainingGuide()

        self.voice_queue = queue.Queue()
        self.reply_queue = queue.Queue() 
        self.log_queue = queue.Queue() 
        
        # 🚨 重点：打通 UI 日志队列到底层脑控中心
        brain_manager.set_log_queue(self.log_queue)
        
        self.processing_event = threading.Event()
        
        self.apps = {}
        self.current_lang = "zh-CN"
        
        self.avatar_state_text = "待命中 (Listening...)"
        self.avatar_state_color = (0, 255, 0) 
        self.last_vram_time = 0
        
        self.WEB_AI_URLS = {
            "chatgpt": "https://chatgpt.com",
            "gemini": "https://gemini.google.com",
            "claude": "https://claude.ai",
            "grok": "https://x.com/i/grok"
        }

        self.INTENT_MAP = {
            "open_app":  ["打开", "启动", "运行", "开"],
            "search":    ["搜索", "查一下", "搜一下", "找"],
            "write_code":["写代码", "写脚本", "写爬虫", "编程"],
            "read_url":  ["读取", "总结网页", "打开网址"]
        }

        # 常用文件夹快捷映射（肌肉记忆级别，无需 LLM 推理）
        self.FOLDER_SHORTCUTS = {
            "c盘":  "C:\\",
            "d盘":  "D:\\",
            "e盘":  "E:\\",
            "f盘":  "F:\\",
            "桌面": os.path.join(os.path.expanduser("~"), "Desktop"),
            "下载": os.path.join(os.path.expanduser("~"), "Downloads"),
            "文档": os.path.join(os.path.expanduser("~"), "Documents"),
            "图片": os.path.join(os.path.expanduser("~"), "Pictures"),
            "音乐": os.path.join(os.path.expanduser("~"), "Music"),
            "视频": os.path.join(os.path.expanduser("~"), "Videos"),
        }
        
        self.ui.btn_connect.clicked.connect(self._handle_manual_path)
        self.ui.language_changed.connect(self._on_lang_change)
        self.ui.text_input_sent.connect(self._handle_text_input) 
        
        self.ui.model_combo.currentTextChanged.connect(self._on_model_changed)

        # 🚨 缝合迭代版特性：Skill 系统日志对接与信号绑定
        skill_manager._log = self.log_queue.put
        self.ui.skill_import_requested.connect(self._handle_skill_import)
        
        self._scan_system_apps()
        self.cmd_lib.commands.update(self.cmd_lib.load_log())
        
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._main_tick)
        
        self.auto.set_logger(self.log_queue.put)

    def _handle_text_input(self, text):
        self.ui.add_log(f"⌨️ 手动输入: {text}")
        self.voice_queue.put(text)

    def _on_model_changed(self, display_name):
        if not display_name or "请先" in display_name or "⏳" in display_name:
            return
        self.ui.add_log(f"🔄 正在切换大脑: {display_name}...")
        
        def _load():
            success = brain_manager.load_selected_model(display_name)
            if success:
                self.log_queue.put(f"🚀 大脑 '{display_name}' 已就绪！")
            else:
                self.log_queue.put(f"❌ 加载中断: 请检查模型格式与依赖")
        threading.Thread(target=_load, daemon=True).start()

    def _handle_manual_path(self):
        user_path = self.ui.input_path.text().strip()
        if not user_path:
            self.ui.add_log("⚠️ 请先输入模型路径")
            return
            
        success, res_name = brain_manager.verify_manual_path(user_path)
        if success:
            self.ui.add_log(f"✅ 手动路径识别成功: {res_name}")
            self.ui.model_combo.blockSignals(True)
            self.ui.model_combo.clear()
            self.ui.model_combo.addItems(list(brain_manager.found_models_dict.keys()))
            self.ui.model_combo.setCurrentText(res_name)
            self.ui.model_combo.blockSignals(False)
            
            self._on_model_changed(res_name)
        else:
            self.ui.add_log(f"❌ 接入失败: {res_name}")

    def _classify_intent(self, cmd: str) -> str:
        for intent, keywords in self.INTENT_MAP.items():
            if any(kw in cmd for kw in keywords):
                return intent
        return "chat"

    # 🚨 缝合迭代版特性：导入技能处理函数
    def _handle_skill_import(self, path: str):
        """用户从 GUI 手动导入 skill 文件或文件夹"""
        name = skill_manager.load_from_path(path)
        if name:
            self.ui.add_skill_item(name)
            self.ui.add_log(f"🧩 技能已导入: {name}")
        else:
            self.ui.add_log(f"❌ 技能导入失败，请检查文件格式（需含 SKILL.md）: {path}")

    def _scan_system_apps(self):
        apps_db_path = "apps_db.json"
        self.apps = {}
        db_changed = False

        if os.path.exists(apps_db_path):
            try:
                with open(apps_db_path, "r", encoding="utf-8") as f:
                    saved_apps = json.load(f)
                    for app_name, app_path in saved_apps.items():
                        if os.path.exists(app_path):
                            self.apps[app_name.lower()] = app_path
                        else:
                            db_changed = True 
            except Exception: pass

        try:
            pythoncom.CoInitialize()
            shell = Dispatch("WScript.Shell")
            paths = [
                os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
                os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
                os.path.join(os.environ['USERPROFILE'], 'Desktop'),
                os.path.join(os.environ['PUBLIC'], 'Desktop')
            ]
            for p in paths:
                if not os.path.exists(p): continue
                for root, _, files in os.walk(p):
                    for f in files:
                        if f.endswith(".lnk"):
                            try:
                                t = shell.CreateShortcut(os.path.join(root, f)).TargetPath
                                if t.endswith(".exe") and os.path.exists(t):
                                    app_name = f.replace(".lnk", "").lower().strip()
                                    if app_name not in self.apps: 
                                        self.apps[app_name] = t
                                        db_changed = True
                            except: pass
        except: pass

        if db_changed or not os.path.exists(apps_db_path):
            try:
                with open(apps_db_path, "w", encoding="utf-8") as f:
                    json.dump(self.apps, f, ensure_ascii=False, indent=4)
                print(f"📦 武器库已收录 {len(self.apps)} 个程序。")
            except: pass

    def _parse_and_execute(self, reply, command):
        if "LEARN:" in reply or "LEARN:" in reply:
            try:
                match = re.search(r'LEARN[:：]\s*(.*?)\s*(?:->|->)\s*(.*?)(?=\s|$|\]|】|>)', reply)
                if match:
                    trigger = match.group(1).strip()
                    action = match.group(2).strip()
                    
                    if trigger in self.cmd_lib.commands:
                        self.log_queue.put(f"⚠️ 冲突检测：记忆库中已存在触发词 '{trigger}'，为保护原有记忆，系统拒绝静默覆盖。")
                        self.tts.speak(f"我已经记得关于{trigger}的事情了，为了安全，我没有覆盖旧记忆。")
                    else:
                        self.cmd_lib.add_command(trigger, action)
                        self.learning.add_command(trigger, action)
                        self.log_queue.put(f"🧠 脑皮层写入成功！习得新反射: 听到 '{trigger}' 时执行 '{action}'")
                        self.tts.speak(f"记住了，以后你说 {trigger}，我就会照做。")
            except Exception as e:
                self.log_queue.put(f"❌ 记忆写入失败: {e}")

        elif "MACRO:" in reply.upper() or "MACRO：" in reply.upper():
            try:
                # 先尝试完整格式 [MACRO:目标|动作序列]
                match = re.search(r'MACRO[:：]\s*([^\|]+)\s*\|\s*([^\]】<]+)', reply, re.IGNORECASE)
                if match:
                    target = match.group(1).strip()
                    macro_str = match.group(2).strip()
                else:
                    # 容错：模型只输出了 [MACRO:目标] 没有 | 动作序列，补一个默认 wait
                    match2 = re.search(r'MACRO[:：]\s*([^\]】<\[]+)', reply, re.IGNORECASE)
                    if match2:
                        target = match2.group(1).strip()
                        macro_str = "wait 1"
                    else:
                        return

                target_lower = target.lower().strip()

                if target_lower in self.WEB_AI_URLS:
                    self.browser.open_url(self.WEB_AI_URLS[target_lower])
                    self.log_queue.put(f"🌐 机械臂前置：已打开 {target} 网页")

                elif "." in target_lower and not target_lower.endswith(".exe"):
                    url = target_lower if target_lower.startswith("http") else "https://" + target_lower
                    self.browser.open_url(url)
                    self.log_queue.put(f"🌐 机械臂前置：已打开泛化网页 {url}")

                # 磁盘/文件夹路径（如 C:\, D:\Projects, C盘, D盘）
                elif re.match(r'^[a-zA-Z]:[/\\]', target) or os.path.isdir(target):
                    try:
                        os.startfile(target)
                        self.log_queue.put(f"📂 已打开文件夹: {target}")
                    except Exception as fe:
                        self.log_queue.put(f"❌ 文件夹打开失败: {fe}")

                # 中文磁盘别名（C盘/D盘 等）
                elif re.match(r'^[a-zA-ZC-Dc-d]盘$', target) or target_lower in self.FOLDER_SHORTCUTS:
                    folder = self.FOLDER_SHORTCUTS.get(target_lower) or self.FOLDER_SHORTCUTS.get(target)
                    if folder:
                        try:
                            os.startfile(folder)
                            self.log_queue.put(f"📂 已打开: {folder}")
                        except Exception as fe:
                            self.log_queue.put(f"❌ 打开失败: {fe}")
                    else:
                        # 尝试直接解析 "X盘" 格式
                        disk_match = re.match(r'^([a-zA-Z])盘$', target)
                        if disk_match:
                            drive_path = disk_match.group(1).upper() + ":\\"
                            try:
                                os.startfile(drive_path)
                                self.log_queue.put(f"📂 已打开磁盘: {drive_path}")
                            except Exception as fe:
                                self.log_queue.put(f"❌ 磁盘打开失败: {fe}")

                else:
                    exe_path = self.apps.get(target_lower)
                    if not exe_path:
                        for k, v in self.apps.items():
                            if target_lower in k or k in target_lower:
                                exe_path = v
                                self.log_queue.put(f"💡 机械臂模糊寻路成功: '{target}' -> '{k}'")
                                break
                    if exe_path and os.path.exists(exe_path):
                        os.startfile(exe_path)
                        self.log_queue.put(f"⚡ 机械臂前置：已唤醒本地程序 [{target}]")
                    else:
                        try:
                            os.startfile(target_lower)
                            self.log_queue.put(f"⚡ 机械臂前置：已通过环境变量唤醒 [{target}]")
                        except Exception:
                            self.log_queue.put(f"⚠️ 未收录 [{target}]，将直接盲打操作。")

                threading.Thread(
                    target=self.auto.execute_dynamic_macro,
                    args=(target, macro_str), daemon=True
                ).start()

            except Exception as e:
                self.log_queue.put(f"❌ 通用宏引擎执行失败: {e}")

        # ==========================================
        # 💻 沉浸式双阶段代码生成 (保留原版强大的 Pywinauto 逻辑)
        # ==========================================
        elif "CODE" in reply.upper() or "CODE：" in reply.upper():
            def code_task():
                self.log_queue.put("⏳ [双脑机制] 正在后台全力编写代码，请耐心等待...")
                try:
                    ctx = "【系统提示】：用户要求写代码，请只输出代码本身，严禁输出Markdown标记（```）和任何解释文字。"
                    full_reply = brain_manager.ask(command, lang=self.current_lang, context=ctx)
                    clean_code = re.sub(r'```[\w]*\n?', '', full_reply).strip()

                    cmd_lower = command.lower()

                    if "trae" in cmd_lower:
                        exe = self.apps.get("trae")
                        trae_running = False

                        if HAS_PYWINAUTO:
                            try:
                                from pywinauto import Application
                                Application(backend="uia").connect(title_re=".*Trae.*", timeout=2)
                                trae_running = True
                                self.log_queue.put("🪟 Trae 已在运行，直接接管...")
                            except Exception:
                                trae_running = False

                        if not trae_running:
                            if exe and os.path.exists(exe):
                                os.startfile(exe)
                                self.log_queue.put("🚀 已启动 Trae，等待加载...")
                            else:
                                for candidate in [r"D:\Trae\Trae\Trae.exe", r"C:\Program Files\Trae\Trae.exe"]:
                                    if os.path.exists(candidate):
                                        os.startfile(candidate)
                                        break
                                else:
                                    self.log_queue.put("⚠️ 未找到 Trae 路径，代码已复制到剪贴板")
                                    pyperclip.copy(clean_code)
                                    return

                        self.log_queue.put("⏳ 等待 Trae 窗口就绪...")
                        trae_win = None
                        for _ in range(20):
                            time.sleep(1)
                            if HAS_PYWINAUTO:
                                try:
                                    from pywinauto import Application
                                    app = Application(backend="uia").connect(title_re=".*Trae.*", timeout=1)
                                    trae_win = app.top_window()
                                    self.log_queue.put("✅ Trae 窗口已就绪！")
                                    break
                                except Exception:
                                    pass
                        if trae_win is None:
                            self.log_queue.put("⚠️ Trae 窗口等待超时，尝试盲打注入...")
                            time.sleep(3)

                        pyperclip.copy(clean_code)
                        time.sleep(0.5)

                        if HAS_PYWINAUTO:
                            try:
                                from pywinauto import Application
                                from pywinauto.keyboard import send_keys
                                app = Application(backend="uia").connect(title_re=".*Trae.*", timeout=5)
                                win = app.top_window()
                                win.set_focus()
                                time.sleep(0.8)
                                send_keys("^n")          
                                time.sleep(2)
                                send_keys("^v")          
                                time.sleep(1)
                                send_keys("^s")          
                                time.sleep(0.5)
                                send_keys("{ENTER}")     
                                self.log_queue.put("✅ [pywinauto] 代码已精准注入 Trae 并保存！")
                            except Exception as e:
                                self.log_queue.put(f"⚠️ pywinauto 注入失败: {e}，切换盲打模式...")
                                screenW, screenH = pyautogui.size()
                                pyautogui.click(screenW // 2, int(screenH * 0.4))
                                time.sleep(0.5)
                                pyautogui.hotkey('ctrl', 'n')
                                time.sleep(2)
                                pyautogui.hotkey('ctrl', 'v')
                                time.sleep(1)
                                pyautogui.hotkey('ctrl', 's')
                                self.log_queue.put("✅ [盲打] 代码注入完成！")
                        else:
                            screenW, screenH = pyautogui.size()
                            pyautogui.click(screenW // 2, int(screenH * 0.4))
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'n')
                            time.sleep(2)
                            pyautogui.hotkey('ctrl', 'v')
                            time.sleep(1)
                            pyautogui.hotkey('ctrl', 's')
                            self.log_queue.put("✅ 代码已注入 Trae！")

                    elif "记事本" in cmd_lower or "notepad" in cmd_lower or "文本" in cmd_lower:
                        os.startfile("notepad.exe")
                        self.log_queue.put("🤖 已唤醒记事本...")
                        time.sleep(2)
                        pyperclip.copy(clean_code)
                        pyautogui.hotkey('ctrl', 'v')
                        self.log_queue.put("✅ 代码已写入记事本！")

                    else:
                        pyperclip.copy(clean_code)
                        self.log_queue.put("✅ 代码已生成并保存到剪贴板，请手动粘贴。")

                except Exception as e:
                    self.log_queue.put(f"❌ 代码生成与注入失败: {e}")

            threading.Thread(target=code_task, daemon=True).start()

        elif "SEARCH:" in reply.upper() or "SEARCH：" in reply.upper():
            try:
                match = re.search(r'SEARCH[:：]\s*([^\]】<]+)', reply, re.IGNORECASE)
                if match:
                    search_target = match.group(1).strip()
                    engine = "bing" 
                    cmd_lower = command.lower()
                    engine_radar = {
                        "google": ["google", "谷歌"], "baidu": ["baidu", "百度"],
                        "duckduckgo": ["duckduckgo", "鸭鸭走"], "sogou": ["sogou", "搜狗"],
                        "bilibili": ["bilibili", "b站"], "github": ["github", "开源"],
                        "youtube": ["youtube", "油管"], "huggingface": ["huggingface", "抱抱脸"],
                        "reddit": ["reddit", "红迪"], "taobao": ["taobao", "淘宝"],
                        "jd": ["jd", "京东"], "amazon": ["amazon", "亚马逊"],
                        "shein": ["shein"], "temu": ["temu"],
                        "x": ["x", "twitter", "推特"], "xiaohongshu": ["xiaohongshu", "小红书"]
                    }
                    for eng_key, keywords in engine_radar.items():
                        if any(kw in cmd_lower for kw in keywords):
                            engine = eng_key
                            break
                    self.network.request_permission()
                    if self.network.is_allowed:
                        self.ui.add_log(f"🧠 路由判定: 正在使用 [{engine.upper()}] 引擎搜索...")
                        self.browser.search(search_target, engine=engine)
            except Exception as e:
                self.ui.add_log(f"❌ 搜索唤起失败: {e}")
        
        elif "OPEN:" in reply.upper() or "OPEN：" in reply.upper():
            try:
                match = re.search(r'OPEN[:：]\s*([^\s\]】>]+)', reply, re.IGNORECASE)
                if match:
                    url = match.group(1).strip()
                    if not url.startswith("http"): url = "https://" + url
                    self.browser.open_url(url)
                    self.ui.add_log(f"🌐 已为您在浏览器打开网页: {url}")
            except Exception as e:
                self.ui.add_log(f"❌ 打开网址失败: {e}")

        elif "READ:" in reply.upper() or "READ：" in reply.upper():
            match = re.search(r'READ[:：]\s*([^\]】<]+)', reply, re.IGNORECASE)
            if match:
                url = match.group(1).strip()
                if not url.startswith("http"):
                    self.ui.add_log(f"💡 自动纠错: 将 '{url}' 转为网页搜索...")
                    self.browser.search(url)
                else:
                    self.ui.add_log(f"🌐 正在后台潜入目标网页: {url} ...")
                    def read_task(target_url):
                        try:
                            page_content = self.parser.get_page_text(target_url)
                            if "❌" in page_content:
                                self.log_queue.put(page_content)
                                self.tts.speak("抱歉，网页读取超时，请检查网络代理。")
                            else:
                                safe_content = page_content[:1000]
                                self.log_queue.put(f"📄 网页抓取成功，正在反馈给大模型...")
                                ctx = f"【系统强制指令】：你刚才读取了网页，内容为：{safe_content}。请用自然语言向我总结，严禁输出任何中括号指令！"
                                self.voice_queue.put(ctx)
                        except Exception as e:
                            self.log_queue.put(f"❌ 网页潜入失败: {e}")
                    threading.Thread(target=read_task, args=(url,), daemon=True).start()

    def _on_lang_change(self, lang):
        self.current_lang = lang
        self.tts.set_name("小智" if "zh" in lang else "Tom")
        mapping = {"zh-HK": "cantonese", "en-US": "english", "zh-CN": "mandarin"}
        tts_mode = mapping.get(lang, "mandarin")
        if hasattr(self.tts, 'set_language'):
            self.tts.set_language(tts_mode)
        self.ui.add_log(f"🔄 语言已切换为: {lang}")

    def _listen_worker(self):
        while True:
            cmd = self.voice_rec.listen_for_wake_word(lang=self.current_lang)
            if cmd and cmd.strip(): 
                self.voice_queue.put(cmd)

    def boot(self):
        self.ui.show()
        self.ui.add_log("🎤 初始化环境中...")

        if not check_permissions():
            sys.exit(1)

        # ── 模型扫描（后台线程）──
        self.ui.add_log("🔍 正在全盘搜索可用模型，稍候...")
        self.ui.model_combo.blockSignals(True)
        self.ui.model_combo.addItem("⏳ 扫描中...")
        self.ui.model_combo.blockSignals(False)

        def _on_model_found(key):
            self.log_queue.put(f"__MODEL_FOUND__:{key}")

        def _scan_models_bg():
            try:
                models = brain_manager.scan_models(progress_callback=_on_model_found)
                self.log_queue.put(f"__SCAN_DONE__:{len(models)}")
            except Exception as e:
                self.log_queue.put(f"⚠️ 扫描异常: {e}")
                self.log_queue.put("__SCAN_DONE__:0")

        threading.Thread(target=_scan_models_bg, daemon=True).start()

        # 🚨 缝合迭代版特性：Skill 扫描（后台线程并入）
        def _scan_skills_bg():
            def _on_done(names):
                if names:
                    self.log_queue.put(f"🧩 发现 {len(names)} 个 Skill：" +
                                       "、".join(n.split()[-1] for n in names[:5]) +
                                       ("…" if len(names) > 5 else ""))
                    for n in names:
                        self.log_queue.put(f"__SKILL_ITEM__{n}")
                    self.log_queue.put("__SKILL_DONE__")
                else:
                    self.log_queue.put("💡 未发现 Skill，可将 .skill 文件放入 skills/ 目录后重启。")

            if hasattr(skill_manager, 'scan_skills'):
                skill_manager.scan_skills(callback=_on_done)

        threading.Thread(target=_scan_skills_bg, daemon=True).start()

        self.ui.add_log("🤖 具身智能中央控制台正在启动...")
        self.camera.start()

        self.config.load_config()
        self._on_lang_change("zh-CN")

        if not os.path.exists("logs/training_log.json"):
            self.guide.guide_user()

        threading.Thread(target=self._listen_worker, daemon=True).start()
        self.main_timer.start(30)
        sys.exit(self.app.exec_())

    def _update_ui_frame(self, frame):
        if frame is not None:
            cv2.putText(frame, self.avatar_state_text, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, self.avatar_state_color, 2, cv2.LINE_AA)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.ui.camera_label.width(), self.ui.camera_label.height(), Qt.KeepAspectRatio
            )
            self.ui.camera_label.setPixmap(scaled_pixmap)

    def _main_tick(self):
        self.res_manager.monitor_and_adjust()
        now = time.time()
        
        frame = self.camera.get_frame()
        
        # ── 消息队列分发（普通日志 + 特殊控制令牌）──
        while not self.log_queue.empty():
            msg = self.log_queue.get()

            # 模型扫描令牌
            if msg.startswith("__MODEL_FOUND__:"):
                key = msg[len("__MODEL_FOUND__:"):]
                if self.ui.model_combo.count() == 1 and self.ui.model_combo.itemText(0) == "⏳ 扫描中...":
                    self.ui.model_combo.blockSignals(True)
                    self.ui.model_combo.clear()
                    self.ui.model_combo.blockSignals(False)
                self.ui.model_combo.blockSignals(True)
                self.ui.model_combo.addItem(key)
                self.ui.model_combo.blockSignals(False)

            elif msg.startswith("__SCAN_DONE__:"):
                count = msg[len("__SCAN_DONE__:"):]
                if count == "0":
                    self.ui.model_combo.blockSignals(True)
                    self.ui.model_combo.clear()
                    self.ui.model_combo.blockSignals(False)
                    self.ui.add_log("⚠️ 未发现任何模型，请使用下方手动路径框加载")
                else:
                    self.ui.add_log(f"✅ 扫描完成，共发现 {count} 个可用模型")

            # 🚨 缝合迭代版特性：Skill 扫描令牌
            elif msg.startswith("__SKILL_ITEM__"):
                name = msg[len("__SKILL_ITEM__"):]
                self.ui.add_skill_item(name)       
            elif msg == "__SKILL_DONE__":
                pass                               

            else:
                self.ui.add_log(msg)
        
        if not self.voice_queue.empty() and not self.processing_event.is_set():
            self.processing_event.set() 
            
            raw_cmd = self.voice_queue.get()
            cmd = raw_cmd
            for w, r in VOICE_CORRECTION.items(): 
                cmd = cmd.replace(w, r)

            # 🚨 保留原版的无敌护甲：文件夹/磁盘快捷拦截，完全绕过 LLM，防止死机！
            shortcut_opened = False
            for keyword, folder_path in self.FOLDER_SHORTCUTS.items():
                  if keyword in cmd:
                        try:
                            os.startfile(folder_path)
                            self.reply_queue.put((cmd, f"[已为您打开{keyword}]"))
                            shortcut_opened = True
                            break
                        except Exception as e:
                            self.ui.add_log(f"❌ 无法打开目录: {e}")

            # X盘 格式快捷拦截（如 "打开C盘" "去D盘"）
            if not shortcut_opened and re.search(r'[a-zA-Z]盘', cmd):
                disk_match = re.search(r'([a-zA-Z])盘', cmd)
                if disk_match:
                    drive_path = disk_match.group(1).upper() + ":\\"
                    try:
                        os.startfile(drive_path)
                        self.reply_queue.put((cmd, f"[已打开磁盘: {drive_path}]"))
                        shortcut_opened = True
                    except Exception as e:
                        self.ui.add_log(f"❌ 磁盘打开失败: {e}")

            learned_action = self.cmd_lib.commands.get(cmd)

            if shortcut_opened:
                pass 
            elif learned_action:
                self.ui.add_log(f"⚡ 触发肌肉记忆: {cmd} -> {learned_action}")
                self.reply_queue.put((cmd, f"[{learned_action}]"))
            else:
                self.avatar_state_text = "🧠 思考中 (Thinking...)"
                self.avatar_state_color = (0, 255, 255) 
                
                is_vision_enabled = hasattr(self.ui, 'vision_switch') and self.ui.vision_switch.isChecked()
                active_frame = frame.copy() if (is_vision_enabled and frame is not None) else None
                
                dynamic_state = self.camera.get_dynamic_state()
                context_hint = ""
                if dynamic_state.get("target_locked"):
                    context_hint += "【视觉雷达感知】：当前视野内已锁定人类目标。"
                    if dynamic_state.get("gesture") == "HAND_UP":
                        context_hint += "对方正在举起手。"
                        
                intent = self._classify_intent(cmd)
                if intent != "chat":
                    context_hint += f"\n【系统意图雷达】：分析出用户意图为 '{intent}'，请严格参考对应法则。"

                def ai_worker(c, f, ctx):
                    try:
                        # 🚨 缝合迭代版特性：将已知程序列表传递给大脑
                        apps_keys = list(self.apps.keys()) if self.apps else []
                        res = brain_manager.ask(c, self.current_lang, frame=f, context=ctx, apps_list=apps_keys)
                    except Exception as e:
                        res = f"抱歉，脑电波断开了: {e}"
                    finally:
                        self.reply_queue.put((c, res))
                
                threading.Thread(target=ai_worker, args=(cmd, active_frame, context_hint), daemon=True).start()

        if not self.reply_queue.empty():
            cmd, reply = self.reply_queue.get()
            
            self.ui.add_log(f"🤖 {reply}")
            self._parse_and_execute(reply, cmd)
            
            clean_msg = re.sub(r'\[.*?\]|【.*?】|<.*?>', '', reply, flags=re.DOTALL).strip()
            if clean_msg: 
                self.tts.speak(clean_msg)
            else:
                self.tts.speak("好的，正在执行。")
                
            self.avatar_state_text = "待命中 (Listening...)"
            self.avatar_state_color = (0, 255, 0)
            
            self.processing_event.clear() 

        self._update_ui_frame(frame)
        if now - self.last_vram_time > 5 and HAS_NVIDIA:
            self.last_vram_time = now

if __name__ == "__main__":
    MainController().boot()