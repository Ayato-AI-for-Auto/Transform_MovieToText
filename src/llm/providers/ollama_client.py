import logging
import time

from ollama import Client

from src.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OllamaCloudClient(BaseLLMClient):
    def __init__(self, api_key):
        # cloud models use the ollama.com host with the API key in headers
        self.client = Client(host="https://ollama.com", headers={"Authorization": f"Bearer {api_key}"})
        logger.info("OllamaCloudClient initialized.")

    def get_available_models(self) -> list[str]:
        """Fetches available cloud models from Ollama."""
        try:
            logger.info("Fetching available Ollama Cloud models...")
            start_time = time.time()
            # According to docs: curl https://ollama.com/api/tags
            # The python sdk's list() might need the host setup
            response = self.client.list()
            duration = time.time() - start_time
            
            models = [m["name"] for m in response["models"]]
            logger.info(f"Successfully fetched {len(models)} Ollama models in {duration:.2f}s.")
            return sorted(models)
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
            # Fallback to some common cloud model names if listing fails,
            # though an empty list is safer for dynamic UI.
            return ["gpt-oss:120b", "gpt-oss:120b-cloud"]

    def generate_minutes(self, transcript: str, model_name: str) -> str:
        """Generates minutes using Ollama Cloud."""
        logger.info(f"Generating minutes using Ollama model: {model_name}...")

        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )

        messages = [{"role": "user", "content": prompt}]

        try:
            # We use chat() for generation
            # Note: Cloud models might not support streaming in the same way,
            # but we'll use non-streaming for simplicity here.
            start_time = time.time()
            response = self.client.chat(model=model_name, messages=messages)
            duration = time.time() - start_time
            logger.info(f"Minutes generated successfully by Ollama in {duration:.2f}s.")
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise Exception(f"Failed to generate minutes: {str(e)}")
