# 2026-03-31 load_web_search_record_id single-source latest_update exact-field regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `load_web_search_record_id` 기반 history-card 선택 경로의 latest_update exact-field 보호 regression 1개 추가를 지시.
- 기존 `test_handle_chat_can_reload_specific_web_search_record_by_id`는 `load_web_search_record_id` 경로를 확인하지만 `response_origin` exact field를 검증하지 않음.
- 기존 `test_handle_chat_single_source_latest_update_reload_exact_fields`는 자연어 reload 경로를 검증하지만 `load_web_search_record_id`를 사용하지 않음.
- 두 경로의 교차 영역(history-card 직접 선택 + single-source exact field)에 dedicated regression이 없었음.
- 근거: `work/3/31/2026-03-31-single-source-latest-update-reload-exact-field-regression.md`, `verify/3/31/2026-03-31-single-source-latest-update-reload-exact-field-regression-verification.md`

## 핵심 변경
- `test_handle_chat_load_web_search_record_id_single_source_latest_update_exact_fields` 추가 (`tests/test_web_app.py`)
  - 첫 호출: single-source fixture(`example.com/seoul-weather`)로 `"서울 날씨 검색해봐"` → `record_id` 획득
  - 둘째 호출: 같은 세션에서 `load_web_search_record_id=<record_id>`만 전달 (user_text 없음)
  - exact assertion:
    - `second["response"]["actions_taken"] == ["load_web_search_record"]`
    - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
    - `second["response"]["response_origin"]["answer_mode"] == "latest_update"`
    - `second["response"]["response_origin"]["verification_label"] == "단일 출처 참고"`
    - `second["response"]["response_origin"]["source_roles"] == ["보조 출처"]`
- production 코드 변경 없음 — test-only slice
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 104 tests, OK (1.627s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- `_reuse_web_search_record`의 show-only 경로는 저장된 `response_origin`을 그대로 재사용하지 않고 현재 record 기반으로 다시 계산함. `_build_user_text`가 `load_web_search_record_id`만 있을 때 `"불러와"`를 포함하는 텍스트를 생성하므로 show_only 경로를 타지만, 이 암묵적 의존이 바뀌면 regression이 될 수 있음.
- dirty worktree가 여전히 넓음.
