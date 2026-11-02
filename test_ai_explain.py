import io
import json
import os
import unittest
from unittest.mock import patch
from ai_explain import explain


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AIAdapterTests(unittest.TestCase):
    def test_model_receives_facts_only_and_returns_explanation(self):
        def opener(request, timeout):
            self.assertEqual(timeout, 30)
            payload = json.loads(request.data)
            self.assertEqual(payload["store"], False)
            self.assertIn("INC-17", payload["input"])
            return Response(json.dumps({"output": [{"content": [{"type": "output_text", "text": "Check log:L-1"}]}]}).encode())

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}):
            self.assertEqual(explain("incident", {"alert_id": "INC-17"}, opener), "Check log:L-1")

    def test_missing_credentials_fail_without_network(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "OPENAI_MODEL": ""}):
            with self.assertRaises(RuntimeError):
                explain("incident", {})

    def test_items_with_null_content_are_skipped(self):
        body = {"output": [{"type": "reasoning", "content": None},
                           {"type": "message", "content": [{"type": "output_text", "text": "ok"}]}]}

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}):
            self.assertEqual(explain("incident", {}, lambda request, timeout: Response(json.dumps(body).encode())), "ok")


if __name__ == "__main__":
    unittest.main()
