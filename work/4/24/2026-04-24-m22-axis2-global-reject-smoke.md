# 2026-04-24 M22 Axis 2 global reject permanence smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m22-axis2-global-reject-smoke.md`

## 사용 skill
- `onboard-lite`: implement handoff, 기존 global recurrence 스펙 위치, helper 재사용 가능 여부, acceptance 검증 엔트리를 먼저 좁게 확인했습니다.
- `finalize-lite`: 변경 후 handoff acceptance 두 항목만 실행하고 `/work` closeout을 실제 결과 기준으로 정리했습니다.

## 변경 이유
- advisory seq 93과 implement handoff seq 95는 M22 Axis 2를 "전역 거절된 global candidate가 이후 세션 review queue에 다시 나타나지 않음"에 대한 Playwright browser/API-level 검증 추가로 정의했습니다.
- M21 Axis 2에서 `record_reviewed_candidate_preference(status=REJECTED)` 경로는 구현됐지만, `_build_review_queue_items` 수준에서 그 전역 거절이 세션을 넘어 영구적으로 반영되는지에 대한 브라우저 스모크가 비어 있었습니다.
- 이번 라운드는 backend 동작 변경이 아니라 현재 shipped global reject 계약의 회귀 방지 검증을 추가하는 bounded E2E slice입니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs`
  - 기존 `quality-info global candidate appears in review queue after cross-session recurrence` 테스트 바로 뒤에 `global reject permanently silences candidate in subsequent sessions` 시나리오를 추가했습니다.
  - `prepareSession`, `createQualityReviewQueueItem`, `fetchSessionPayload` 기존 helper를 그대로 재사용해 4개 세션 흐름을 검증합니다.
  - 1, 2번 세션에서 동일한 `recurringText`로 cross-session recurrence를 만들고, 3번 세션에서 생성된 global candidate를 `message_id="global"` + `review_action="reject"`로 API 거절한 뒤, 4번 세션에서 같은 candidate id가 `review_queue_items`에 재등장하지 않는지 확인합니다.
  - handoff 지시대로 global candidate가 아직 materialize되지 않은 경우에는 `console.log("global-reject-perm: no global candidate found - skipping rejection step")` 후 조용히 return하는 soft-skip 가드를 유지했습니다.
- `docs/MILESTONES.md`
  - M22 shipped block을 `Axes 1-2`로 갱신하고, Axis 2 (seq 95) global reject permanence smoke 항목을 추가했습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "global reject permanently" --reporter=line`
  - 통과: `1 passed (15.2s)`
  - 이번 실행에서는 soft-skip 로그가 아니라 실제 시나리오 통과가 발생했습니다.

## 남은 리스크
- handoff 경계에 따라 `make e2e-test` 전체 스위트는 실행하지 않았습니다. 전체 브라우저 release gate는 M22 Axis 3 범위입니다.
- 이번 라운드는 E2E + milestone doc sync만 다뤘고, `app/handlers/aggregate.py`, `app/serializers.py` 등 backend 구현 파일은 변경하지 않았습니다.
- 작업 시작 시점에 이미 존재하던 unrelated dirty/untracked 상태(`pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `watcher_prompt_assembly.py`, 일부 `report/gemini/*`, `work/4/23/*`)는 건드리지 않았습니다.
