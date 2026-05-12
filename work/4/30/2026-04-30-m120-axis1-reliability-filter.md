# 2026-04-30 M120 Axis 1 injection correction reliability filter

## 변경 파일

- `storage/preference_utils.py`
- `tests/test_preference_handler.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/30/2026-04-30-m120-axis1-reliability-filter.md`

## 사용 skill

- `doc-sync`: M120 신뢰도 projection 변경을 제품/아키텍처/수용 기준/마일스톤/백로그 문서에 동기화했다.
- `finalize-lite`: 구현 범위, 실행 검증, 미실행 검증, closeout 필요 여부를 점검했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유

- M119에서 노출한 `injection_correction_rate`가 감사용 수치에 머물러 있어, 반복적으로 주입된 뒤 교정되는 선호가 계속 `is_highly_reliable=True`로 남을 수 있었다.
- 이번 handoff는 `injected_count >= 3`이고 `injection_correction_rate > 0.25`인 선호를 명시적 신뢰도 값보다 우선해 신뢰도 낮음으로 강등하는 Axis 1 구현을 요구했다.

## 핵심 변경

- `storage.preference_utils`에 `INJECTION_CORRECTION_THRESHOLD = 0.25`, `INJECTION_MINIMUM_COUNT = 3` 상수와 주입-교정률 강등 helper를 추가했다.
- `enrich_preference_reliability()`와 `is_highly_reliable_preference()`가 주입 3회 이상 및 주입-교정률 25% 초과 조건을 먼저 평가해 `is_highly_reliable=False`를 반환하도록 했다.
- 조건 미충족 시에는 기존 명시적 `is_highly_reliable` 값 우선 규칙과 고품질 + 적용 3회 이상 + 교정률 15% 미만 규칙을 유지했다.
- `tests/test_preference_handler.py`에 명시적 true 강등, 주입 횟수 미달, 비율 미달, 기존 신뢰도 회귀 케이스를 추가했다.
- M120 동작을 `PRODUCT_SPEC`, `ARCHITECTURE`, `ACCEPTANCE_CRITERIA`, `MILESTONES`, `TASK_BACKLOG`에 반영했다.
- handoff 금지 범위인 `get_global_audit_summary()`, `_get_active_preferences()`, `_preference_context_terms()`, UI/frontend는 변경하지 않았다.

## 검증

- `python3 -m py_compile storage/preference_utils.py` — PASS
- `python3 -m unittest -v tests.test_preference_handler` — PASS, 25 tests
- `python3 -m unittest -v tests.test_preference_store` — PASS, 34 tests
- `git diff --check -- storage/preference_utils.py tests/test_preference_handler.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — PASS

## 남은 리스크

- 브라우저/UI 변경이 없어 Playwright 및 dist rebuild는 실행하지 않았다.
- 전체 unittest는 실행하지 않았고, handoff에서 지정한 preference helper/handler/store 중심 검증만 수행했다.
- commit, push, branch/PR 생성은 implement lane 금지 조건에 따라 수행하지 않았다.
