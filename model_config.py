# model_config.py
import os
import json

class ModelConfig:
    def __init__(self):
        self.model_folder = "models"
        self.config_file = "config.json"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                    self.model_folder = config.get("model_folder", self.model_folder)
                except:
                    pass
        os.makedirs(self.model_folder, exist_ok=True)

    def save_config(self):
        config = {"model_folder": self.model_folder}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get_model_path(self, model_name):
        return os.path.join(self.model_folder, f"{model_name}.pt")
