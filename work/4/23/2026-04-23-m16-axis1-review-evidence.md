# 2026-04-23 M16 Axis 1 review evidence enrichment

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m16-axis1-review-evidence.md`

## 사용 skill
- `doc-sync`: M16 Axis 1 문서 반영 범위를 `docs/MILESTONES.md`로 제한해 현재 구현 사실과 맞췄습니다.
- `finalize-lite`: 지정된 py_compile, TypeScript, focused Playwright, whitespace 검증 결과를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 이번 `/work` closeout에 기록했습니다.

## 변경 이유
- implement handoff seq 43 기준 review queue item이 accept/defer/reject 전에 correction pattern을 볼 수 있도록 compact evidence를 제공해야 했습니다.
- 기존 `review_queue_items[]`는 `quality_info`까지만 노출해 후보가 어떤 수정에서 왔는지 판단할 단서가 부족했습니다.
- 이번 slice는 read-only evidence 표시이며 preference lifecycle, storage promotion, dist asset 갱신은 범위 밖이었습니다.

## 핵심 변경
- `SerializerMixin._build_review_queue_items()`가 같은 artifact correction record에서 첫 번째 non-empty `delta_summary`를 찾아 각 review queue item에 `delta_summary`로 포함합니다.
- `ReviewQueueItem` TypeScript 타입에 optional nullable `delta_summary` shape를 추가했습니다.
- `ReviewQueuePanel.tsx`가 replacement, addition, removal 순서로 compact 한 줄 correction summary를 표시합니다.
- `web-smoke.spec.mjs`에 `quality-info` focused test를 추가해 correction 이후 review queue item에 `delta_summary` key가 존재하는지 확인합니다.
- `docs/MILESTONES.md`에 Milestone 16 Axis 1-3 planned infrastructure와 guardrails를 추가했습니다.
- handoff boundary대로 `storage/correction_store.py`, `PreferencePanel.tsx`, `app/static/dist`는 변경하지 않았습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과: 출력 없음
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "quality-info" --reporter=line`
  - 통과: `3 passed (49.2s)`
  - 참고: Node warning `The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.`이 출력됐지만 테스트는 통과했습니다.
- `git diff --check -- app/serializers.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음

## 남은 리스크
- 전체 Playwright suite와 Vite build는 handoff 범위가 아니라 실행하지 않았습니다.
- UI는 compact 한 줄 요약만 표시하며, 긴 correction pattern은 truncate됩니다. 전체 delta detail 표시나 source/effect context는 M16 후속 axis 범위입니다.
- 작업 전부터 있던 untracked `report/gemini/2026-04-23-m16-definition.md`는 이번 implement 범위 밖이라 건드리지 않았습니다.
