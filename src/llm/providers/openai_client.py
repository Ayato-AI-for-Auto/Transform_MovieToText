import logging
import time

from openai import OpenAI

from src.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(BaseLLMClient):
    """Client for any OpenAI-compatible API (Groq, Local Ollama, DeepSeek, etc.)"""

    def __init__(self, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAICompatibleClient initialized with base_url: {base_url}")

    def get_available_models(self) -> list[str]:
        """Fetches models from the compatible API."""
        try:
            logger.info("Fetching models from OpenAI compatible API...")
            start_time = time.time()
            models = self.client.models.list()
            duration = time.time() - start_time
            
            result = [m.id for m in models.data]
            logger.info(f"Successfully fetched {len(result)} models in {duration:.2f}s.")
            return sorted(result)
        except Exception as e:
            logger.warning(f"Failed to fetch models from compatible API: {e}. User might need to enter model name manually.")
            return []

    def generate_minutes(self, transcript: str, model_name: str) -> str:
        """Generates minutes via OpenAI-compatible completion."""
        logger.info(f"Generating minutes using model: {model_name} via OpenAI-compatible API...")
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            duration = time.time() - start_time
            logger.info(f"Minutes generated successfully in {duration:.2f}s.")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI-compatible generation failed: {e}")
            raise Exception(f"Failed to generate minutes: {str(e)}")
