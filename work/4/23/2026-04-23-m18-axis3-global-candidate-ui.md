# 2026-04-23 M18 Axis 3 global candidate UI

## 변경 파일
- `app/serializers.py`
- `app/handlers/aggregate.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m18-axis3-global-candidate-ui.md`

## 사용 skill
- `security-gate`: global candidate accept가 session message 없이 `PreferenceStore`에 기록되는 write-capable 경로라서 로컬 persistence, 감사 로그, 승인 경계를 확인했습니다.
- `doc-sync`: M18 Axis 3 shipped infrastructure와 milestone closure를 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `e2e-smoke-triage`: `quality-info` smoke 그룹에 API-level `is_global` field presence 검증을 추가하고 해당 그룹만 재실행했습니다.
- `finalize-lite`: 지정된 py_compile, tsc, Playwright group, diff whitespace 검증 결과만 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 66 / advisory seq 65 기준 cross-session recurring correction pattern을 review queue에서 `범용` 후보로 볼 수 있어야 했습니다.
- global 후보는 특정 session-local message가 없으므로 `source_message_id="global"` path에서 직접 preference candidate를 기록해야 했습니다.

## 핵심 변경
- `_build_review_queue_items`가 session-local 후보에는 `is_global: False`를 넣고, `correction_store.find_recurring_patterns()` 결과 중 아직 `PreferenceStore`에 없는 fingerprint를 `global_candidate` item으로 추가합니다.
- global 후보 생성은 try/except로 감싸 session-local review queue 렌더를 막지 않도록 했습니다.
- `submit_candidate_review`가 `message_id == "global"`인 경우 session message lookup과 `record_candidate_review_for_message`를 건너뛰고, accept일 때 `record_reviewed_candidate_preference()`를 직접 호출한 뒤 `global_candidate_review_recorded` task log를 남깁니다.
- `ReviewQueueItem` 타입에 `is_global`을 추가하고, `ReviewQueuePanel`은 global item에 `범용` badge를 표시합니다.
- `quality-info` smoke에 cross-session recurrence 후 review queue item의 `is_global` key presence를 확인하는 API-level scenario를 추가했습니다.
- `docs/MILESTONES.md`에 M18 Axis 3와 Milestone 18 closure를 기록했습니다.

## 검증
- `python3 -m py_compile app/serializers.py app/handlers/aggregate.py`
  - 통과: 출력 없음
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "quality-info" --reporter=line`
  - 통과: `5 passed (2.4m)`
  - 참고: Node warning `The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.`이 출력됐지만 테스트는 통과했습니다.
- `git diff --check -- app/serializers.py app/handlers/aggregate.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음

## 남은 리스크
- global candidate 노출은 best-effort입니다. correction recurrence 조회나 preference lookup 실패가 session-local review queue를 막지 않도록 무시됩니다.
- smoke의 global 후보 존재 확인은 conditional입니다. 기존 correction promotion이 같은 fingerprint를 이미 `PreferenceStore`에 후보로 기록하면 global item은 스킵될 수 있어, 테스트는 모든 review item에 `is_global` key가 존재하는지를 보장합니다.
- global reject/defer는 session message가 없어 message-level audit record를 남기지 않고 `task_logger`에만 기록합니다. handoff boundary대로 stale guard와 `record_candidate_review_for_message`는 추가하지 않았습니다.
- `storage/preference_store.py`, `storage/sqlite_store.py`, `storage/correction_store.py`는 handoff boundary에 따라 변경하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m18-axis3-review-ui-scope.md`는 이번 round에서 건드리지 않았습니다.
