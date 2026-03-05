import logging
import time

from google import genai
from google.genai import types

from src.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiLLMClient(BaseLLMClient):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiLLMClient initialized.")

    def get_available_models(self) -> list[str]:
        """Fetches and filters Gemini models."""
        try:
            logger.info("Fetching available Gemini models...")
            start_time = time.time()
            models = self.client.models.list()
            duration = time.time() - start_time
            
            filtered_models = []
            for m in models:
                if any(x in m.name.lower() for x in ["gemini", "gemma"]):
                    actions = getattr(m, "supported_actions", [])
                    if "generate_content" in actions or "generateContent" in actions or not actions:
                        name = m.name.replace("models/", "")
                        filtered_models.append(name)

            result = sorted(filtered_models, reverse=True)
            logger.info(f"Successfully fetched {len(result)} models in {duration:.2f}s.")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch Gemini models: {e}")
            raise Exception(f"Failed to fetch models: {str(e)}")

    def generate_minutes(self, transcript: str, model_name: str) -> str:
        """Generates meeting minutes using Gemini."""
        logger.info(f"Generating minutes using Gemini model: {model_name}...")
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )

        try:
            start_time = time.time()
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                ),
            )
            duration = time.time() - start_time
            logger.info(f"Minutes generated successfully by Gemini in {duration:.2f}s.")
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise Exception(f"Failed to generate minutes: {str(e)}")
