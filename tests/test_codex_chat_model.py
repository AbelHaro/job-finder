import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ValidationError

from job_finder.services.codex_chat_model import CodexChatModel


class Answer(BaseModel):
    score: float
    reason: str = ""


class CodexChatModelTests(unittest.TestCase):
    def run_cli(self, command, **kwargs):
        self.command = command
        self.request = kwargs
        schema = Path(command[command.index("--output-schema") + 1])
        self.schema = json.loads(schema.read_text())
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(self.response)
        return subprocess.CompletedProcess(command, 0)

    def setUp(self):
        self.response = '{"score": 0.7, "reason": "fit"}'
        self.model = CodexChatModel(model_name="chosen-model")
        self.messages = [HumanMessage(content="Rank this job")]

    def test_structured_output_and_subscription_configuration(self):
        with (
            patch.dict(
                os.environ, {"OPENAI_API_KEY": "unused", "CODEX_API_KEY": "unused"}
            ),
            patch(
                "job_finder.services.codex_chat_model.subprocess.run",
                side_effect=self.run_cli,
            ),
        ):
            result = self.model.with_structured_output(Answer, include_raw=True).invoke(
                self.messages
            )
        self.assertEqual(result["parsed"].score, 0.7)
        self.assertIsNone(result["parsing_error"])
        self.assertNotIn("OPENAI_API_KEY", self.request["env"])
        self.assertNotIn("CODEX_API_KEY", self.request["env"])
        self.assertIn('forced_login_method="chatgpt"', self.command)
        self.assertIn("--ignore-user-config", self.command)
        self.assertIn("chosen-model", self.command)
        self.assertEqual(self.schema["required"], ["score", "reason"])
        self.assertFalse(self.schema["additionalProperties"])
        self.assertNotIn("default", self.schema["properties"]["reason"])
        self.assertFalse(Path(self.request["cwd"]).exists())

    def test_invalid_json_obeys_include_raw(self):
        self.response = "invalid JSON"
        with patch(
            "job_finder.services.codex_chat_model.subprocess.run",
            side_effect=self.run_cli,
        ):
            result = self.model.with_structured_output(Answer, include_raw=True).invoke(
                self.messages
            )
            self.assertIsNone(result["parsed"])
            self.assertIsInstance(result["parsing_error"], ValidationError)
            with self.assertRaises(ValidationError):
                self.model.with_structured_output(Answer).invoke(self.messages)

    def test_process_failures_are_actionable(self):
        cases = [
            (FileNotFoundError(), "codex login"),
            (subprocess.TimeoutExpired("codex", 300), "timed out"),
        ]
        for error, message in cases:
            with (
                self.subTest(error=error),
                patch(
                    "job_finder.services.codex_chat_model.subprocess.run",
                    side_effect=error,
                ),
                self.assertRaisesRegex(RuntimeError, message),
            ):
                self.model.invoke(self.messages)
        with (
            patch(
                "job_finder.services.codex_chat_model.subprocess.run",
                return_value=subprocess.CompletedProcess([], 1),
            ),
            self.assertRaisesRegex(RuntimeError, "login status"),
        ):
            self.model.invoke(self.messages)
        with (
            patch(
                "job_finder.services.codex_chat_model.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0),
            ),
            self.assertRaisesRegex(RuntimeError, "no final response"),
        ):
            self.model.invoke(self.messages)
