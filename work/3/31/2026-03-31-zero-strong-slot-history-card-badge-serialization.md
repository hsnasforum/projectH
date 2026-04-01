# 2026-03-31 zero-strong-slot history-card badge serialization

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, zero-strong-slot entity-card의 history-card summary에서 downgraded verification_label이 exact하게 직렬화되는지 확인하도록 지시.
- 이전 라운드에서 initial response의 badge downgrade는 잠갔으나, `session.web_search_history` header에 노출되는 직렬화된 badge는 아직 explicit regression이 없었음.

## 핵심 변경
- `test_handle_chat_zero_strong_slot_entity_card_history_badge_serialization` 추가 (`tests/test_web_app.py`)
  - fixture: wiki 2개(namu.wiki + ko.wikipedia.org)이지만 cross-verify되지 않는 텍스트
  - 검증:
    - `history[0]["answer_mode"] == "entity_card"`
    - `history[0]["verification_label"] != "설명형 다중 출처 합의"` (downgraded)
    - `history[0]["verification_label"]` 비어있지 않음
    - `history[0]["source_roles"]` list이고 1개 이상
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 117 tests, OK (2.042s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- dirty worktree가 여전히 넓음.
