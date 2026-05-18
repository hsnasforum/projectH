# 2026-04-29 M97 Axis 1 자동 활성화 알림 UX

## 변경 파일

- `app/handlers/feedback.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/App.tsx`
- `app/frontend/src/components/Sidebar.tsx`
- `app/frontend/src/components/PreferencePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/29/2026-04-29-m97-axis1-auto-activate-notification.md`

## 사용 skill

- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 라운드 closeout 형식으로 정리하기 위해 사용했다.
- `finalize-lite`: 구현 후 검증 진실성, doc-sync 필요 여부, `/work` 준비 상태를 점검하기 위해 사용했다.
- `release-check`: UI/E2E 변경의 검증 누락과 남은 리스크를 구분하기 위해 사용했다.
- `doc-sync`: UI 동작과 E2E 시나리오 추가에 맞춰 README/spec/acceptance/milestone/backlog 문장을 최소 동기화하기 위해 사용했다.

## 변경 이유

- 반복 교정으로 내구 선호가 자동 활성화될 때 사용자가 그 변화를 즉시 알 수 있는 UI 피드백이 없었다.
- M94-M96에서 강화한 applied preferences `신뢰도 높음` 배지와 `선호에서 보기` 이동 흐름에 이어, correction-submit 자동 활성화 이벤트도 `PreferencePanel`에서 확인할 수 있게 해야 했다.

## 핵심 변경

- `submit_correction()`이 반복 교정 승격 중 `candidate -> active` 전환을 감지하고, highly reliable 기준을 만족하면 응답에 `auto_activated: true`와 `preference_id`를 포함하도록 했다.
- 자동 활성화 판정에는 기존 recurrence 기반 `seed_reliability_from_recurrence()` 기준을 재사용해, 반복 교정이 아직 저장된 적용 통계로 반영되기 전에도 응답 이벤트 판정이 같은 신뢰도 기준을 따르도록 했다.
- `postCorrection()`이 correction 응답 JSON을 반환하도록 타입을 추가하고, `App.tsx`가 auto activation 이벤트를 상태로 보관해 `Sidebar`를 거쳐 `PreferencePanel`에 전달하도록 했다.
- `PreferencePanel`은 이벤트 수신 시 active 탭을 열고 선호 목록을 다시 불러오며, `data-testid="preference-auto-activated-notice"` 알림과 `data-testid="preference-auto-activated-link"` 링크를 표시한다.
- `e2e/tests/web-smoke.spec.mjs`에 correction 응답의 `auto_activated` 이벤트가 `PreferencePanel` 알림으로 렌더링되는 preference 시나리오를 추가했다.
- UI 동작과 E2E 시나리오 변경에 맞춰 README, product spec, acceptance criteria, milestones, backlog 문장을 최소 갱신했다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `23f946ddd365722603560da317b4aab9ed8fc70dd41ae77f9a703ed4b44140d0` 일치.
- `python3 -m py_compile app/handlers/feedback.py`
  - 통과.
- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
  - 통과.
- `python3 - <<'PY' ...`
  - 통과. `_with_auto_activation_reliability_seed()`가 recurrence 3회 preference를 `applied_count: 3`, `is_highly_reliable: true`로 판정하는지 확인했다.
- `git diff --check -- app/handlers/feedback.py app/frontend/src/components/PreferencePanel.tsx app/frontend/src/App.tsx app/frontend/src/components/Sidebar.tsx app/frontend/src/api/client.ts e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 통과.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference auto activation notice" --reporter=line`
  - 실패: 테스트 실행 전 `app.web` webServer가 socket 생성에서 `PermissionError: [Errno 1] Operation not permitted`로 중단됐다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference" --reporter=line`
  - 실패: 같은 webServer socket 제한으로 테스트 본문 실행 전에 중단됐다.

## 남은 리스크

- Playwright browser smoke는 현재 sandbox의 소켓 생성 제한 때문에 실행하지 못했다. 추가한 E2E 시나리오는 파일에 반영됐지만 실제 브라우저 렌더링은 별도 실행 환경에서 확인해야 한다.
- `app/static/dist/` 재빌드는 이번 handoff 경계에 없어서 수행하지 않았다. React preview source와 E2E만 갱신됐다.
- 로컬에는 `main` 브랜치가 없어 handoff의 branch-from-main 지시를 검증하지 못했다. commit, push, branch/PR publish는 implement 역할 경계에 따라 수행하지 않았다.
