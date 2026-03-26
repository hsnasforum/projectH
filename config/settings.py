from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class AppSettings:
    app_name: str = "local-ai-assistant"
    sessions_dir: str = "data/sessions"
    task_log_path: str = "logs/task_log.jsonl"
    notes_dir: str = "data/notes"
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    model_provider: str = "mock"
    web_search_permission: str = "disabled"
    web_search_history_dir: str = "data/web-search"
    web_search_timeout_seconds: float = 10.0
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 180.0

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            app_name=os.getenv("LOCAL_AI_APP_NAME", "local-ai-assistant"),
            sessions_dir=os.getenv("LOCAL_AI_SESSIONS_DIR", "data/sessions"),
            task_log_path=os.getenv("LOCAL_AI_TASK_LOG_PATH", "logs/task_log.jsonl"),
            notes_dir=os.getenv("LOCAL_AI_NOTES_DIR", "data/notes"),
            web_host=os.getenv("LOCAL_AI_WEB_HOST", "127.0.0.1"),
            web_port=int(os.getenv("LOCAL_AI_WEB_PORT", "8765")),
            model_provider=os.getenv("LOCAL_AI_MODEL_PROVIDER", "mock"),
            web_search_permission=os.getenv("LOCAL_AI_WEB_SEARCH_PERMISSION", "disabled"),
            web_search_history_dir=os.getenv("LOCAL_AI_WEB_SEARCH_HISTORY_DIR", "data/web-search"),
            web_search_timeout_seconds=float(os.getenv("LOCAL_AI_WEB_SEARCH_TIMEOUT_SECONDS", "10")),
            ollama_base_url=os.getenv("LOCAL_AI_OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("LOCAL_AI_OLLAMA_MODEL", ""),
            ollama_timeout_seconds=float(
                os.getenv("LOCAL_AI_OLLAMA_TIMEOUT_SECONDS", "180")
            ),
        )
