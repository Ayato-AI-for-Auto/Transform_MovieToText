import unittest
from unittest.mock import patch

from src.llm.providers.ollama_client import (
    CloudModelBlockedError,
    OllamaLocalClient,
)


class TestOllamaLocalClient(unittest.TestCase):
    def setUp(self):
        self.local_config = {"base_url": "http://localhost:11434"}

    @patch("src.llm.providers.ollama_client.Client")
    def test_ollama_local_client_basic(self, mock_client_class):
        """Verify local client connects to localhost and produces responses."""
        mock_instance = mock_client_class.return_value
        mock_instance.chat.return_value = {"message": {"content": "local response"}}

        client = OllamaLocalClient(**self.local_config)
        self.assertEqual(client.host, "http://localhost:11434")

        response = client.generate_minutes("transcript", model_name="gemma3:1b")
        self.assertEqual(response, "local response")

        mock_client_class.assert_called_with(host="http://localhost:11434")

    @patch("src.llm.providers.ollama_client.Client")
    def test_external_url_forced_to_localhost(self, mock_client_class):
        """SECURITY: External URLs must be forced to localhost."""
        client = OllamaLocalClient(base_url="https://ollama.com")
        self.assertEqual(client.host, "http://localhost:11434")
        mock_client_class.assert_called_with(host="http://localhost:11434")

    @patch("src.llm.providers.ollama_client.Client")
    def test_cloud_model_blocked_at_inference(self, mock_client_class):
        """SECURITY: Cloud model names must be rejected at inference time."""
        client = OllamaLocalClient(**self.local_config)

        with self.assertRaises(CloudModelBlockedError):
            client.chat("llama3:cloud", [{"role": "user", "content": "test"}])

        with self.assertRaises(CloudModelBlockedError):
            client.generate_minutes("transcript", model_name="gemma3:cloud")

        with self.assertRaises(CloudModelBlockedError):
            client.extract_category("transcript", model_name="remote-model")

        with self.assertRaises(CloudModelBlockedError):
            client.generate_title("transcript", model_name="hosted-llama")

    @patch("src.llm.providers.ollama_client.Client")
    def test_local_model_allowed_at_inference(self, mock_client_class):
        """Local model names must pass through without error."""
        mock_instance = mock_client_class.return_value
        mock_instance.chat.return_value = {"message": {"content": "ok"}}

        client = OllamaLocalClient(**self.local_config)
        # These should NOT raise
        result = client.chat("gemma3:1b", [{"role": "user", "content": "test"}])
        self.assertEqual(result, "ok")

    @patch("src.llm.providers.ollama_client.Client")
    def test_cloud_model_filtered_from_list(self, mock_client_class):
        """SECURITY: Cloud models must not appear in get_available_models()."""
        mock_instance = mock_client_class.return_value
        # Simulate Ollama returning both local and cloud models
        mock_model_local = type("Model", (), {"model": "gemma3:1b"})()
        mock_model_cloud = type("Model", (), {"model": "llama3:cloud"})()
        mock_model_remote = type("Model", (), {"model": "remote-phi4"})()
        mock_models_response = type("ListResponse", (), {"models": [mock_model_local, mock_model_cloud, mock_model_remote]})()

        mock_instance.list.return_value = mock_models_response
        # Mock show() to return local model details
        mock_instance.show.return_value = {"details": {"family": "gemma", "quantization_level": "Q4_K_M"}}

        client = OllamaLocalClient(**self.local_config)
        models = client.get_available_models()

        self.assertIn("gemma3:1b", models)
        self.assertNotIn("llama3:cloud", models)
        self.assertNotIn("remote-phi4", models)


if __name__ == "__main__":
    unittest.main()
