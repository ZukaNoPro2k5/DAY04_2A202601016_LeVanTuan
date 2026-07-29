from __future__ import annotations

import unittest
from unittest.mock import patch

from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall


class OneToolProvider:
    def __init__(self) -> None:
        self.call_count = 0

    def complete(self, messages, tools, **kwargs):
        self.call_count += 1
        if self.call_count > 1:
            raise AssertionError("The model must not receive a fallback round after a total tool failure")
        return ModelResponse(
            text=None,
            tool_calls=[ToolCall(name="timeline", args={"screenname": "domixi"})],
        )


class ToolErrorBoundaryTest(unittest.TestCase):
    @patch(
        "chat.execute_tool_call",
        return_value={
            "tool": "timeline",
            "args": {"screenname": "domixi"},
            "result": {
                "tool": "get_user_tweets",
                "error": "JSONDecodeError",
                "message": "Expecting value",
            },
        },
    )
    def test_total_tool_failure_stops_before_model_fallback(self, _mock_execute):
        provider = OneToolProvider()
        result = run_model_tool_loop(
            provider=provider,
            messages=[{"role": "user", "content": "Tweet mới nhất của Độ Mixi?"}],
            tools=[],
            model=None,
            max_tool_rounds=4,
        )

        self.assertEqual(result["status"], "tool_error")
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(len(result["rounds"]), 1)
        self.assertEqual(len(result["tool_events"]), 1)
        self.assertIn("JSONDecodeError", result["assistant_text"])
        self.assertIn("không thay thế", result["assistant_text"])


if __name__ == "__main__":
    unittest.main()
