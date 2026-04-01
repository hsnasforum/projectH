# 2026-04-01 web search reload follow-up response_origin retention

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, non-show-only reload-follow-up path에서 stored `response_origin`을 보존하도록 지시.
- 기존 코드는 `_respond_with_active_context()` 경로에서 `response.response_origin`이 None이면 `app/web.py`가 runtime default로 채워, WEB/history identity가 drift하는 user-visible continuity 리스크.

## 핵심 변경
- `core/agent_loop.py`의 `_reuse_web_search_record()` non-show-only 경로에서:
  - `_respond_with_active_context()` 응답 후 `response.response_origin`이 None이고 stored `response_origin`에 `answer_mode`가 있으면 stored 값을 설정
  - stored origin이 없거나 `answer_mode`가 없으면 기존 동작 유지
- `tests/test_web_app.py`에 `test_handle_chat_entity_card_reload_follow_up_preserves_stored_response_origin` 추가
  - entity search → load_web_search_record_id + user_text follow-up에서 response_origin이 존재하고 entity_card answer_mode가 유지되는지 확인

## 검증
- `python3 -m unittest -v tests.test_web_app`: 183 tests, OK (3.162s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- `app/web.py`는 건드리지 않았으므로 `response.response_origin`이 이미 non-None인 경우(active_context follow-up이 자체 origin을 생성하는 경우)는 stored origin으로 덮어쓰지 않음. 이는 의도된 동작.
- dirty worktree가 여전히 넓음.
