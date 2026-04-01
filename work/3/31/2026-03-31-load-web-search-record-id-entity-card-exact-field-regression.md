# 2026-03-31 load_web_search_record_id entity-card exact-field regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `load_web_search_record_id` 기반 history-card 선택 경로의 entity-card exact-field 보호 regression 1개 추가를 지시.
- 기존 `test_handle_chat_entity_web_search_serializes_claim_coverage`는 entity-card 첫 호출의 claim_coverage를 검증하지만 reload 경로를 타지 않음.
- 기존 `test_handle_chat_can_reload_specific_web_search_record_by_id`는 `load_web_search_record_id` 경로를 확인하지만 `response_origin` exact field를 검증하지 않음.
- 이전 라운드에서 single-source, mixed-source `load_web_search_record_id` exact-field regression은 추가했으나 entity-card 버전은 아직 없었음.
- 근거: `work/3/31/2026-03-31-load-web-search-record-id-mixed-source-exact-field-regression.md`, `verify/3/31/2026-03-31-load-web-search-record-id-mixed-source-latest-update-exact-field-regression-verification.md`

## 핵심 변경
- `test_handle_chat_load_web_search_record_id_entity_card_exact_fields` 추가 (`tests/test_web_app.py`)
  - 첫 호출: entity-card fixture(namu.wiki `붉은사막`)로 `"붉은사막에 대해 알려줘"` → `record_id` 획득
  - 둘째 호출: 같은 세션에서 `load_web_search_record_id=<record_id>`만 전달 (user_text 없음)
  - exact assertion:
    - `second["response"]["actions_taken"] == ["load_web_search_record"]`
    - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
    - `second["response"]["response_origin"]["answer_mode"] == "entity_card"`
    - `second["response"]["response_origin"]["verification_label"] == "설명형 단일 출처"`
    - `second["response"]["response_origin"]["source_roles"] == ["백과 기반"]`
- production 코드 변경 없음 — test-only slice
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 106 tests, OK (1.607s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- `_build_user_text`가 `load_web_search_record_id`만 있을 때 `"불러와"` 포함 텍스트를 생성하여 show_only 경로를 타는 암묵적 의존은 이전 라운드와 동일하게 존재.
- dirty worktree가 여전히 넓음.
