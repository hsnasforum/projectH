# 2026-03-31 single-source latest_update reload exact-field regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, single-source `latest_update` reload exact-field regression 1개 추가를 지시.
- 이전 라운드 `/verify`에서 mixed-source reload 보호는 완료되었으나, single-source reload 경로의 dedicated regression이 아직 없다는 남은 리스크가 명시적으로 식별됨.
- 근거: `work/3/31/2026-03-31-mixed-source-latest-update-reload-exact-field-regression.md`, `verify/3/31/2026-03-31-mixed-source-latest-update-reload-exact-field-regression-verification.md`

## 핵심 변경
- `test_handle_chat_single_source_latest_update_reload_exact_fields` 추가 (`tests/test_web_app.py`)
  - 첫 호출: single-source fixture(`example.com/seoul-weather`)로 `"서울 날씨 검색해봐"` → `web_search_record_path` 획득
  - 둘째 호출: 같은 세션에서 `"방금 검색한 결과 다시 보여줘"` → reload
  - exact assertion:
    - `second["response"]["actions_taken"] == ["load_web_search_record"]`
    - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
    - `second["response"]["response_origin"]["answer_mode"] == "latest_update"`
    - `second["response"]["response_origin"]["verification_label"] == "단일 출처 참고"`
    - `second["response"]["response_origin"]["source_roles"] == ["보조 출처"]`
- production 코드 변경 없음 — test-only slice
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 103 tests, OK (1.653s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- `_reuse_web_search_record`의 show-only 경로는 저장된 `response_origin`을 그대로 재사용하지 않고 현재 record 기반으로 다시 계산함. 키워드가 없는 latest_update 검색 기록의 reload에서 `reloaded_answer_mode`가 "general"로 떨어질 가능성은 이번 fixture에서는 재현 불가 — 실제 regression 발견 시 production fix 대상.
- dirty worktree가 여전히 넓음.
