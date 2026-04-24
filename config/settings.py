from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_SESSIONS_DIR = "data/sessions"
DEFAULT_TASK_LOG_PATH = "logs/task_log.jsonl"
DEFAULT_NOTES_DIR = "data/notes"
DEFAULT_ARTIFACTS_DIR = "data/artifacts"
DEFAULT_CORRECTIONS_DIR = "data/corrections"
DEFAULT_PREFERENCES_DIR = "data/preferences"
DEFAULT_WEB_SEARCH_HISTORY_DIR = "data/web-search"
DEFAULT_STORAGE_BACKEND = "sqlite"
DEFAULT_SQLITE_DB_PATH = "data/projecth.db"


@dataclass(slots=True)
class AppSettings:
    app_name: str = "local-ai-assistant"
    sessions_dir: str = DEFAULT_SESSIONS_DIR
    task_log_path: str = DEFAULT_TASK_LOG_PATH
    notes_dir: str = DEFAULT_NOTES_DIR
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    model_provider: str = "mock"
    web_search_permission: str = "disabled"
    artifacts_dir: str = DEFAULT_ARTIFACTS_DIR
    corrections_dir: str = DEFAULT_CORRECTIONS_DIR
    preferences_dir: str = DEFAULT_PREFERENCES_DIR
    web_search_history_dir: str = DEFAULT_WEB_SEARCH_HISTORY_DIR
    web_search_timeout_seconds: float = 10.0
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    ollama_timeout_seconds: float = 180.0
    storage_backend: str = DEFAULT_STORAGE_BACKEND  # "json" | "sqlite"
    sqlite_db_path: str = DEFAULT_SQLITE_DB_PATH

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            app_name=os.getenv("LOCAL_AI_APP_NAME", "local-ai-assistant"),
            sessions_dir=os.getenv("LOCAL_AI_SESSIONS_DIR", DEFAULT_SESSIONS_DIR),
            task_log_path=os.getenv("LOCAL_AI_TASK_LOG_PATH", DEFAULT_TASK_LOG_PATH),
            notes_dir=os.getenv("LOCAL_AI_NOTES_DIR", DEFAULT_NOTES_DIR),
            web_host=os.getenv("LOCAL_AI_WEB_HOST", "127.0.0.1"),
            web_port=int(os.getenv("LOCAL_AI_WEB_PORT", "8765")),
            model_provider=os.getenv("LOCAL_AI_MODEL_PROVIDER", "mock"),
            web_search_permission=os.getenv("LOCAL_AI_WEB_SEARCH_PERMISSION", "disabled"),
            artifacts_dir=os.getenv("LOCAL_AI_ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR),
            corrections_dir=os.getenv("LOCAL_AI_CORRECTIONS_DIR", DEFAULT_CORRECTIONS_DIR),
            preferences_dir=os.getenv("LOCAL_AI_PREFERENCES_DIR", DEFAULT_PREFERENCES_DIR),
            web_search_history_dir=os.getenv("LOCAL_AI_WEB_SEARCH_HISTORY_DIR", DEFAULT_WEB_SEARCH_HISTORY_DIR),
            web_search_timeout_seconds=float(os.getenv("LOCAL_AI_WEB_SEARCH_TIMEOUT_SECONDS", "10")),
            ollama_base_url=os.getenv("LOCAL_AI_OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("LOCAL_AI_OLLAMA_MODEL", ""),
            ollama_timeout_seconds=float(
                os.getenv("LOCAL_AI_OLLAMA_TIMEOUT_SECONDS", "180")
            ),
            storage_backend=os.getenv("LOCAL_AI_STORAGE_BACKEND", DEFAULT_STORAGE_BACKEND),
            sqlite_db_path=os.getenv("LOCAL_AI_SQLITE_DB_PATH", DEFAULT_SQLITE_DB_PATH),
        )
