# 2026-04-23 M17 Axis 1 smoke fix

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/23/2026-04-23-m17-axis1-smoke-fix.md`

## 사용 skill
- `e2e-smoke-triage`: 실패한 `review queue edit` smoke의 검증 대상이 preference 생성이 아니라 accept 요청 payload여야 함을 좁혔습니다.
- `finalize-lite`: focused Playwright와 whitespace 검증 결과만 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증을 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 51 기준 `review queue edit` smoke가 `PreferenceStore` 생성 여부를 검증해 테스트 환경의 recurrence 조건에 의존하고 있었습니다.
- mock correction 단일 세션에서는 `candidate_recurrence_key`가 없을 수 있어 preference가 생성되지 않지만, M17 Axis 1 UI 계약은 edited statement가 `/api/candidate-review` accept 요청에 실리는 것입니다.
- 따라서 preference lookup 대신 browser가 보낸 candidate-review request body를 검증하도록 바꿨습니다.

## 핵심 변경
- 테스트 제목을 `review queue edit statement sends edited text in accept request`로 수정했습니다.
- 기존 `/api/preferences` lookup과 `description` 검색 assertion을 제거했습니다.
- `reviewResponse.request().postData()`를 JSON으로 파싱해 `statement === editedStatement`와 `review_action === "accept"`를 검증합니다.
- 기존 setup, UI interaction, accept 후 review queue removal 검증은 그대로 유지했습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue edit" --reporter=line`
  - 통과: `1 passed (22.7s)`
  - 참고: Node warning `The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.`이 출력됐지만 테스트는 통과했습니다.

## 남은 리스크
- 이번 smoke는 edited statement가 accept request에 포함되는 계약까지만 검증합니다. Preference 생성은 recurrence 조건에 따라 달라질 수 있어 이 테스트의 직접 검증 대상에서 제외했습니다.
- production code, frontend source, docs, static dist는 handoff boundary대로 변경하지 않았습니다.
