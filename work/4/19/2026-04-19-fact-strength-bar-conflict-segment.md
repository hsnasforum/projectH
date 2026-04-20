# 2026-04-19 fact strength bar conflict segment

## 변경 파일
- app/static/app.js
- app/static/style.css
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- release-check: 이번 라운드가 단건 UI renderer + CSS class 변경인지 확인하고, 가장 좁은 Playwright rerun과 미실행 항목을 정직하게 분리했습니다.
- work-log-closeout: `/work` closeout 형식과 실제 실행 결과를 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- seq 376에서 history-card summary는 이미 `정보 상충 N`을 보여 주지만, in-answer fact-strength bar는 여전히 `교차 확인 / 단일 출처 / 미확인` 3-badge만 렌더링해 같은 claim coverage를 두 표면이 다르게 보여 주고 있었습니다.
- 이번 라운드는 handoff 범위대로 `renderFactStrengthBar`와 `.fact-count.conflict` CSS, 그리고 새 Playwright 시나리오만 추가해 in-answer badge parity를 닫는 데 목적이 있었습니다.

## 핵심 변경
- `app/static/app.js::renderFactStrengthBar`가 이제 `counts.conflict`를 `total`에 포함하고, 모든 count가 양수일 때 `교차 확인 · 정보 상충 · 단일 출처 · 미확인` 순서의 4 badge group을 렌더링합니다.
- `app/static/app.js::renderFactStrengthBar` 안에 raw `"conflict"` status fallback을 한 번 두어, 이번 라운드 범위 밖인 `app/static/contracts.js`를 다시 열지 않아도 실제 claim_coverage payload의 `status: "conflict"`를 badge로 표면화할 수 있게 했습니다.
- `app/static/style.css`에는 `.fact-strength-bar .fact-count.conflict` 규칙 하나만 추가했습니다. 기존 `.strong` / `.weak` / `.missing` 색상 규칙은 바꾸지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`에는 `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다` 시나리오를 추가했습니다. 기존 bar 관련 assertion은 수정하지 않았습니다.
- 문서 문장은 바꾸지 않았습니다. 현재 shipped 문장 중 in-answer fact-strength bar를 `교차 확인 / 단일 출처 / 미확인` 3-badge로 명시한 문장은 바로 보이지 않았습니다.
- `formatClaimCoverageCountSummary`, `summarizeClaimCoverageCounts`, `app/serializers.py`, `storage/web_search_store.py`는 이번 라운드에서 의도적으로 건드리지 않았고, seq 376에서 닫힌 상태를 유지합니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다" --reporter=line`
  - 초기 2회 실패:
    - `response-box`가 hidden인 상태라 `#fact-strength-bar` visibility assertion이 실패
    - page runtime의 `app/static/contracts.js`가 아직 `CoverageStatus.CONFLICT`를 노출하지 않아 새 시나리오의 conflict seed가 group count 4를 만들지 못함
  - 조정 후 최종 결과: `1 passed (5.7s)`
- `git diff --check -- app/static/app.js app/static/style.css e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `app/static/contracts.js`는 이번 handoff 범위 밖이라 여전히 `CoverageStatus.CONFLICT`를 직접 노출하지 않습니다. 이번 라운드는 `renderFactStrengthBar` 안의 raw `"conflict"` fallback으로만 parity를 닫았습니다.
- `core/agent_loop.py`의 CONFLICT-specific focus_slot wording은 이번 라운드에서도 그대로이며, 별도 future round 후보입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family(`LocalOnlyHTTPServer` bind `PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` 누락)는 이번 슬라이스와 무관하며 여전히 범위 밖입니다.
