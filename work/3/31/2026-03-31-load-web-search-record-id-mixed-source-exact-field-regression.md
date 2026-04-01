# 2026-03-31 load_web_search_record_id mixed-source latest_update exact-field regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `load_web_search_record_id` 기반 history-card 선택 경로의 mixed-source latest_update exact-field 보호 regression 1개 추가를 지시.
- 기존 `test_handle_chat_mixed_source_latest_update_reload_exact_fields`는 자연어 reload 경로에서 mixed-source exact field를 검증하지만 `load_web_search_record_id`를 사용하지 않음.
- 기존 `test_handle_chat_can_reload_specific_web_search_record_by_id`는 `load_web_search_record_id` 경로를 확인하지만 `response_origin` exact field를 검증하지 않음.
- 이전 라운드에서 single-source 버전은 추가했으나, mixed-source(official + news) 버전은 아직 없었음.
- 근거: `work/3/31/2026-03-31-load-web-search-record-id-single-source-latest-update-exact-field-regression.md`, `verify/3/31/2026-03-31-load-web-search-record-id-single-source-latest-update-exact-field-regression-verification.md`

## 핵심 변경
- `test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields` 추가 (`tests/test_web_app.py`)
  - 첫 호출: mixed-source fixture(official `store.steampowered.com` + news `news.example.com`)로 `"최신 스팀 할인 소식 검색해줘"` → `record_id` 획득
  - 둘째 호출: 같은 세션에서 `load_web_search_record_id=<record_id>`만 전달 (user_text 없음)
  - exact assertion:
    - `second["response"]["actions_taken"] == ["load_web_search_record"]`
    - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
    - `second["response"]["response_origin"]["answer_mode"] == "latest_update"`
    - `second["response"]["response_origin"]["verification_label"] == "공식+기사 교차 확인"`
    - `second["response"]["response_origin"]["source_roles"] == ["보조 기사", "공식 기반"]`
- production 코드 변경 없음 — test-only slice
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 105 tests, OK (1.609s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- `_build_user_text`가 `load_web_search_record_id`만 있을 때 `"불러와"` 포함 텍스트를 생성하여 show_only 경로를 타는 암묵적 의존은 single-source 테스트와 동일하게 존재.
- dirty worktree가 여전히 넓음.
