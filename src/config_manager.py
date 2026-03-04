import json
import os


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_api_key(self):
        return self.config.get("gemini_api_key", "")

    def set_api_key(self, api_key):
        self.config["gemini_api_key"] = api_key
        self.save_config()

    def get_last_model(self):
        return self.config.get("last_gemini_model", "")

    def set_last_model(self, model_name):
        self.config["last_gemini_model"] = model_name
        self.save_config()
