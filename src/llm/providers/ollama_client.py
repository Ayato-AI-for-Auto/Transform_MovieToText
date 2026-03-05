import logging

from ollama import Client

from src.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class OllamaLocalClient(BaseLLMClient):
    """Client for local Ollama instance."""
    def __init__(self, base_url="http://localhost:11434", **kwargs):
        self.host = base_url
        self.client = Client(host=self.host)

    def get_available_models(self) -> list[str]:
        try:
            models_info = self.client.list()
            if isinstance(models_info, dict) and 'models' in models_info:
                return sorted([m['name'] for m in models_info['models'] if 'name' in m])
            if hasattr(models_info, 'models'):
                return sorted([m.model for m in models_info.models])
            return []
        except Exception as e:
            logger.error(f"Failed to list local Ollama models: {e}")
            return []

    def generate_minutes(self, transcript: str, model_name: str) -> str:
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )
        try:
            response = self.client.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama Local generation error: {e}")
            raise

    def generate(self, prompt, model_name, system_prompt=None):
        """Legacy/Internal helper for direct generation."""
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        return self.client.chat(model=model_name, messages=messages)['message']['content']


class OllamaCloudClient(BaseLLMClient):
    """Client for Ollama Cloud API (Pattern 2)."""
    def __init__(self, api_key="", base_url="https://ollama.com", **kwargs):
        self.host = base_url
        self.api_key = api_key
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        self.client = Client(host=self.host, headers=headers)

    def get_available_models(self) -> list[str]:
        # Cloud might have a fixed set if listing fails
        try:
            models_info = self.client.list()
            if isinstance(models_info, dict) and 'models' in models_info:
                return sorted([m['name'] for m in models_info['models'] if 'name' in m])
            return ["gpt-oss:120b"]
        except Exception as e:
            logger.warning(f"Failed to fetch models from Ollama Cloud: {e}")
            return ["gpt-oss:120b"]

    def generate_minutes(self, transcript: str, model_name: str) -> str:
        prompt = (
            "以下の文字起こしテキストを元に、構造化された議事録をMarkdown形式で作成してください。\n"
            "項目は「会議の概要」「決定事項」「ネクストアクション」を含めて、適切なヘッダーやリスト（# や -）を使用してください。\n\n"
            f"--- 文字起こしテキスト ---\n{transcript}"
        )
        try:
            response = self.client.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama Cloud generation error: {e}")
            raise
            
    def generate(self, prompt, model_name, system_prompt=None):
        """Legacy/Internal helper for direct generation."""
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        return self.client.chat(model=model_name, messages=messages)['message']['content']
