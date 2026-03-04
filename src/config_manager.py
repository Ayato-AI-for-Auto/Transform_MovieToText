import json
import logging
import os

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self._migrate_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return {}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _migrate_config(self):
        """Migrates old flat config to new provider-based structure."""
        changed = False

        # Move gemini_api_key to providers dict if it exists and new structure isn't there
        if "gemini_api_key" in self.config and "providers" not in self.config:
            old_key = self.config.pop("gemini_api_key")
            self.config["providers"] = {
                "gemini": {"api_key": old_key},
                "ollama_cloud": {"api_key": ""},
                "openai_custom": {"api_key": "", "base_url": "https://api.groq.com/openai/v1"},
            }
            self.config["active_provider"] = "gemini"
            changed = True

        # Ensure 'providers' key exists
        if "providers" not in self.config:
            self.config["providers"] = {
                "gemini": {"api_key": ""},
                "ollama_cloud": {"api_key": ""},
                "openai_custom": {"api_key": "", "base_url": "https://api.groq.com/openai/v1"},
            }
            self.config["active_provider"] = "gemini"
            changed = True

        if changed:
            self.save_config()

    def get_active_provider(self):
        return self.config.get("active_provider", "gemini")

    def set_active_provider(self, provider_name):
        self.config["active_provider"] = provider_name
        self.save_config()

    def get_provider_config(self, provider_name):
        return self.config.get("providers", {}).get(provider_name, {})

    def set_provider_config(self, provider_name, provider_config):
        if "providers" not in self.config:
            self.config["providers"] = {}
        self.config["providers"][provider_name] = provider_config
        self.save_config()

    def get_last_model(self, provider_name=None):
        if not provider_name:
            provider_name = self.get_active_provider()
        return self.config.get("last_models", {}).get(provider_name, "")

    def set_last_model(self, model_name, provider_name=None):
        if not provider_name:
            provider_name = self.get_active_provider()
        if "last_models" not in self.config:
            self.config["last_models"] = {}
        self.config["last_models"][provider_name] = model_name
        self.save_config()

    def get_whisper_model(self):
        return self.config.get("whisper_model", "base")

    def set_whisper_model(self, model_name):
        self.config["whisper_model"] = model_name
        self.save_config()
