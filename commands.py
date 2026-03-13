import os
import json

class CommandLibrary:
    def __init__(self):
        # 🚨 已清空出厂自带的毒数据，把控制权完全交给用户
        self.commands = {}
        self.learning_log = "logs/learning_log.json"
        os.makedirs("logs", exist_ok=True)
        self.FOLDER_SHORTCUTS = {
            "c盘": "C:\\",
            "d盘": "D:\\",
            "桌面": os.path.join(os.path.expanduser("~"), "Desktop"),
            "下载": os.path.join(os.path.expanduser("~"), "Downloads"),
            "文档": os.path.join(os.path.expanduser("~"), "Documents"),
}
        
        


    def add_command(self, new_command, action):
        if new_command.strip():
            self.commands[new_command.strip()] = action
            self.save_log()
            print(f"✅ 已学习新指令：{new_command} → {action}")
            return True
        return False

    def save_log(self):
        with open(self.learning_log, "w", encoding="utf-8") as f:
            json.dump(self.commands, f, ensure_ascii=False, indent=2)

    def load_log(self):
        if os.path.exists(self.learning_log):
            with open(self.learning_log, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.commands.update(data) # 确保加载后更新到内存中
                    return data
                except:
                    pass
        return {}

    def show_commands(self):
        print("📖 已学习指令：")
        for k, v in self.commands.items():
            print(f"  - {k} → {v}")