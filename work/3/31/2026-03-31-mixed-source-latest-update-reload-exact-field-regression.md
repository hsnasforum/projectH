# 2026-03-31 mixed-source latest_update reload exact-field regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `handle_chat` 두 번 호출(initial mixed-source latest_update 검색 → 같은 세션에서 reload)의 exact badge field 보존을 검증하는 integration regression 1개 추가를 지시.
- 이전 라운드 `/verify`에서 reload show-only 경로에 대한 dedicated regression이 아직 없다는 남은 리스크가 명시적으로 식별됨.
- 근거: `work/3/31/2026-03-31-mixed-source-latest-update-badge-ordering-regression.md`, `verify/3/31/2026-03-31-mixed-source-latest-update-badge-ordering-regression-verification.md`

## 핵심 변경
- `test_handle_chat_mixed_source_latest_update_reload_exact_fields` 추가 (`tests/test_web_app.py`)
  - 첫 호출: official-domain(`store.steampowered.com`) + news-domain(`news.example.com`) fixture로 `"최신 스팀 할인 소식 검색해줘"` → `web_search_record_path` 획득
  - 둘째 호출: 같은 세션에서 `"방금 검색한 결과 다시 보여줘"` → reload
  - exact assertion:
    - `second["response"]["actions_taken"] == ["load_web_search_record"]`
    - `second["response"]["web_search_record_path"] == first["response"]["web_search_record_path"]`
    - `second["response"]["response_origin"]["answer_mode"] == "latest_update"`
    - `second["response"]["response_origin"]["verification_label"] == "공식+기사 교차 확인"`
    - `second["response"]["response_origin"]["source_roles"] == ["보조 기사", "공식 기반"]`
- production 코드 변경 없음 — test-only slice
- UI, Playwright smoke, docs, approval flow, reviewed-memory 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 102 tests, OK (1.751s)
- `git diff --check -- tests/test_web_app.py app/web.py storage/web_search_store.py core/agent_loop.py`: 통과

## 남은 리스크
- reload 경로의 `_reuse_web_search_record`는 `intent_kind`/`answer_mode`/`freshness_risk` 없이 `_rank_web_search_sources`를 호출. 현재 fixture에서는 query의 "최신" 키워드가 `_infer_web_query_profile`에서 "live"로 분류되어 정상 동작하지만, 키워드가 없는 latest_update 검색 기록의 reload에서는 `reloaded_answer_mode`가 "general"로 떨어질 가능성 있음.
- dirty worktree가 여전히 넓음.
