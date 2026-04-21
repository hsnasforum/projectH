from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline_gui.tokens as token_module
from pipeline_gui.tokens import (
    collect_claude_usage,
    collect_codex_usage,
    collect_token_usage,
    collect_gemini_usage,
    format_token_usage_note,
)


class PipelineGuiTokensTest(unittest.TestCase):
    def test_collect_claude_usage_sums_global_usage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / ".claude" / "projects" / "proj"
            root.mkdir(parents=True)
            log_path = root / "session.jsonl"
            rows = [
                {
                    "cwd": "/tmp/other",
                    "timestamp": "2026-04-05T01:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": 99,
                            "output_tokens": 1,
                            "cache_creation_input_tokens": 0,
                            "cache_read_input_tokens": 0,
                        }
                    },
                },
                {
                    "cwd": "/tmp/projectH",
                    "timestamp": "2026-04-05T02:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 5,
                            "cache_creation_input_tokens": 1,
                            "cache_read_input_tokens": 4,
                        }
                    },
                },
                {
                    "cwd": "/tmp/projectH",
                    "timestamp": "2026-04-05T03:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": 8,
                            "output_tokens": 2,
                            "cache_creation_input_tokens": 0,
                            "cache_read_input_tokens": 10,
                        }
                    },
                },
            ]
            log_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

            summary = collect_claude_usage(
                Path("/tmp/projectH"),
                root=root.parent,
                today=dt.date(2026, 4, 5),
            )

            self.assertTrue(summary["available"])
            self.assertEqual(summary["input_tokens"], 117)
            self.assertEqual(summary["output_tokens"], 8)
            self.assertEqual(summary["cached_tokens"], 15)
            self.assertEqual(summary["session_tokens"], 125)
            self.assertEqual(summary["today_tokens"], 125)

    def test_collect_codex_usage_reads_global_token_count_and_rate_limits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / ".codex" / "sessions" / "2026" / "04" / "05"
            root.mkdir(parents=True)
            first_log_path = root / "a-rollout.jsonl"
            first_rows = [
                {
                    "timestamp": "2026-04-05T01:00:00Z",
                    "type": "session_meta",
                    "payload": {"cwd": "/tmp/projectH"},
                },
                {
                    "timestamp": "2026-04-05T01:05:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 10,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 115,
                            },
                            "last_token_usage": {
                                "input_tokens": 100,
                                "cached_input_tokens": 40,
                                "output_tokens": 10,
                                "reasoning_output_tokens": 5,
                                "total_tokens": 115,
                            },
                        },
                        "rate_limits": {
                            "primary": {"used_percent": 14.2, "resets_at": 1775377200},
                        },
                    },
                },
            ]
            first_log_path.write_text(
                "\n".join(json.dumps(row) for row in first_rows),
                encoding="utf-8",
            )
            second_log_path = root / "b-rollout.jsonl"
            second_rows = [
                {
                    "timestamp": "2026-04-05T02:00:00Z",
                    "type": "session_meta",
                    "payload": {"cwd": "/tmp/other"},
                },
                {
                    "timestamp": "2026-04-05T02:05:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 20,
                                "cached_input_tokens": 5,
                                "output_tokens": 4,
                                "reasoning_output_tokens": 1,
                                "total_tokens": 25,
                            },
                            "last_token_usage": {
                                "input_tokens": 20,
                                "cached_input_tokens": 5,
                                "output_tokens": 4,
                                "reasoning_output_tokens": 1,
                                "total_tokens": 25,
                            },
                        },
                        "rate_limits": {
                            "primary": {"used_percent": 15.0, "resets_at": 1775377800},
                        },
                    },
                },
            ]
            second_log_path.write_text(
                "\n".join(json.dumps(row) for row in second_rows),
                encoding="utf-8",
            )
            os.utime(first_log_path, (1_000, 1_000))
            os.utime(second_log_path, (2_000, 2_000))

            summary = collect_codex_usage(
                Path("/tmp/projectH"),
                root=root.parent.parent.parent,
                today=dt.date(2026, 4, 5),
            )

            self.assertTrue(summary["available"])
            self.assertEqual(summary["session_tokens"], 25)
            self.assertEqual(summary["today_tokens"], 140)
            self.assertEqual(summary["input_tokens"], 20)
            self.assertEqual(summary["cached_tokens"], 5)
            self.assertEqual(summary["output_tokens"], 4)
            self.assertEqual(summary["reasoning_tokens"], 1)
            self.assertEqual(summary["used_percent"], 15.0)
            self.assertEqual(summary["reset_at"], "17:30")

    def test_collect_gemini_usage_reads_usage_metadata_without_project_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / ".gemini" / "tmp" / "myapp"
            root.mkdir(parents=True)
            payload = [
                {
                    "timestamp": "2026-04-05T04:00:00Z",
                    "usageMetadata": {
                        "promptTokenCount": 12,
                        "candidatesTokenCount": 4,
                        "cachedContentTokenCount": 3,
                        "thoughtsTokenCount": 2,
                        "toolUsePromptTokenCount": 1,
                    },
                }
            ]
            (root / "logs.json").write_text(json.dumps(payload), encoding="utf-8")

            summary = collect_gemini_usage(Path("/tmp/projectH"), root=root.parent)

            self.assertTrue(summary["available"])
            self.assertEqual(summary["input_tokens"], 13)
            self.assertEqual(summary["output_tokens"], 4)
            self.assertEqual(summary["cached_tokens"], 3)
            self.assertEqual(summary["reasoning_tokens"], 2)
            self.assertEqual(summary["session_tokens"], 19)
            self.assertEqual(summary["today_tokens"], 19)

    def test_format_token_usage_note_prefers_usage_summary(self) -> None:
        note = format_token_usage_note(
            {
                "available": True,
                "used_percent": 14.2,
                "session_tokens": 42100,
                "today_tokens": 108200,
                "reset_at": "03:00",
            }
        )
        self.assertEqual(note, "14% 사용 · 세션 42.1k · 오늘 108.2k")

    def test_collect_token_usage_via_wsl_uses_shared_reader_script(self) -> None:
        token_module._TOKEN_CACHE.clear()
        payload = json.dumps(
            {
                "Claude": {
                    "available": True,
                    "session_tokens": 7,
                    "today_tokens": 7,
                }
            }
        )
        with (
            patch.object(token_module, "IS_WINDOWS", True),
            patch.object(token_module, "resolve_project_runtime_file", return_value=Path("/tmp/token_usage_shared.py")) as resolve_mock,
            patch.object(token_module, "_windows_to_wsl_mount", return_value="/mnt/c/shared.py") as mount_mock,
            patch.object(token_module, "_run", return_value=(0, payload)) as run_mock,
        ):
            summary = collect_token_usage(Path("/tmp/projectH"))

        resolve_mock.assert_called_once_with(Path("/tmp/projectH"), "token_usage_shared.py")
        mount_arg = mount_mock.call_args.args[0]
        self.assertEqual(mount_arg, Path("/tmp/token_usage_shared.py"))
        run_mock.assert_called_once_with(["python3", "/mnt/c/shared.py"], timeout=12.0)
        self.assertTrue(summary["Claude"]["available"])
        self.assertEqual(summary["Claude"]["session_tokens"], 7)
        self.assertFalse(summary["Codex"]["available"])
        token_module._TOKEN_CACHE.clear()


if __name__ == "__main__":
    unittest.main()
