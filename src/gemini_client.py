import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiClient initialized.")

    def get_available_models(self):
        """Fetches and filters models suitable for text generation."""
        try:
            logger.info("Fetching available Gemini models...")
            models = self.client.models.list()
            filtered_models = []
            for m in models:
                # In google-genai, m is a Model object
                # Check for gemini/gemma and typical generation action
                if any(x in m.name.lower() for x in ["gemini", "gemma"]):
                    # We can use simple name filtering or check supported_actions
                    actions = getattr(m, "supported_actions", [])
                    if "generate_content" in actions or "generateContent" in actions or not actions:
                        name = m.name.replace("models/", "")
                        filtered_models.append(name)
            
            result = sorted(filtered_models, reverse=True)
            logger.info(f"Successfully fetched {len(result)} models.")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            raise Exception(f"Failed to fetch models: {str(e)}")

    def generate_minutes(self, transcript, model_name):
        """Generates meeting minutes from the transcript."""
        logger.info(f"Generating minutes using model: {model_name}...")
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                ),
            )
            logger.info("Minutes generated successfully.")
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate minutes: {e}")
            raise Exception(f"Failed to generate minutes: {str(e)}")
