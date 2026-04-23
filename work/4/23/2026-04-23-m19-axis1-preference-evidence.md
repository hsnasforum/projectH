# 2026-04-23 M19 Axis 1 preference evidence persistence

## 변경 파일
- `storage/preference_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m19-axis1-preference-evidence.md`

## 사용 skill
- `security-gate`: preference record에 correction evidence snippet을 저장하는 local persistence 변경이라 저장 경계와 승인/감사 영향이 없는지 확인했습니다.
- `doc-sync`: M19 Axis 1 shipped infrastructure를 `docs/MILESTONES.md`에 좁게 반영했습니다.
- `finalize-lite`: handoff가 지정한 py_compile, unittest, tsc, diff whitespace 검증만 실행했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 69 / advisory seq 68 기준 review queue에서 보던 원문/교정 evidence가 preference로 승격된 뒤에도 사라지지 않아야 했습니다.
- 이번 범위는 preference record에 400자 snippet을 보존하고, `PreferencePanel`에서 read-only 상세 보기로 보여 주는 것입니다.

## 핵심 변경
- JSON `PreferenceStore.promote_from_corrections()`와 `_refresh_evidence()`가 source correction에서 `original_snippet` / `corrected_snippet`을 추출해 preference record에 저장합니다.
- JSON/SQLite `record_reviewed_candidate_preference()`가 `original_snippet` / `corrected_snippet` 인자를 받고, 새 record 생성 및 기존 record 갱신 시 값이 있을 때만 저장합니다.
- `submit_candidate_review`의 session-local accept path와 global accept path가 correction에서 400자 snippet을 추출해 preference 기록에 넘깁니다.
- `PreferenceRecord` 타입에 snippet 필드를 추가했고, `PreferencePanel`은 두 snippet이 모두 있을 때 `상세 보기` / `접기` 토글과 원문/교정 비교 블록을 표시합니다.
- JSON/SQLite preference store 단위 테스트에 snippet persistence 검증 3개를 추가했습니다.
- `docs/MILESTONES.md`에 Milestone 19 Axis 1 정의와 shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_store tests.test_sqlite_store -v`
  - 통과: `Ran 43 tests in 0.149s`, `OK`
  - 새 snippet 테스트 3개 포함
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- storage/preference_store.py storage/sqlite_store.py app/handlers/aggregate.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 slice는 `PreferencePanel` UI toggle의 TypeScript compile 경로까지만 검증했습니다. handoff boundary대로 Playwright와 Vite build, `app/static/dist` 갱신은 실행하지 않았습니다.
- snippet은 read-only display evidence이며 fingerprint, lifecycle status, preference activation policy를 바꾸지 않습니다.
- 기존 preference record에는 snippet 필드가 없을 수 있습니다. 새 승격/갱신 경로에서 evidence가 있는 경우에만 채워집니다.
- `storage/correction_store.py`는 handoff boundary에 따라 변경하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m19-definition.md`는 이번 round에서 건드리지 않았습니다.
