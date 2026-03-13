# log_manager.py
import datetime
import os

class OperationLogger:
    def __init__(self):
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "operation.log")

    def log(self, action, user_input=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ACTION: {action} | INPUT: {user_input}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"📝 已记录：{action}")
