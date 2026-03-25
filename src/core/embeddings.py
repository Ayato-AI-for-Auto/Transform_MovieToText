import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        pass

class GoogleEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = "text-embedding-004"

    def embed_text(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text
        )
        return response.embeddings[0].values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=texts
        )
        return [e.values for e in response.embeddings]

class FastEmbedProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding
        # This will download the model on first init
        self.model = TextEmbedding(model_name=model_name)
        logger.info(f"FastEmbed initialized with model: {model_name}")

    def embed_text(self, text: str) -> list[float]:
        # FastEmbed returns an iterator of numpy arrays
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

class EmbeddingFactory:
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> BaseEmbeddingProvider:
        if provider_type == "google":
            return GoogleEmbeddingProvider(api_key=kwargs.get("api_key"))
        if provider_type == "local":
            return FastEmbedProvider(model_name=kwargs.get("model_name", "BAAI/bge-small-en-v1.5"))
        raise ValueError(f"Unknown embedding provider: {provider_type}")
