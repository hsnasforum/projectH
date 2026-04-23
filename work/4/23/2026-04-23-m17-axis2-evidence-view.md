# 2026-04-23 M17 Axis 2 detailed evidence view

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m17-axis2-evidence-view.md`

## 사용 skill
- `doc-sync`: 구현된 M17 Axis 2 범위만 `docs/MILESTONES.md`에 동기화했습니다.
- `e2e-smoke-triage`: handoff가 지정한 `quality-info` 그룹만 좁게 재검증했습니다.
- `finalize-lite`: 지정 검증과 diff whitespace 검사를 확인하고 commit/PR/next-slice 없이 종료했습니다.
- `work-log-closeout`: 구현 결과와 검증 내역을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 54 기준 review queue 사용자가 후보 문장만 보지 않고, 해당 후보가 어떤 원문 응답에서 어떤 교정본으로 생겼는지 최소 근거를 펼쳐 볼 수 있어야 했습니다.
- 이번 범위는 새 route나 저장소 변경 없이 기존 correction 기록에서 짧은 evidence snippet만 review queue item에 노출하는 것입니다.

## 핵심 변경
- `app/serializers.py`의 `_build_review_queue_items`가 각 후보의 correction 목록에서 `original_text`와 `corrected_text`가 모두 있는 첫 기록을 찾아 `original_snippet`, `corrected_snippet`을 추가합니다.
- 두 snippet은 각각 최대 400자로 제한되며, 근거 correction이 없으면 `null`로 유지됩니다.
- `ReviewQueueItem` TypeScript 타입에 `original_snippet` / `corrected_snippet` nullable field를 추가했습니다.
- `ReviewQueuePanel`에 `상세 보기` / `접기` toggle을 추가하고, 두 snippet이 모두 있을 때만 원문과 교정 텍스트를 표시합니다. rich diff line coloring은 추가하지 않았습니다.
- `quality-info` Playwright 그룹에 review queue item의 snippet key 존재와 400자 제한을 확인하는 API-level smoke를 추가했습니다.
- `docs/MILESTONES.md`에 M17 Axis 2 shipped infrastructure를 추가했습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과: 출력 없음
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "quality-info" --reporter=line`
  - 통과: `4 passed (1.1m)`
  - 참고: Node warning `The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.`이 출력됐지만 테스트는 통과했습니다.
- `git diff --check -- app/serializers.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx docs/MILESTONES.md e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음

## 남은 리스크
- UI smoke는 이번 handoff 범위대로 API-level snippet 계약까지만 추가했습니다. `ReviewQueuePanel`의 펼침/접힘 상호작용은 타입 검사와 기존 review queue 패널 smoke의 컴파일/렌더 경로에 의존합니다.
- `app/static/dist`는 handoff boundary에 따라 빌드하지 않았고 변경하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m17-axis2-prioritization.md`는 이번 round에서 건드리지 않았습니다.
