import unittest

from app.localization import localize_runtime_status_payload, localize_session, localize_text


class LocalizationTest(unittest.TestCase):
    def test_localize_runtime_status_detail(self) -> None:
        localized = localize_runtime_status_payload(
            {
                "provider": "ollama",
                "configured_model": "qwen2.5:3b",
                "reachable": True,
                "configured_model_available": True,
                "detail": "Ollama is reachable and model 'qwen2.5:3b' is installed.",
            }
        )

        self.assertIsNotNone(localized)
        self.assertIn("설치되어 있습니다", localized["detail"])

    def test_localize_session_translates_user_text_and_note_preview(self) -> None:
        session = {
            "session_id": "demo-session",
            "messages": [
                {"role": "user", "text": "Summarize /tmp/demo.md"},
                {
                    "role": "assistant",
                    "text": "Saved summary note to /tmp/demo-summary.md.",
                    "note_preview": "# Summary of demo.md\n\nSource: /tmp/demo.md\n\n## Summary\n[mock-summary] hello",
                },
            ],
        }

        localized = localize_session(session)

        self.assertEqual(localized["messages"][0]["text"], "/tmp/demo.md 파일을 요약해 주세요.")
        self.assertIn("요약 노트를 /tmp/demo-summary.md에 저장했습니다.", localized["messages"][1]["text"])
        self.assertIn("# demo.md 요약", localized["messages"][1]["note_preview"])
        self.assertIn("[모의 요약]", localized["messages"][1]["note_preview"])

    def test_localize_text_translates_search_notice(self) -> None:
        localized = localize_text(
            "Note: Skipped 2 scanned or image-only PDF file(s) during search because OCR is not supported in this MVP. Examples: a.pdf, b.pdf"
        )

        self.assertIn("참고:", localized)
        self.assertIn("OCR 미지원", localized)

    def test_localize_text_translates_ollama_wsl_hint(self) -> None:
        localized = localize_text(
            "Unable to reach Ollama at http://localhost:11434. Is the local runtime running? "
            "If this app is running inside WSL, localhost may point to the Linux environment instead of Windows. "
            "Start Ollama in the same environment or use the Windows host IP as Base URL."
        )

        self.assertIn("Ollama에 연결할 수 없습니다", localized)
        self.assertIn("WSL", localized)
        self.assertIn("Windows 호스트 IP", localized)

    def test_localize_text_translates_ollama_timeout_hint(self) -> None:
        localized = localize_text(
            "Ollama request timed out after 180 seconds while waiting for model 'qwen2.5:3b'. "
            "The local model may still be loading or generating. Retry once, or increase LOCAL_AI_OLLAMA_TIMEOUT_SECONDS."
        )

        self.assertIn("180초", localized)
        self.assertIn("qwen2.5:3b", localized)
        self.assertIn("LOCAL_AI_OLLAMA_TIMEOUT_SECONDS", localized)


if __name__ == "__main__":
    unittest.main()
