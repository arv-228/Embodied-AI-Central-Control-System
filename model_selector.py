# model_selector.py
import os
import json

class ModelSelector:
    def __init__(self):
        self.model_folder = "models"
        self.model_list = []
        self.current_model = "default"
        self.load_models()

    def load_models(self):
        if not os.path.exists(self.model_folder):
            return # 目录不存在直接退回，防止崩溃
        self.model_list = []
        for file in os.listdir(self.model_folder):
            if file.endswith(".pt"):
                name = file.replace(".pt", "")
                self.model_list.append(name)
        if not self.model_list:
            self.model_list.append("default")
        self.current_model = self.model_list[0] if self.model_list else "default"

    def select_model(self, name):
        if name in self.model_list:
            self.current_model = name
            print(f"✅ 已选择模型：{name}")
            return True
        else:
            print(f"❌ 模型 {name} 不存在")
            return False

    def show_models(self):
        print("📦 可用模型：")
        for m in self.model_list:
            print(f"  - {m}")
