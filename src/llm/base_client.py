from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Returns a list of available model names for this provider."""
        pass

    @abstractmethod
    def generate_minutes(self, transcript: str, model_name: str) -> str:
        """Generates meeting minutes from the transcript using the specified model."""
        pass
