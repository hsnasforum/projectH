## 변경 파일
- verify/4/5/2026-04-05-candidate-confirmation-initial-response-text-gate-smoke-tightening-verification.md
- .pipeline/claude_handoff.md

## 사용 skill
- round-handoff
- e2e-smoke-triage

## 변경 이유
- latest `/work`인 `work/4/5/2026-04-05-candidate-confirmation-initial-response-text-gate-smoke-tightening.md`의 candidate-confirmation initial readiness gate 변경이 current tree와 재실행 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest `/verify`는 rejected-verdict branch 기준이었으므로, 오늘 기준 current truth와 다음 exact slice를 candidate-confirmation 이후 상태로 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 핵심 test change는 truthful합니다. `e2e/tests/web-smoke.spec.mjs:573-574`는 현재 `response-box` broad gate가 아니라 `response-text` visible + `middleSignal` gate로 반영되어 있습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 깨끗했습니다.
- canonical `make e2e-test`는 이번 verification round에서도 그대로 재현되지 못했습니다. 실제 재실행 결과는 `Error: http://127.0.0.1:8879 is already used`였고, latest `/work`가 적은 blockage와 일치합니다.
- 대신 isolated alternate-port 검증으로 `/tmp/projecth-playwright-8892.config.mjs`를 만들어 target scenario 1건만 다시 돌렸고, `candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다`는 `1 passed (31.5s)`로 통과했습니다.
- current render order도 narrow gate 선택과 맞습니다. `app/static/app.js:3153-3164`에서 `responseBox`를 먼저 보이게 하고 `responseText.textContent`를 채운 뒤, 그 다음 candidate-confirmation control을 렌더링합니다. 그래서 same-family initial readiness gate는 계속 `response-text` 직접 참조가 더 deterministic합니다.
- current tree에서 `middleSignal`을 아직 broad container로 기다리는 남은 assertions는 `e2e/tests/web-smoke.spec.mjs:736`과 `e2e/tests/web-smoke.spec.mjs:754`입니다. 그중 다음 smallest same-family current-risk reduction은 `aggregate-trigger` scenario의 first ready gate line `736`입니다. line `754`는 같은 scenario의 later second-request gate라 한 단계 뒤로 두는 편이 맞습니다.

## 검증
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '563,579p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '724,756p'`
- `nl -ba app/static/app.js | sed -n '3148,3172p'`
- `rg -n "toContainText\\(middleSignal\\)|responseBox\\).*middleSignal|response-text\\).*middleSignal" e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `make e2e-test`
  - 실패: `Error: http://127.0.0.1:8879 is already used, make sure that nothing is running on the port/url or set reuseExistingServer:true in config.webServer.`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs --grep 'candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다' --config /tmp/projecth-playwright-8892.config.mjs`
  - `1 passed (31.5s)`
- `python3 -m unittest -v tests.test_web_app`
  - 이번은 test-only Playwright stabilization family 검수라 재실행하지 않았습니다.

## 남은 리스크
- latest `/work`의 코드 변경 자체와 candidate-confirmation target scenario는 current tree에서 맞지만, canonical `make e2e-test` full-suite는 포트 `8879` 충돌 때문에 이번 verification round에서도 그대로 재현하지 못했습니다.
- current readiness family의 남은 broad gate는 `aggregate-trigger` lines `736`과 `754`입니다.
- 다음 Claude slice는 가장 작은 same-family risk인 `aggregate-trigger` initial `response-text` gate tightening 1건으로 좁히는 편이 맞습니다.
