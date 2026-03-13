# command_learning.py
import os
import json

class CommandLearning:
    def __init__(self):
        self.learning_log = "logs/learning_log.json"
        os.makedirs("logs", exist_ok=True)

    def add_command(self, new_command, action):
        if new_command.strip():
            with open(self.learning_log, "a", encoding="utf-8") as f:
                f.write(f"{new_command} → {action}\n")
            print(f"✅ 已学习新指令：{new_command} → {action}")
        else:
            print("❌ 指令为空")

    def show_learning(self):
        print("📊 已学习指令：")
        if os.path.exists(self.learning_log):
            with open(self.learning_log, "r", encoding="utf-8") as f:
                for line in f:
                    print(f"  - {line.strip()}")
