# history-card header-badge progress-summary smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — generic header-badge 시나리오에 `claim_coverage_progress_summary` fixture 및 assertion 추가

## 사용 skill
- 없음

## 변경 이유
- `README.md:138`과 `docs/ACCEPTANCE_CRITERIA.md:1366`는 generic header-badge Playwright 시나리오가 non-empty `claim_coverage_progress_summary` 표시를 검증한다고 기술하지만, 실제 시나리오에는 해당 fixture와 assertion이 없었음
- progress summary 가시성 검증은 별도의 entity-card reload 시나리오에만 존재하여, docs가 약속한 smoke coverage와 실제 테스트 사이에 drift가 있었음
- 이 슬라이스는 generic header-badge 시나리오를 docs 계약 범위까지 맞춰 same-family smoke-coverage drift를 닫음

## 핵심 변경
1. **fixture** (`e2e/tests/web-smoke.spec.mjs:1112`): Card 1 (entity_card, `대통령 출생일`) fixture에 `claim_coverage_progress_summary: "출생일: 단일 출처 → 교차 확인으로 보강되었습니다."` 추가
2. **assertion** (`e2e/tests/web-smoke.spec.mjs:1166–1168`): Card 1의 `.meta` 요소에서 progress summary 텍스트 `toContainText` 검증 추가

## 검증

이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → 1 passed (6.1s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader `tests.test_web_app` 전체 unit suite
- `history-card entity-card` 13-scenario Playwright family
- full Playwright suite / `make e2e-test`

docs truth-sync 불필요:
- `README.md:138`과 `docs/ACCEPTANCE_CRITERIA.md:1366`는 이미 이 coverage를 기술하고 있었고, 테스트가 docs를 따라잡은 것이므로 docs 수정 없음
- `docs/NEXT_STEPS.md`에는 progress summary 관련 내용 없음

## 남은 리스크
- Card 2–4에는 `claim_coverage_progress_summary`를 넣지 않았으므로, 비어있는 경우의 non-render는 기존 entity-card reload 시나리오 계열에서만 간접 확인됨
- 이번 라운드는 isolated 시나리오 1건만 재실행했으므로, broader browser family drift는 독립적으로 재확인하지 않음
