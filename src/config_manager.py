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
            logger.debug(f"Config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)

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
        old = self.get_active_provider()
        if old != provider_name:
            self.config["active_provider"] = provider_name
            logger.info(f"Active provider changed: {old} -> {provider_name}")
            self.save_config()

    def get_provider_config(self, provider_name):
        return self.config.get("providers", {}).get(provider_name, {})

    def set_provider_config(self, provider_name, provider_config):
        if "providers" not in self.config:
            self.config["providers"] = {}
        
        # Mask API key in log if present
        log_config = provider_config.copy()
        if "api_key" in log_config and log_config["api_key"]:
            key = log_config["api_key"]
            log_config["api_key"] = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
            
        logger.info(f"Updating config for provider {provider_name}: {log_config}")
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
        old = self.get_whisper_model()
        if old != model_name:
            self.config["whisper_model"] = model_name
            logger.info(f"Whisper model changed: {old} -> {model_name}")
            self.save_config()

    def get_force_gpu(self):
        return self.config.get("force_gpu", False)

    def set_force_gpu(self, enabled):
        old = self.get_force_gpu()
        if old != enabled:
            self.config["force_gpu"] = enabled
            logger.info(f"Force GPU setting changed: {old} -> {enabled}")
            self.save_config()

    def get_audio_source(self):
        """Returns the current audio source: 'system' or 'microphone'."""
        return self.config.get("audio_source", "system")

    def set_audio_source(self, source):
        """Sets the audio source: 'system' or 'microphone'."""
        old = self.get_audio_source()
        if old != source:
            self.config["audio_source"] = source
            logger.info(f"Audio source changed: {old} -> {source}")
            self.save_config()
