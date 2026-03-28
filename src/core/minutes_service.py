import logging

from src.core.config_manager import ConfigManager
from src.core.history_mgr import history_mgr
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class MinutesService:
    """
    Handles business logic for generating meeting minutes and summaries.
    Decoupled from UI state.
    """

    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr

    def generate_minutes_sync(self, transcript: str, provider: str, model: str, meeting_id: int | None = None) -> str:
        """
        Synchronously generates minutes and updates history if meeting_id is provided.
        """
        if not transcript or not model:
            raise ValueError("Transcript and model name are required.")

        # 1. Initialize client
        conf = self.config_mgr.get_provider_config(provider)
        client = LLMFactory.create_client(provider_name=provider, api_key=conf.get("api_key"), base_url=conf.get("base_url"))

        # 2. Fetch Visual Context if available
        visual_contexts = []
        if meeting_id:
            try:
                visual_contexts = history_mgr.get_visual_contexts(meeting_id)
                logger.info(f"Retrieved {len(visual_contexts)} visual contexts for meeting {meeting_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch visual contexts: {e}")

        # 3. Generate multimodal minutes
        try:
            res = client.generate_minutes(transcript, model, visual_contexts=visual_contexts)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise RuntimeError(f"Minutes generation failed: {e}") from e

        # 4. Update history and config
        if meeting_id:
            try:
                history_mgr.update_minutes(meeting_id, res, model_name=model)
            except Exception as e:
                logger.error(f"Failed to update history with minutes: {e}")

        self.config_mgr.set_last_model(model)
        return res

    def get_available_models(self, provider: str) -> list[str]:
        """Fetches available models for a given provider."""
        try:
            conf = self.config_mgr.get_provider_config(provider)
            client = LLMFactory.create_client(provider_name=provider, api_key=conf.get("api_key"), base_url=conf.get("base_url"))
            return client.get_available_models()
        except Exception as e:
            logger.error(f"Failed to fetch models for {provider}: {e}")
            return []
