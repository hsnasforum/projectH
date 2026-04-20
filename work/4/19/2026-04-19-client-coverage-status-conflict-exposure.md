# 2026-04-19 client CoverageStatus CONFLICT 노출

## 변경 파일
- app/static/contracts.js
- app/static/app.js
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- release-check: browser-visible claim coverage 변경에 맞춰 required Playwright isolated rerun과 diff check만 정직하게 분리해 마무리 점검했습니다.
- work-log-closeout: `/work` 표준 섹션 순서와 실제 실행 결과를 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- seq 376에서 `summarizeClaimCoverageCounts()`와 `formatClaimCoverageCountSummary()`는 이미 `conflict`를 처리하도록 닫혀 있었지만, `app/static/contracts.js::CoverageStatus`가 여전히 `STRONG / WEAK / MISSING`만 노출해 client 쪽 `C.CoverageStatus.CONFLICT` 분기가 실질적인 dead branch였습니다.
- seq 377은 `renderFactStrengthBar` 안의 raw `"conflict"` fallback으로 in-answer badge parity를 임시로 닫았지만, live-session answer `.meta`의 `formatClaimCoverageSummary(message.claim_coverage)` 경로는 여전히 `정보 상충 N`을 빠뜨리고 있었습니다.
- 이번 라운드는 handoff 범위대로 client contract에 `CONFLICT`를 노출하고, bar fallback을 걷어내며, live-session summary 경로가 실제로 `정보 상충 N`을 렌더링하는지 Playwright로 고정하는 데 목적이 있었습니다.

## 핵심 변경
- `app/static/contracts.js::CoverageStatus`가 이제 `STRONG / CONFLICT / WEAK / MISSING` 순서로 `CONFLICT: "conflict"`를 노출합니다.
- `app/static/app.js::renderFactStrengthBar` 안의 raw `"conflict"` items-reduce fallback을 제거했습니다. bar는 이제 `summarizeClaimCoverageCounts()`가 돌려주는 count만 사용합니다.
- `summarizeClaimCoverageCounts`, `formatClaimCoverageCountSummary`, `formatClaimCoverageSummary`의 body는 이번 라운드에서 의도적으로 건드리지 않았습니다. `app/serializers.py`와 `storage/web_search_store.py`도 untouched로 유지했고, seq 376/seq 377에서 닫힌 상태를 그대로 사용합니다.
- `e2e/tests/web-smoke.spec.mjs`에 `live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다` 시나리오를 추가해 transcript `.meta`가 `교차 확인 · 정보 상충 · 단일 출처 · 미확인` 순서로 렌더링되는 경로를 고정했습니다.
- 기존 seq 377 시나리오 `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다`는 그대로 두었고, fallback 제거 뒤에도 통과했습니다.
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 이번 라운드에서 바꾸지 않았습니다. browser-side `CoverageStatus` literal set을 여전히 3개로 적는 즉시 수정이 필요한 문장은 바로 보이지 않았습니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다" --reporter=line`
  - 결과: `1 passed (5.3s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다" --reporter=line`
  - 결과: `1 passed (4.5s)`
- `git diff --check -- app/static/contracts.js app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과

## 남은 리스크
- `core/agent_loop.py`의 CONFLICT-specific focus_slot wording은 이번 라운드에서도 그대로이며 별도 future round 후보입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family(`LocalOnlyHTTPServer` bind `PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` 누락)는 이번 슬라이스와 무관하며 여전히 범위 밖입니다.
- `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, docs에는 이번 라운드와 무관한 선행 dirty hunk가 이미 존재했습니다. 이번 작업은 handoff 범위만 확장했고, unrelated hunk는 건드리지 않았습니다.
