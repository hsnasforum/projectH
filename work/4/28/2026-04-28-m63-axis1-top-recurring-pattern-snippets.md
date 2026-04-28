# 2026-04-28 M63 Axis 1 Top Recurring Pattern Snippets

## 변경 파일
- `app/handlers/aggregate.py`
- `tests/test_correction_summary.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m63-axis1-top-recurring-pattern-snippets.md`

## 사용 skill
- `doc-sync`: M63 Axis 1 진행 사실을 `docs/MILESTONES.md`에 반영했습니다.
- `e2e-smoke-triage`: browser-visible compact line이 확장되지만 이번 handoff가 dist 재빌드와 E2E를 Axis 2로 분리하므로 단위/타입 검증만 수행했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M61-M62에서 correction summary endpoint와 compact frontend 표시가 추가되었지만, `top_recurring_fingerprints` 항목은 fingerprint와 recurrence count만 포함했습니다.
- 이미 존재하는 `_first_correction_snippets()` 헬퍼와 recurring pattern의 `corrections` 목록을 재사용해 반복 교정의 원문/수정문 snippet을 summary payload와 compact UI에 노출했습니다.

## 핵심 변경
- `AggregateHandlerMixin.get_correction_summary()`가 상위 recurring pattern 5개에 `original_snippet`과 `corrected_snippet`을 선택적으로 포함하도록 확장했습니다.
- `tests/test_correction_summary.py`의 recurring pattern assertion을 snippet 필드까지 확인하도록 갱신했습니다.
- `CorrectionSummary.top_recurring_fingerprints` 타입에 `original_snippet`, `corrected_snippet` optional 필드를 추가했습니다.
- `PreferencePanel.tsx`에서 첫 번째 recurring pattern의 `original_snippet`을 `반복 교정:` compact line으로 표시합니다.
- `docs/MILESTONES.md`에 M63 Correction Pattern Visibility / Axis 1 항목을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile app/handlers/aggregate.py tests/test_correction_summary.py`
- 통과: `python3 -m unittest -v tests.test_correction_summary` (2 tests OK)
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- app/handlers/aggregate.py tests/test_correction_summary.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`

## 남은 리스크
- handoff 경계에 따라 `app/static/dist/` 재빌드와 E2E는 실행하지 않았습니다. 해당 검증은 Axis 2 대상입니다.
- 이번 frontend 표시 범위는 top 1 pattern의 original snippet compact line으로 제한했습니다.
- backend helper `_first_correction_snippets()`는 기존 구현을 그대로 재사용했고 수정하지 않았습니다.
