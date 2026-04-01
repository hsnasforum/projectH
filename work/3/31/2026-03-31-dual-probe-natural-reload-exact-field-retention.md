# 2026-03-31 dual-probe entity natural reload exact-field retention

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 실제 dual-probe entity search가 만든 최근 record를 자연어 reload했을 때 badge/meta exact field가 initial과 일관되는지 확인하도록 지시.
- 이전 라운드에서 single-source entity-card natural reload exact field는 잠갔으나, dual-probe entity-card natural reload exact field는 아직 explicit regression이 없었음.

## 핵심 변경
- `test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields` 추가 (`tests/test_web_app.py`)
  - `_FakeWebSearchTool`로 실제 dual-probe entity search 수행 (namu.wiki + pearlabyss.com platform + service probes)
  - 첫 호출: entity search → initial `response_origin`과 `web_search_record_path` 캡처, `answer_mode == "entity_card"` 확인
  - 둘째 호출: `"방금 검색한 결과 다시 보여줘"` 자연어 reload
  - 검증:
    - `reload_origin["answer_mode"] == "entity_card"`
    - `reload_origin["verification_label"] == first_origin["verification_label"]`
    - `reload_origin["source_roles"] == first_origin["source_roles"]`
    - `reload["web_search_record_path"] == first_record_path`
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 115 tests, OK (1.947s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app에 test-only 추가)

## 남은 리스크
- dirty worktree가 여전히 넓음.
