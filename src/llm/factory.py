import logging

from src.llm.providers.gemini_client import GeminiLLMClient
from src.llm.providers.ollama_client import OllamaCloudClient
from src.llm.providers.openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


def get_llm_client(provider_name, api_key, base_url=None):
    """Factory function to get the appropriate LLM client."""
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "****"
    logger.info(f"Creating LLM client for provider: {provider_name} (API Key: {masked_key})")
    
    if provider_name == "gemini":
        return GeminiLLMClient(api_key=api_key)
    elif provider_name == "ollama_cloud":
        return OllamaCloudClient(api_key=api_key)
    elif provider_name == "openai_custom":
        if not base_url:
            logger.error("Attempted to create openai_custom client without base_url")
            raise ValueError("base_url is required for openai_custom provider.")
        logger.debug(f"OpenAI compatible base_url: {base_url}")
        return OpenAICompatibleClient(api_key=api_key, base_url=base_url)
    else:
        logger.error(f"Unsupported LLM provider requested: {provider_name}")
        raise ValueError(f"Unknown LLM provider: {provider_name}")
