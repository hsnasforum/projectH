# 2026-04-28 M64 Axis 1 Pattern Confirmation

## 변경 파일
- `storage/correction_store.py`
- `tests/test_correction_store.py`
- `app/handlers/aggregate.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m64-axis1-pattern-confirmation.md`

## 사용 skill
- `security-gate`: 새 POST 경로가 local correction 상태를 갱신하는 write-capable 동작이라 same-origin 경계와 기존 상태 전이 가드 재사용 여부를 확인했습니다.
- `doc-sync`: M64 Axis 1 진행 사실을 `docs/MILESTONES.md`에 좁게 반영했습니다.
- `e2e-smoke-triage`: browser-visible 버튼이 추가되지만 dist 재빌드와 E2E는 handoff상 Axis 2 대상임을 분리했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M63에서 반복 correction pattern이 summary와 frontend compact line에 노출되었습니다.
- 이번 slice는 반복 fingerprint 단위로 기록된 correction들을 명시적 "승인" 버튼으로 `RECORDED`에서 `CONFIRMED`로 일괄 전이하는 M64 Axis 1 범위였습니다.

## 핵심 변경
- `CorrectionStore.confirm_by_fingerprint()`를 추가해 같은 `delta_fingerprint`의 correction들을 기존 `confirm_correction()` 전이 가드로 순차 승인합니다.
- `test_confirm_by_fingerprint`를 추가해 같은 fingerprint 2건이 `confirmed` 상태로 바뀌는 경로를 고정했습니다.
- `AggregateHandlerMixin.confirm_correction_pattern()`와 `POST /api/corrections/confirm-pattern` 라우트를 추가했습니다.
- frontend client에 `confirmCorrectionPattern()`을 추가하고 `PreferencePanel.tsx` 반복 교정 line 옆에 `correction-confirm-pattern` 승인 버튼을 연결했습니다.
- `docs/MILESTONES.md`에 M64 Axis 1 항목을 추가했습니다.
- `CORRECTION_STATUS_TRANSITIONS`, `app/static/dist/`, E2E 파일은 변경하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile storage/correction_store.py app/handlers/aggregate.py app/web.py`
- 통과: `python3 -m unittest -v tests.test_correction_store` (28 tests)
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- storage/correction_store.py tests/test_correction_store.py app/handlers/aggregate.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`

## 남은 리스크
- dist 재빌드와 Playwright E2E는 handoff 경계상 Axis 2 대상이라 실행하지 않았습니다.
- 이번 handoff의 수정 파일 범위에 `storage/sqlite_store.py`가 포함되지 않아 SQLite store parity는 다루지 않았습니다.
- 전체 unittest, 전체 Playwright, 장기 soak는 실행하지 않았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
