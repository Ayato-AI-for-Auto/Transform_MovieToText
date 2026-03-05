import logging
import threading

from src.config_manager import ConfigManager
from src.core.state import state
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)

class MinutesController:
    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr
        self.llm_client = None

    def generate_minutes(self, transcript: str, provider: str, model: str):
        if not transcript:
            return
        if not model:
            return

        state.set("is_processing", True)
        state.set("minutes_text", "議事録を生成中...")

        def _worker():
            try:
                # Initialize or get client
                conf = self.config_mgr.get_provider_config(provider)
                client = LLMFactory.create_client(
                    provider_name=provider,
                    api_key=conf.get("api_key"),
                    base_url=conf.get("base_url")
                )
                
                res = client.generate_minutes(transcript, model)
                state.set("minutes_text", res)
                
                # Save last used model
                self.config_mgr.set_last_model(model)
            except Exception as e:
                logger.error(f"Minutes generation error: {e}", exc_info=True)
                state.set("minutes_text", f"【エラーが発生しました】\n{e}")
            finally:
                state.set("is_processing", False)

        threading.Thread(target=_worker, daemon=True).start()

    def get_available_models(self, provider: str):
        """Helper to fetch models for a provider."""
        try:
            conf = self.config_mgr.get_provider_config(provider)
            client = LLMFactory.create_client(
                provider_name=provider,
                api_key=conf.get("api_key"),
                base_url=conf.get("base_url")
            )
            return client.get_available_models()
        except Exception as e:
            logger.warning(f"Failed to fetch models for {provider}: {e}")
            return []
