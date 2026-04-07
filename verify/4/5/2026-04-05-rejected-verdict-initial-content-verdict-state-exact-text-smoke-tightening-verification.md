## 변경 파일
- verify/4/5/2026-04-05-rejected-verdict-initial-content-verdict-state-exact-text-smoke-tightening-verification.md
- .pipeline/claude_handoff.md

## 사용 skill
- round-handoff
- e2e-smoke-triage

## 변경 이유
- latest `/work`의 truthful 여부를 current tree와 rerun 기준으로 다시 확인해야 했습니다.
- 같은 날 `/verify`가 아직 이전 cancel 라운드 기준이라, 오늘 기준 current truth와 다음 exact slice를 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`인 `work/4/5/2026-04-05-rejected-verdict-initial-content-verdict-state-exact-text-smoke-tightening.md`의 핵심 변경은 truthful합니다. `e2e/tests/web-smoke.spec.mjs:427`은 `toHaveText("최신 내용 판정은 원문 저장 승인입니다.")`로 강화되어 있고, runtime 문자열도 `app/static/app.js:1787-1788` 기준으로 deterministic합니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 깨끗했습니다.
- 다만 current workspace는 persistent `/work`보다 한 줄 앞서 있습니다. `git diff -- e2e/tests/web-smoke.spec.mjs` 기준으로 `e2e/tests/web-smoke.spec.mjs:511`이 같은 family의 추가 exact-text tightening으로 이미 바뀌어 있었고, 이 변경은 latest `/work`에 아직 기록되지 않았습니다. 아래 rerun truth는 이 current workspace 기준입니다.
- default `make e2e-test`는 이번 verification 라운드에서 두 번 모두 `http://127.0.0.1:8879 is already used`로 중단됐습니다. `ps -ef | rg '8879|app.web|playwright test|make e2e-test'` 기준으로 다른 lane가 `make e2e-test`와 `python3 -m app.web --host 127.0.0.1 --port 8879`를 이미 점유하고 있어 latest `/work`의 full-suite pass claim은 같은 명령으로 직접 재재현하지 못했습니다.
- 대신 동일 Playwright 설정을 alternate port로 옮긴 `/tmp/projectH-playwright-8880.config.mjs`로 full suite를 돌렸고, 결과는 `16 passed, 1 failed (4.8m)`였습니다. 실패는 `e2e/tests/web-smoke.spec.mjs:246`의 `response-search-preview` visible assertion이었습니다.
- 같은 failing test를 `--repeat-each=3`로 focused rerun한 결과는 `3 passed (33.1s)`였습니다. current truth는 rejected-verdict target change 문제라기보다 search-only preview visibility의 full-suite-only flake 또는 readiness race 쪽입니다.
- 다음 Claude handoff는 same-family exact-text tightening을 계속 미는 대신, `search-only` preview readiness gate stabilization 1건으로 갱신했습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `ps -ef | rg '8879|app.web|playwright test|make e2e-test'`
- `make e2e-test`
  - 두 번 모두 `Error: http://127.0.0.1:8879 is already used`
- `cd e2e && npx playwright test --config /tmp/projectH-playwright-8880.config.mjs`
  - `16 passed, 1 failed (4.8m)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g '검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다' --config /tmp/projectH-playwright-8880.config.mjs --repeat-each=3`
  - `3 passed (33.1s)`
- `python3 -m unittest -v tests.test_web_app`
  - 이번은 Playwright smoke triage 라운드라 재실행하지 않았습니다.

## 남은 리스크
- default 포트 `8879`를 고정한 `make e2e-test`는 multi-lane 환경에서 concurrent occupant에 막혀 rerun 재현성이 흔들립니다.
- `e2e/tests/web-smoke.spec.mjs:246`의 search-only preview visibility는 equivalent full suite에서 한 번 실패했고 focused repeat에서는 통과했습니다. 현재는 browser contract보다 test readiness gate 쪽이 더 의심됩니다.
- `e2e/tests/web-smoke.spec.mjs:541`의 corrected-save saved-history `#response-content-verdict-state` broad partial 1건은 여전히 남아 있지만, 현재 full-suite flake를 안정화하기 전까지는 우선순위를 낮추는 편이 맞습니다.
