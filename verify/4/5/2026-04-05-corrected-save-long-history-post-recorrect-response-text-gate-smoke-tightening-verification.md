## 변경 파일
- verify/4/5/2026-04-05-corrected-save-long-history-post-recorrect-response-text-gate-smoke-tightening-verification.md
- .pipeline/claude_handoff.md

## 사용 skill
- round-handoff
- e2e-smoke-triage

## 변경 이유
- latest `/work`인 `work/4/5/2026-04-05-corrected-save-long-history-post-recorrect-response-text-gate-smoke-tightening.md`의 corrected-save long-history post-recorrect gate 변경이 current tree와 재실행 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest `/verify`는 corrected-save long-history post-reject gate 기준이었으므로, same-family 마지막 gate가 실제로 닫혔는지와 그 다음 exact slice가 무엇인지 current truth로 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 핵심 test change와 rerun claim은 truthful합니다. `e2e/tests/web-smoke.spec.mjs:553-554`는 현재 `responseBox` broad gate가 아니라 `response-text` visible + `승인 시점에 고정된 수정본` gate로 반영되어 있습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 깨끗했습니다.
- canonical `make e2e-test`는 이번 verification round에서도 그대로 재현되지 못했습니다. 실제 재실행 결과는 `Error: http://127.0.0.1:8879 is already used`였고, latest `/work`가 적은 blockage와 일치합니다.
- 대신 isolated alternate-port 검증으로 `/tmp/projecth-playwright-8903.config.mjs`를 만들어 target scenario 1건만 다시 돌렸고, `corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다`는 `1 passed (25.3s)`로 통과했습니다.
- current tree에서 `승인 시점에 고정된 수정본` gate inventory를 다시 세어 보면, `e2e/tests/web-smoke.spec.mjs:491`, `:522`, `:533`, `:554`는 이미 `response-text` 직접 gate이고 broad `responseBox` gate는 candidate-confirmation path `e2e/tests/web-smoke.spec.mjs:626` 1건만 남았습니다.
- runtime `app/static/app.js:3153-3167`는 `responseBox`를 보여 준 뒤 `responseText.textContent`를 먼저 채우고, 그다음 메타/패널 렌더링으로 이어집니다. 그래서 남은 candidate-confirmation save-result gate도 `response-box` 전체보다 `response-text`를 readiness gate로 쓰는 편이 더 deterministic합니다.
- 따라서 다음 exact slice는 candidate-confirmation path `e2e/tests/web-smoke.spec.mjs:626`의 save-result `승인 시점에 고정된 수정본` broad gate 1건을 `response-text` 기준으로 좁히는 test-only stabilization이 맞습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '548,556p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '620,628p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '560,606p'`
- `nl -ba app/static/app.js | sed -n '3150,3167p'`
- `rg -n '승인 시점에 고정된 수정본' e2e/tests/web-smoke.spec.mjs`
- `make e2e-test`
  - 실패: `Error: http://127.0.0.1:8879 is already used, make sure that nothing is running on the port/url or set reuseExistingServer:true in config.webServer.`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs --grep 'corrected-save 저장 뒤 늦게 내용 거절하고 다시 수정해도 saved snapshot과 latest state가 분리됩니다' --config /tmp/projecth-playwright-8903.config.mjs`
  - `1 passed (25.3s)`
- `python3 -m unittest -v tests.test_web_app`
  - 이번은 test-only Playwright stabilization family 검수라 재실행하지 않았습니다.

## 남은 리스크
- latest `/work`의 code change와 target scenario rerun은 current tree에서 맞지만, canonical `make e2e-test` full-suite는 포트 `8879` 충돌 때문에 이번 verification round에서도 그대로 재현하지 못했습니다.
- broad `승인 시점에 고정된 수정본` save-result gate는 current tree 기준 candidate-confirmation path `e2e/tests/web-smoke.spec.mjs:626` 1건만 남았습니다.
- 다음 Claude slice는 candidate-confirmation path save-result gate 1건을 `response-text` visible + exact text 기준으로 좁히는 `candidate-confirmation save-result response-text gate smoke tightening`으로 고정하는 편이 맞습니다.
