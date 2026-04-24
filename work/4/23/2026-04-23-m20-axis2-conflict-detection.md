# 2026-04-23 M20 Axis 2 conflict detection

## 변경 파일
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m20-axis2-conflict-detection.md`

## 사용 skill
- `security-gate`: preference activation warning이 기존 local preference lifecycle 경계 안에서 동작하고, 저장 필드나 approval/write 경로를 넓히지 않는지 확인했습니다.
- `doc-sync`: M20 Axis 2 shipped behavior를 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `finalize-lite`: handoff acceptance check만 실행하고, 미실행 Playwright 검증은 통과로 적지 않았습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- advisory seq 80 / implement handoff seq 81 기준 active durable preference 간 설명 중복을 API와 sidebar UI에서 드러내기 위해서입니다.
- 충돌 정보는 저장 필드가 아니라 현재 preference 목록 조회 시점에 계산되어야 했습니다.

## 핵심 변경
- `app/handlers/preferences.py`에 `_jaccard_word_similarity()` helper를 추가했습니다.
- `list_preferences_payload()`가 ACTIVE preference 설명끼리 Jaccard word-token similarity > 0.7이면 각 preference에 `conflict_info.has_conflict`와 `conflicting_preference_ids`를 붙입니다.
- `PreferenceRecord` TypeScript 타입에 optional `conflict_info`를 추가했습니다.
- `PreferencePanel.tsx`가 conflict preference에 `⚠ 충돌` badge를 표시하고, activate action 전에 `window.confirm()`을 실행하도록 변경했습니다.
- `tests/test_preference_handler.py`에 no-conflict, similar-description conflict, Jaccard helper threshold test를 추가했습니다.
- `docs/MILESTONES.md`에 M20 Axis 2 shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile app/handlers/preferences.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_handler -v`
  - 통과: `Ran 5 tests in 0.001s`, `OK`
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`
  - 통과: 출력 없음
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- conflict 계산은 handoff boundary대로 ACTIVE preference끼리만 수행합니다. Candidate/paused/rejected preference 자체는 conflict 대상으로 계산하지 않습니다.
- activate 전 `window.confirm()`은 `pref.conflict_info?.has_conflict`가 있을 때만 동작합니다. 현재 계산 범위가 ACTIVE-only이므로 비활성 preference를 활성화하기 전 잠재 충돌을 선제 계산하는 UX는 별도 slice가 필요합니다.
- pairwise 비교는 O(n²)입니다. 일반적인 active preference 수가 50개 미만이라는 전제에서는 충분하지만, 100개 이상으로 늘면 별도 index/cache가 필요할 수 있습니다.
- handoff boundary에 따라 Playwright/browser interaction test는 추가하거나 실행하지 않았습니다. M20 Axis 3 smoke gate에서 다룰 수 있습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m20-axis2-conflict-scope.md`는 이번 implement round에서 건드리지 않았습니다.
