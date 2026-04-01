# 2026-03-31 dual-probe history-card reload exact-field retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 실제 dual-probe entity search가 만든 record를 `load_web_search_record_id` history-card reload했을 때 exact field가 initial과 일관되는지 확인하도록 지시.
- 이전 라운드에서 자연어 reload 경로의 dual-probe exact field는 잠갔으나, history-card 선택 경로의 dual-probe exact field는 아직 explicit regression이 없었음.

## 핵심 변경
- `test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields` 추가 (`tests/test_web_app.py`)
  - `_FakeWebSearchTool`로 실제 dual-probe entity search 수행
  - 첫 호출: entity search → initial `response_origin`과 `web_search_record_path` 캡처, `record_id` 획득
  - 둘째 호출: `load_web_search_record_id` history-card reload
  - 검증:
    - `reload_origin["answer_mode"] == "entity_card"`
    - `reload_origin["verification_label"] == first_origin["verification_label"]`
    - `reload_origin["source_roles"] == first_origin["source_roles"]`
    - `reload["web_search_record_path"] == first_record_path`
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 116 tests, OK (1.960s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음

## 남은 리스크
- entity-card reload exact-field family는 single-source(자연어+history-card) + dual-probe(자연어+history-card) 4개 경로를 모두 explicit regression으로 잠금. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
