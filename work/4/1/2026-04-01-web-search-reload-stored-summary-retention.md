# 2026-04-01 web search reload stored summary retention

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, history reload에서 stored `summary_text`를 우선 재사용하도록 지시.
- 기존 `_reuse_web_search_record()`는 stored record의 `summary_text`를 무시하고 `results/pages`로 다시 요약을 생성하여, badge/source role/claim progress는 유지돼도 본문 summary text가 drift할 수 있는 user-visible evidence continuity 리스크.

## 핵심 변경
- `core/agent_loop.py`의 `_reuse_web_search_record()`에서:
  - stored `summary_text`가 있으면 그대로 사용
  - stored `summary_text`가 비어 있을 때만 기존 `_summarize_web_search_results()` fallback 유지
- `tests/test_web_app.py`에 `test_handle_chat_entity_card_reload_preserves_stored_summary_text` 추가
  - entity search → load_web_search_record_id reload에서 응답 본문에 stored summary text가 그대로 포함되는지 확인

## 검증
- `python3 -m unittest -v tests.test_web_app`: 181 tests, OK (3.118s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- `latest_update` / `general` path의 reload summary continuity도 동일하게 stored summary를 우선 사용하게 됨 (같은 코드 경로). 이는 의도된 동작.
- dirty worktree가 여전히 넓음.
