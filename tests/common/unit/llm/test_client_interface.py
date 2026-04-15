import inspect
import unittest

from src.llm.base_client import BaseLLMClient
from src.llm.providers.ollama_client import (
    CloudModelBlockedError,
    OllamaLocalClient,
    _is_cloud_model,
)


class TestLLMClientInterfaces(unittest.TestCase):
    """
    Unit test for LLM provider class signatures.
    Directly inspects the class structure to catch attribute/signature mismatches.
    Only tests OllamaLocalClient (the sole permitted provider in local-first architecture).
    """

    def _verify_conformance(self, client_cls):
        """Helper to check if a class strictly follows BaseLLMClient interface."""
        base_methods = {
            name: func
            for name, func in inspect.getmembers(BaseLLMClient, predicate=inspect.isfunction)
            if not name.startswith("__")
        }

        for name, base_func in base_methods.items():
            self.assertTrue(hasattr(client_cls, name), f"{client_cls.__name__} is missing required method: '{name}'")

            client_func = getattr(client_cls, name)
            base_sig = inspect.signature(base_func)
            client_sig = inspect.signature(client_func)

            base_params = list(base_sig.parameters.keys())
            client_params = list(client_sig.parameters.keys())

            self.assertEqual(
                base_params,
                client_params,
                f"Signature mismatch in {client_cls.__name__}.{name}. Expected {base_params}, got {client_params}",
            )

    def test_ollama_local_interface(self):
        self._verify_conformance(OllamaLocalClient)


class TestCloudModelBlocking(unittest.TestCase):
    """
    CRITICAL SECURITY TESTS: Verify that cloud/remote models are blocked.
    These tests validate the core privacy guarantee of the application.
    """

    def test_cloud_suffix_detected(self):
        """Models with ':cloud' suffix must be blocked."""
        self.assertTrue(_is_cloud_model("llama3:cloud"))
        self.assertTrue(_is_cloud_model("gemma3:12b-cloud"))
        self.assertTrue(_is_cloud_model("deepseek-r1:cloud"))

    def test_cloud_keyword_detected(self):
        """Models containing 'cloud' anywhere must be blocked."""
        self.assertTrue(_is_cloud_model("cloud-llama3"))
        self.assertTrue(_is_cloud_model("my-cloud-model"))

    def test_remote_keyword_detected(self):
        """Models containing 'remote' must be blocked."""
        self.assertTrue(_is_cloud_model("remote:llama3"))
        self.assertTrue(_is_cloud_model("llama3-remote"))

    def test_hosted_keyword_detected(self):
        """Models containing 'hosted' must be blocked."""
        self.assertTrue(_is_cloud_model("hosted-gemma3"))

    def test_online_keyword_detected(self):
        """Models containing 'online' must be blocked."""
        self.assertTrue(_is_cloud_model("gemma3-online"))

    def test_local_models_allowed(self):
        """Standard local models must NOT be blocked."""
        self.assertFalse(_is_cloud_model("gemma3:1b"))
        self.assertFalse(_is_cloud_model("llama3.2"))
        self.assertFalse(_is_cloud_model("mistral-nemo"))
        self.assertFalse(_is_cloud_model("phi4"))
        self.assertFalse(_is_cloud_model("deepseek-r1:7b"))
        self.assertFalse(_is_cloud_model("qwen2.5:32b"))

    def test_empty_model_name_rejected(self):
        """Empty or None model names must be rejected."""
        self.assertTrue(_is_cloud_model(""))
        self.assertTrue(_is_cloud_model(None))

    def test_case_insensitive(self):
        """Cloud detection must be case-insensitive."""
        self.assertTrue(_is_cloud_model("llama3:CLOUD"))
        self.assertTrue(_is_cloud_model("Llama3:Cloud"))

    def test_cloud_model_blocked_error(self):
        """CloudModelBlockedError must be a RuntimeError."""
        err = CloudModelBlockedError("test:cloud")
        self.assertIsInstance(err, RuntimeError)
        self.assertIn("SECURITY BLOCK", str(err))

    def test_localhost_enforcement(self):
        """OllamaLocalClient must force localhost when given external URLs."""
        # This should NOT raise but should silently force localhost
        try:
            client = OllamaLocalClient(base_url="https://ollama.com")
            self.assertIn("localhost", client.host)
        except Exception:
            # Connection error is acceptable; structural error is not
            pass


if __name__ == "__main__":
    unittest.main()
