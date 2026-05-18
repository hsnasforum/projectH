# 2026-04-30 M118 Axis 1 injected_count API exposure

## 변경 파일

- `storage/session_store.py`
- `storage/sqlite/session.py`
- `storage/preference_utils.py`
- `tests/test_session_store.py`
- `tests/test_sqlite_store.py`
- `tests/test_preference_handler.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `security-gate`: `preference_injected` task-log 집계와 로컬 session/task 기록 표면 변경의 승인/로그 경계를 확인.
- `doc-sync`: M117 문서의 "기존 stats 키가 없으면 무시" 설명을 M118 구현 사실과 맞춤.
- `finalize-lite`: 구현 범위, 검증 결과, 미실행/실패 검증을 closeout 전에 정리.
- `work-log-closeout`: `/work` closeout 형식과 필수 섹션을 맞춤.

## 변경 이유

M117의 `get_global_audit_summary()`는 `preference_injected` 이벤트를 스캔하면서 기존 `per_preference_stats` 항목이 있는 선호만 `injected_count`를 누적했다. 이 때문에 주입만 되고 아직 적용/교정 이력이 없는 선호는 집계와 API 표면에서 누락됐다.

## 핵심 변경

- JSON `SessionStore`와 SQLite `SQLiteSessionStore` 모두 유효한 `preference_id`가 있으면 `per_preference_stats.setdefault(...)`로 zeroed entry를 만든 뒤 `injected_count`를 누적하도록 수정.
- `preference_id`가 비어 있거나 detail이 잘못된 `preference_injected` 이벤트는 기존처럼 무시.
- `enrich_preference_reliability()`가 각 선호 응답 dict에 top-level `injected_count`를 추가하고, 기존 `reliability_stats` 구조는 `applied_count` / `corrected_count` 그대로 유지.
- JSON/SQLite store 테스트에서 주입 전용 선호의 `applied_count=0`, `corrected_count=0`, `injected_count=1` 집계를 검증.
- `list_preferences_payload()` 테스트에 `injected_count` 노출과 기본값 `0` 검증 추가.
- PRODUCT_SPEC / ACCEPTANCE_CRITERIA / ARCHITECTURE / MILESTONES / TASK_BACKLOG에 M118의 집계 보정과 API 노출 사실을 최소 반영.

## 검증

- `python3 -m py_compile storage/session_store.py storage/sqlite/session.py storage/preference_utils.py` — PASS
- `python3 -m unittest -v tests.test_session_store` — PASS, 20 tests
- `python3 -m unittest -v tests.test_sqlite_store` — PASS, 47 tests
- `python3 -m unittest -v tests.test_preference_handler` — PASS, 23 tests
- `git diff --check -- storage/session_store.py storage/sqlite/session.py storage/preference_utils.py tests/test_session_store.py tests/test_sqlite_store.py tests/test_preference_handler.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS
- `python3 -m unittest discover -v tests` — FAIL, 1923 tests run, 4 failures, 36 errors

전체 discover 실패 관찰:
- 다수 HTTP/Ollama 테스트가 sandbox의 socket 생성 제한으로 `PermissionError: [Errno 1] Operation not permitted` 발생.
- `tests.test_correction_summary.CorrectionSummaryTest.test_promote_pattern_reports_highly_reliable_false_below_threshold` 단독 재실행도 실패했으나, 실패 지점은 `PreferenceStore.activate_preference()`의 기존 `is_highly_reliable=True` 동작이며 M118 변경 파일과 직접 관련 없음.
- `tests.test_docs_sync.BrowserSmokeInventoryDocsParityTest` 단독 재실행도 `docs/ACCEPTANCE_CRITERIA.md` 127 vs `docs/NEXT_STEPS.md`/`README.md` 126 smoke count 불일치로 실패. 이번 변경은 해당 count line을 수정하지 않음.
- `tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_live_operator_request_header_canonical` 단독 재실행도 현재 `.pipeline/operator_request.md` live header의 `DECISION_CLASS` 값 불일치로 실패. M118 변경 범위 밖.

## 남은 리스크

- `app/frontend/`와 TypeScript 타입, dist, Playwright E2E는 handoff 금지 범위라 수정/실행하지 않음. API에는 `injected_count`가 노출되지만 UI 표시는 후속 Axis로 남음.
- 전체 unittest discover는 현재 sandbox/socket 및 기존 live-state 문서/파이프라인 조건 때문에 clean하지 않다. M118 관련 지정 검증은 통과했다.
- commit, push, branch, PR 생성은 수행하지 않음.
