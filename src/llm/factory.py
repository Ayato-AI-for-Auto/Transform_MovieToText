from src.llm.providers.gemini_client import GeminiLLMClient
from src.llm.providers.ollama_client import OllamaCloudClient
from src.llm.providers.openai_client import OpenAICompatibleClient


def get_llm_client(provider_name, api_key, base_url=None):
    """Factory function to get the appropriate LLM client."""
    if provider_name == "gemini":
        return GeminiLLMClient(api_key=api_key)
    elif provider_name == "ollama_cloud":
        return OllamaCloudClient(api_key=api_key)
    elif provider_name == "openai_custom":
        if not base_url:
            raise ValueError("base_url is required for openai_custom provider.")
        return OpenAICompatibleClient(api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
