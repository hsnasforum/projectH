# 2026-04-28 M67 Axis 1 Correction List Recent View

## 변경 파일
- `app/handlers/aggregate.py`
- `app/web.py`
- `tests/test_correction_summary.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m67-axis1-correction-list-recent-view.md`

## 사용 skill
- `security-gate`: correction record 텍스트를 노출하는 새 GET 경로가 read-only/local-only 경계 안에 머무는지 확인했습니다.
- `e2e-smoke-triage`: browser-visible compact 목록이 추가되지만 dist 재빌드와 E2E는 handoff상 Axis 2 대상임을 분리했습니다.
- `doc-sync`: M67 Axis 1 구현 범위를 `docs/MILESTONES.md`에 좁게 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- correction summary와 pattern 승인/무시 경로는 존재하지만, 최근 correction record 자체를 UI에서 훑어볼 compact 목록은 없었습니다.
- 이번 slice는 기존 JSON/SQLite `list_recent()`을 재사용해 read-only recent correction list를 backend와 frontend에 연결하는 범위였습니다.

## 핵심 변경
- `AggregateHandlerMixin.get_correction_list()`를 추가해 `correction_store.list_recent(limit=5)` 결과를 반환합니다.
- `GET /api/corrections/list` route를 추가했습니다.
- `tests/test_correction_summary.py`에 empty store와 recent record 반환 테스트를 추가했습니다.
- frontend client에 `CorrectionListResponse`/`CorrectionListItem` 타입과 `fetchCorrectionList()`를 추가했습니다.
- `PreferencePanel.tsx`가 correction summary와 함께 recent correction list를 불러오고 최근 3개를 compact 목록으로 표시합니다.
- `docs/MILESTONES.md`에 M67 Axis 1 항목을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile app/handlers/aggregate.py app/web.py`
- 통과: `python3 -m unittest -v tests.test_correction_summary` (4 tests)
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- app/handlers/aggregate.py app/web.py tests/test_correction_summary.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`

## 남은 리스크
- `app/static/dist/` 재빌드와 Playwright E2E는 handoff 경계상 Axis 2 대상이라 실행하거나 수정하지 않았습니다.
- storage 파일은 `list_recent()`가 JSON/SQLite 양쪽에 이미 있어 변경하지 않았습니다.
- 전체 unittest, 전체 Playwright, 장기 soak는 실행하지 않았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
