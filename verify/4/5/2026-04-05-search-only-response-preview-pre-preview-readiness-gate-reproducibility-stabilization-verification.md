## 변경 파일
- verify/4/5/2026-04-05-search-only-response-preview-pre-preview-readiness-gate-reproducibility-stabilization-verification.md
- .pipeline/claude_handoff.md

## 사용 skill
- round-handoff
- e2e-smoke-triage

## 변경 이유
- latest `/work`의 search-only pre-preview readiness gate 변경이 current tree와 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 최신 `/verify`는 이전 rejected-verdict 라운드 기준이어서, 오늘 기준 current truth와 다음 exact slice를 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`인 `work/4/5/2026-04-05-search-only-response-preview-pre-preview-readiness-gate-reproducibility-stabilization.md`의 핵심 변경은 truthful합니다. `e2e/tests/web-smoke.spec.mjs:245-246`에 `#selected-text` pre-preview gate가 추가되어 있고, current tree에는 그대로 반영되어 있습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 깨끗했습니다.
- isolated full suite `cd e2e && npx playwright test --config /tmp/projectH-playwright-8880.config.mjs`는 한 번 `16 passed, 1 failed (4.5m)`였고, 실패는 같은 search-only test의 recovery branch `e2e/tests/web-smoke.spec.mjs:294`였습니다. 즉 pre-preview gate가 막으려던 기존 line `246` failure는 현재 재현되지 않았습니다.
- 같은 search-only test를 isolated config로 `--repeat-each=3` 재실행한 결과는 `3 passed (29.7s)`였습니다. latest `/work`에 적힌 multi-worker residual risk는 current rerun 기준으로는 재현되지 않았습니다.
- canonical `make e2e-test`를 default `8879` 포트가 비어 있는 상태에서 다시 돌린 결과는 `17 passed (4.5m)`였습니다. 따라서 current persistent truth는 search-only family가 현재는 닫혀 있고, latest `/work`의 main smoke claim도 재현됐다는 쪽입니다.
- 다음 Claude handoff는 search-only follow-up이 아니라, current tree에서 아직 broad partial로 남은 corrected-save saved-history `#response-content-verdict-state` line `544` 1건을 exact-text로 좁히는 slice로 갱신했습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '243,248p'`
- `cd e2e && npx playwright test --config /tmp/projectH-playwright-8880.config.mjs`
  - `16 passed, 1 failed (4.5m)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g '검색만 응답은 transcript에서 preview cards만 보이고 본문 텍스트는 숨겨집니다' --config /tmp/projectH-playwright-8880.config.mjs --repeat-each=3`
  - `3 passed (29.7s)`
- `make e2e-test`
  - `17 passed (4.5m)`
- `python3 -m unittest -v tests.test_web_app`
  - 이번은 test-only Playwright stabilization 라운드라 재실행하지 않았습니다.

## 남은 리스크
- isolated alternate-port full suite에서는 search-only recovery branch `e2e/tests/web-smoke.spec.mjs:294`가 한 번 흔들렸습니다. 다만 focused repeat와 canonical `make e2e-test`는 모두 통과했으므로 현재는 persistent blocker로 보지 않습니다.
- `e2e/tests/web-smoke.spec.mjs:544`의 corrected-save saved-history `#response-content-verdict-state`는 아직 broad partial입니다.
- verification 중 만든 `/tmp/projectH-playwright-8880.config.mjs`는 repo tracked 대상이 아니며, persistent truth는 repo 파일과 `/verify` 메모를 기준으로 읽어야 합니다.
