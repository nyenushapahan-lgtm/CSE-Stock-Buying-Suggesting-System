import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.services.ManageAI import chat_with_ollama


class OllamaClientTests(unittest.TestCase):
    @patch.dict("os.environ", {"OLLAMA_API_KEY": "test-key"})
    @patch("src.services.ManageAI.OpenAI")
    def test_chat_uses_ollama_cloud_and_returns_reply(self, openai_mock):
        client = openai_mock.return_value
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Test reply"))]
        )

        reply = chat_with_ollama("Hello")

        self.assertEqual(reply, "Test reply")
        openai_mock.assert_called_once_with(
            api_key="test-key",
            base_url="https://ollama.com/v1",
            timeout=60.0,
        )
        client.chat.completions.create.assert_called_once_with(
            model="gemma4:31b",
            messages=[{"role": "user", "content": "Hello"}],
        )

    @patch.dict("os.environ", {"OLLAMA_API_KEY": ""})
    @patch("src.services.ManageAI.OpenAI")
    def test_missing_key_is_reported_without_making_request(self, openai_mock):
        with self.assertRaisesRegex(RuntimeError, "OLLAMA_API_KEY is not set"):
            chat_with_ollama("Hello")

        openai_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
