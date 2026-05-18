# 2026-04-30 M119 Axis 1 injection correction loop

## 변경 파일

- `core/contracts.py`
- `storage/session_store.py`
- `storage/sqlite/session.py`
- `storage/preference_utils.py`
- `tests/test_session_store.py`
- `tests/test_sqlite_store.py`
- `tests/test_preference_handler.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/30/2026-04-30-m119-axis1-injection-correction-loop.md`

## 사용 skill

- `security-gate`: 세션 저장소와 task-log 기반 감사 집계가 로컬 기록 경계를 유지하는지 확인했습니다.
- `doc-sync`: 새 API 응답 필드와 감사 집계 의미를 제품/아키텍처/수용 기준/마일스톤/백로그에 맞췄습니다.
- `finalize-lite`: 구현 종료 전 실제 검증, 미실행 범위, closeout 필요성을 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유

- M118까지 `injected_count`는 집계/노출됐지만, 같은 세션에서 선호가 주입된 뒤 교정이 발생한 경우를 별도 감사 신호로 볼 수 없었습니다.
- 이번 Axis 1은 boolean 신뢰도 필터를 바꾸지 않고, 후속 판단에 쓸 수 있는 `injection_correction_count` / `injection_correction_rate`만 노출하는 범위입니다.

## 핵심 변경

- `PerPreferenceStats`와 preference 응답 contract에 `injection_correction_count` / `injection_correction_rate`를 추가했습니다.
- JSON/SQLite `get_global_audit_summary()`가 세션 단위로 `preference_injected`와 교정 이벤트(`correction_submitted`, corrected text/outcome, explicit preference correction evidence)가 함께 있는 경우, 해당 세션에서 주입된 선호별로 `injection_correction_count`를 1회 누적합니다.
- `enrich_preference_reliability()`가 top-level `injection_correction_count`와 `injection_correction_rate`를 계산해 `/api/preferences` 응답에 싣고, 기존 `reliability_stats`는 `applied_count` / `corrected_count` 모양을 유지합니다.
- `is_highly_reliable_preference()`와 `_get_active_preferences()`는 수정하지 않았습니다.
- JSON store, SQLite store, preference handler 테스트에 집계와 응답 필드 검증을 추가했습니다.
- PRODUCT_SPEC / ARCHITECTURE / ACCEPTANCE_CRITERIA / MILESTONES / TASK_BACKLOG에 현재 동작과 후속 boolean 조정 미포함 사실을 반영했습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` — `a4243194e37416c1de28a5d27377cb9aedb14cc777715464d28e81d4c227a22f` 일치.
- `python3 -m py_compile storage/session_store.py storage/sqlite/session.py storage/preference_utils.py core/contracts.py` — 통과.
- `python3 -m unittest -v tests.test_session_store` — 20 tests OK.
- `python3 -m unittest -v tests.test_sqlite_store` — 47 tests OK.
- `python3 -m unittest -v tests.test_preference_handler` — 23 tests OK.
- `git diff --check -- core/contracts.py storage/session_store.py storage/sqlite/session.py storage/preference_utils.py tests/test_session_store.py tests/test_sqlite_store.py tests/test_preference_handler.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/30/2026-04-30-m119-axis1-injection-correction-loop.md` — 통과.

## 남은 리스크

- `injection_correction_count`는 handoff 지시대로 세션 단위 근사 신호입니다. 주입 이벤트와 교정 이벤트의 세션 내 시간 순서는 정밀 추적하지 않습니다.
- 전체 저장소 unittest, browser/E2E, frontend dist는 실행하지 않았습니다. 이번 변경은 backend 감사 집계/API projection/docs 범위이며 UI와 frontend는 수정하지 않았습니다.
- implement lane 규칙에 따라 commit / push / PR 생성은 하지 않았습니다.
