# 2026-04-19 claim-coverage panel hint conflict explanation

## 변경 파일
- app/static/app.js
- docs/ACCEPTANCE_CRITERIA.md
- e2e/tests/web-smoke.spec.mjs

## 사용 skill
- release-check: 단일 renderer 문구 + 단일 docs bullet + 단일 Playwright 시나리오 추가라는 범위에 맞춰 isolated rerun과 diff check만 정직하게 분리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서와 실제 실행 결과를 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- seq 376/377/378과 seq 381 이후 CONFLICT는 history-card summary, in-answer fact-strength bar, live-session summary, client contract enum, 문서 문장에는 보이지만, claim-coverage panel 하단 hint는 여전히 `[교차 확인] / [단일 출처] / [미확인]` 3-tag 설명만 남아 있어 panel 안의 `정보 상충` 라벨을 같은 화면에서 해석할 수 없었습니다.
- 이번 라운드는 handoff 범위대로 panel hint 문구와 그에 대응하는 `docs/ACCEPTANCE_CRITERIA.md:1375` 한 문장만 최소 수정해, claim-coverage panel의 visible explanation gap을 닫는 것이 목적이었습니다.

## 핵심 변경
- `app/static/app.js:2511-2512`의 claim-coverage panel hint는 이제 `[교차 확인] / [정보 상충] / [단일 출처] / [미확인]` 순서로 4-tag를 나열하고, `정보 상충` 설명을 `출처들이 서로 어긋나 추가 확인이 필요한 항목`으로 고정합니다. `progressText ? ... : ...` 두 branch 모두 동일하게 바꿨고, `${progressText} ` prefix와 주변 helper 호출은 그대로 유지했습니다.
- `docs/ACCEPTANCE_CRITERIA.md:1375`의 panel-rendering-contract bullet을 3-tag에서 4-tag(`[교차 확인]`, `[정보 상충]`, `[단일 출처]`, `[미확인]`)로만 업데이트했습니다. `docs/ACCEPTANCE_CRITERIA.md:35/48/49`를 포함한 다른 문장은 이번 라운드에서 다시 건드리지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`에 `claim-coverage panel hint는 conflict 상태 설명을 4-tag 순서로 렌더링합니다` 시나리오를 추가했습니다. non-empty `claim_coverage_progress_summary`와 CONFLICT slot이 있는 live-session renderer 호출에서 hint가 4 tag를 올바른 순서로 포함하고, `출처들이 서로 어긋나 추가 확인이 필요한 항목` 문구를 실제로 렌더링하는지 고정합니다.
- 기존 panel-hint assertion widening은 필요하지 않았습니다. 기존 `claim-coverage panel은 status tag와 행동 힌트를 올바르게 렌더링합니다` 시나리오는 `#claim-coverage-hint`에 대해 `.toContainText(...)`로 3개 기존 tag substring만 확인하고 있어서, 새 4-tag hint에서도 그대로 truthful하게 통과 가능한 상태입니다.
- `core/agent_loop.py`의 response-body section headers(`[교차 확인]` / `[단일 출처]` / `[미확인]`)는 의도적으로 바꾸지 않았습니다. 따라서 `docs/ACCEPTANCE_CRITERIA.md:49`의 “dedicated `[정보 상충]` response-body header tag는 아직 없다”는 설명도 계속 truthful합니다.

## 검증
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel hint는 conflict 상태 설명을 4-tag 순서로 렌더링합니다" --reporter=line`
  - 결과: `1 passed (5.4s)`
- 기존 panel-hint assertion 추가 rerun
  - 실행하지 않음. 기존 scenario assertion을 수정하지 않았고, `.toContainText(...)` 기반 substring check라 이번 4-tag 확장 후에도 논리적으로 그대로 truthful합니다.
- `git diff --check -- app/static/app.js docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음, 통과

## 남은 리스크
- 이번 라운드는 code+docs mixed slice이며 pure docs-only round가 아닙니다. 따라서 같은 날 same-family docs-only round count는 seq 381의 1회에서 그대로 증가하지 않습니다.
- `core/agent_loop.py`의 CONFLICT-specific focus_slot wording strengthening은 이번 라운드에서도 그대로이며 별도 future round 후보입니다.
- Milestone 4의 새 sub-axis(`source role labeling/weighting`, `strong vs weak vs unresolved separation beyond CONFLICT`)는 이번 라운드 범위 밖이며 separate candidate로 남습니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family(`LocalOnlyHTTPServer` bind `PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` 누락)는 이번 슬라이스와 무관하며 여전히 범위 밖입니다.
- `app/static/app.js`, `docs/ACCEPTANCE_CRITERIA.md`, `e2e/tests/web-smoke.spec.mjs`에는 이번 라운드 이전의 선행 dirty hunk가 이미 있었고, 이번 작업은 handoff가 지정한 panel hint explanation + line 1375 sync 범위만 확장했습니다.
