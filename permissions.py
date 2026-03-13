# permissions.py
import sys
import os
import getpass
import hashlib
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout
)
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import Qt

def get_machine_signature():
    """生成当前设备的专属指纹"""
    user = getpass.getuser()
    return hashlib.md5(f"EmbodiedAI_Secret_{user}".encode()).hexdigest()

class PermissionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌐 权限请求")
        self.resize(500, 300)
        self.permission_granted = False 
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        title = QLabel("⚠️ Embodied AI 需要访问您的设备权限")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        content = QLabel(
            "为使用本应用，请同意以下权限：\n"
            "✅ 麦克风（语音识别）\n"
            "✅ 摄像头（视觉感知）\n"
            "✅ 网络访问（搜索网页）\n"
            "✅ 浏览器操作（打开网页）\n"
            "⚠️ 所有操作需你主动触发，不会自动执行\n"
        )
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignCenter)
        layout.addWidget(content)

        button_layout = QHBoxLayout()
        self.btn_agree = QPushButton("✅ 同意并继续")
        self.btn_cancel = QPushButton("❌ 取消并退出")
        self.btn_agree.clicked.connect(self.on_agree)
        self.btn_cancel.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.btn_agree)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_agree(self):
        sig = get_machine_signature()
        with open("permission_agreed.dat", "w") as f:
            f.write(sig)
        self.permission_granted = True
        self.close() 

    def on_cancel(self):
        self.permission_granted = False
        print("❌ 权限拒绝，程序退出")
        sys.exit(0)

def check_permissions():
    """对接 main.py 的逻辑入口"""
    sig = get_machine_signature()
    if os.path.exists("permission_agreed.dat"):
        with open("permission_agreed.dat", "r") as f:
            if f.read().strip() == sig:
                return True
    
    app = QWidget() 
    dialog = PermissionDialog()
    dialog.show()
    
    from PyQt5.QtWidgets import QApplication
    while dialog.isVisible():
        QApplication.processEvents()
        
    return dialog.permission_granted