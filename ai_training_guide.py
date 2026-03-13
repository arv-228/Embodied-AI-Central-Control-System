# ai_training_guide.py
import os
import json
import datetime

class AITrainingGuide:
    def __init__(self):
        self.training_log = "logs/training_log.json"
        os.makedirs("logs", exist_ok=True)

    def guide_user(self):
        print("\n💡 AI 本地训练引导：")
        print("你可以在本地训练模型，例如：")
        print("1. 准备一个训练数据集（如文本、代码）")
        print("2. 使用 Python 或 TensorFlow 训练模型")
        print("3. 保存为 .pt 文件，放入 models/ 文件夹")
        print("4. 例如：models/small_ai_model.pt")
        print("5. 输入：select_model('small_ai_model')")
        print("✅ 你已掌握本地训练流程！")

    def record_training(self, model_name, task, result):
        entry = {
            "model": model_name,
            "task": task,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat()
        }
        with open(self.training_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"✅ 已记录训练：{model_name} → {task}")
