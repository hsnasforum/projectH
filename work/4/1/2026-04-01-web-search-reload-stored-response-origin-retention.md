# 2026-04-01 web search reload stored response_origin retention

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, history reload에서 stored `response_origin`의 exact fields를 우선 재사용하도록 지시.
- 기존 `_reuse_web_search_record()`는 stored `response_origin`을 무시하고 `_build_web_search_origin()`으로 재계산하여, badge/verification_label/source_roles가 ranking 변화에 따라 drift할 수 있는 user-visible continuity 리스크.

## 핵심 변경
- `core/agent_loop.py`의 `_reuse_web_search_record()` show-only 경로에서:
  - stored `response_origin`에 `answer_mode`가 있으면 그대로 사용
  - stored `response_origin`이 비어 있거나 `answer_mode`가 없을 때만 `_build_web_search_origin()` fallback 유지
- `tests/test_web_app.py`에 `test_handle_chat_entity_card_reload_preserves_stored_response_origin` 추가
  - entity search → load_web_search_record_id reload에서 `answer_mode`, `verification_label`, `source_roles`, `badge`, `provider`가 initial stored 값 그대로 보존되는지 확인

## 검증
- `python3 -m unittest -v tests.test_web_app`: 182 tests, OK (3.189s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- non-show-only reload path (`_respond_with_active_context` 경로)는 아직 재계산을 사용. 이번 라운드 범위 밖.
- dirty worktree가 여전히 넓음.
