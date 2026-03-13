import sys, traceback
sys.path.insert(0, '.')

try:
    # 逐步执行 main.py 的顶层代码
    print("step 1: 导入标准库...")
    import sys, os, time, threading, queue, re, string, json, winreg, ctypes
    print("OK")

    print("step 2: 导入第三方库...")
    import pyautogui, pyperclip, cv2
    print("OK")

    print("step 3: 导入 PyQt5...")
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QImage, QPixmap
    from PyQt5.QtCore import Qt, QTimer
    print("OK")

    print("step 4: 导入 win32com...")
    from win32com.client import Dispatch
    print("OK")

    print("step 5: 导入所有本地模块...")
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
    print("OK")

    print("step 6: 初始化 QApplication...")
    app = QApplication(sys.argv)
    print("OK")

    print("step 7: 初始化 MainController...")
    # 直接从 main.py 导入 MainController 类
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("OK")

except SystemExit as e:
    print(f"FAIL: sys.exit() 被调用，退出码: {e.code}")
    traceback.print_exc()
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
    traceback.print_exc()

input("按回车退出")