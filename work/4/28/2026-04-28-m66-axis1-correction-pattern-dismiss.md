# 2026-04-28 M66 Axis 1 Correction Pattern Dismiss

## 변경 파일
- `core/contracts.py`
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m66-axis1-correction-pattern-dismiss.md`

## 사용 skill
- `security-gate`: pattern dismiss가 correction 상태를 `stopped`로 바꾸는 write-capable 동작이라 기존 lifecycle guard와 local-only 저장소 경계를 확인했습니다.
- `e2e-smoke-triage`: UI 버튼과 `data-testid`가 추가되지만 dist 재빌드와 E2E는 handoff상 Axis 2 대상임을 분리했습니다.
- `doc-sync`: M66 Axis 1 구현 범위를 `docs/MILESTONES.md`에 좁게 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M64/M65에서 반복 correction pattern 승인 경로가 JSON/SQLite 양쪽에 추가되었습니다.
- 이번 slice는 반복 pattern을 승인하지 않고 명시적으로 무시할 수 있도록 `RECORDED -> STOPPED` 전이와 fingerprint 단위 dismiss 경로를 추가하는 범위였습니다.

## 핵심 변경
- `CORRECTION_STATUS_TRANSITIONS[RECORDED]`에 `STOPPED`를 추가하고 기존 나머지 전이는 변경하지 않았습니다.
- JSON `CorrectionStore`와 `SQLiteCorrectionStore`에 `dismiss_by_fingerprint()`를 추가해 기존 `stop_correction()` 가드를 재사용합니다.
- `POST /api/corrections/dismiss-pattern` handler와 route를 추가했습니다.
- frontend client에 `dismissCorrectionPattern()`을 추가하고 `PreferencePanel.tsx` 반복 교정 line 옆에 `correction-dismiss-pattern` 무시 버튼을 연결했습니다.
- JSON/SQLite 단위 테스트에 fingerprint batch dismiss 검증을 추가했습니다.
- `app/static/dist/`와 E2E 파일은 변경하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile core/contracts.py storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py`
- 통과: `python3 -m unittest -v tests.test_correction_store tests.test_sqlite_store` (62 tests)
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- core/contracts.py storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_correction_store.py tests/test_sqlite_store.py docs/MILESTONES.md`

## 남은 리스크
- dist 재빌드와 Playwright E2E는 handoff 경계상 Axis 2 대상이라 실행하거나 수정하지 않았습니다.
- 전체 unittest, 전체 Playwright, 장기 soak는 실행하지 않았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
