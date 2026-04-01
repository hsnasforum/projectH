# 2026-03-31 zero-strong-slot natural reload exact-field retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, zero-strong-slot entity-card record를 자연어 reload했을 때 downgraded exact field가 유지되는지 확인하도록 지시.
- 이전 라운드에서 history-card reload 경로는 잠갔으나, 자연어 `"방금 검색한 결과 다시 보여줘"` 경로는 아직 explicit regression이 없었음.

## 핵심 변경
- `test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` 추가 (`tests/test_web_app.py`)
  - fixture: wiki 2개이지만 cross-verify되지 않는 zero-strong-slot entity-card
  - 첫 호출: entity search → initial downgraded `verification_label` 캡처
  - 둘째 호출: `"방금 검색한 결과 다시 보여줘"` 자연어 reload
  - 검증: `answer_mode`, `verification_label`, `source_roles`, `web_search_record_path`가 initial과 일치
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 119 tests, OK (2.047s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- zero-strong-slot badge semantics family는 initial response downgrade + history summary serialization + history-card reload + natural reload 4개 경로를 모두 explicit regression으로 잠금. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
