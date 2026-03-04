from genai import Client
from genai.types import GenerateContentConfig

class GeminiClient:
    def __init__(self, api_key):
        self.client = Client(api_key=api_key)

    def get_available_models(self):
        """Fetches and filters models suitable for text generation."""
        try:
            models = self.client.models.list()
            # Filter for models that support generating content and are relevant Gemini models
            # We look for models with 'generateContent' in supported_methods
            # and name containing 'gemini'
            filtered_models = []
            for m in models:
                if "generateContent" in m.supported_generation_methods and "gemini" in m.name:
                    # Clean the name (remove 'models/' prefix if present)
                    name = m.name.replace("models/", "")
                    filtered_models.append(name)
            
            # Sort models, putting newer ones at the top if possible
            # Just alphabetical sort for now
            return sorted(filtered_models, reverse=True)
        except Exception as e:
            raise Exception(f"Failed to fetch models: {str(e)}")

    def generate_minutes(self, transcript, model_name):
        """Generates meeting minutes from the transcript."""
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録を作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めてください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )
        
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate minutes: {str(e)}")
