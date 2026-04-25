# 2026-04-26 review queue context turns

## 변경 파일
- `app/serializers.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/ReviewQueuePanel.tsx`
- `tests/test_serializers.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/26/2026-04-26-review-queue-context-turns.md`

## 사용 skill
- `doc-sync`: review queue UI/API와 신규 smoke 시나리오가 기존 문서 parity 테스트를 깨지 않는지 확인했습니다.
- `finalize-lite`: 변경 파일, 검증 통과/실패, 미실행 범위, closeout 필요 여부를 점검했습니다.
- `work-log-closeout`: 실제 변경과 검증 결과를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- review queue 후보가 statement와 quality/snippet 정보만 보여 주어, 운영자가 해당 후보가 어떤 대화 흐름에서 나온 것인지 판단하기 어려웠습니다.
- `source_message_id` 기준 직전 대화 turn을 함께 직렬화하고 React review queue panel에 표시해 승인/거절 판단 맥락을 보강해야 했습니다.

## 핵심 변경
- `_build_review_queue_items`에서 후보 source message 직전 최대 3개 turn을 `context_turns`로 직렬화했습니다.
- context turn은 `role`, 최대 500자 `text`, 선택적 `message_id`만 포함하며, global review item은 빈 `context_turns`를 갖게 했습니다.
- `ReviewQueueItem` TypeScript interface에 `context_turns`를 추가했습니다.
- `ReviewQueuePanel`에 `대화 맥락` 섹션을 추가해 context가 있을 때만 role badge와 turn text를 표시합니다.
- serializer unit test와 기존 exact web_app expected payload에 additive field를 반영했습니다.
- 기존 E2E를 수정하지 않고, context payload와 React panel 렌더링을 확인하는 신규 review queue smoke 시나리오를 추가했습니다.

## 검증
- `python3 -m py_compile app/serializers.py`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_serializers`
  - 통과.
  - `Ran 3 tests in 0.004s`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support`
  - 통과.
  - `Ran 1 test in 0.028s`
- `cd app/frontend && npx tsc --noEmit`
  - 통과, 출력 없음.
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.029s`
- `git diff --check -- app/serializers.py app/frontend/src/api/client.ts app/frontend/src/components/ReviewQueuePanel.tsx e2e/tests/web-smoke.spec.mjs tests/test_serializers.py tests/test_web_app.py`
  - 통과, 출력 없음.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue" --reporter=line`
  - 실패.
  - Playwright `config.webServer`의 `python3 -m app.web --host 127.0.0.1 --port 8879` 시작 단계에서 현재 sandbox가 socket 생성을 막아 `PermissionError: [Errno 1] Operation not permitted`가 발생했습니다.

## 남은 리스크
- 신규 review queue context E2E와 기존 review queue browser flow는 현재 sandbox의 socket 제한 때문에 실제 브라우저 실행으로 확인하지 못했습니다.
- 전체 `make e2e-test`는 이번 handoff의 narrow 검증 범위를 넘고, 같은 socket 제한이 예상되어 실행하지 않았습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 기존 미추적 `work/4/25/2026-04-25-m31-bundle-publish-closeout.md` 등은 이번 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
