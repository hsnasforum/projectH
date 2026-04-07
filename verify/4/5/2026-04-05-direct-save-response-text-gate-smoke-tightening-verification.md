## 변경 파일
- verify/4/5/2026-04-05-direct-save-response-text-gate-smoke-tightening-verification.md
- .pipeline/claude_handoff.md

## 사용 skill
- round-handoff
- e2e-smoke-triage

## 변경 이유
- latest `/work`인 `work/4/5/2026-04-05-direct-save-response-text-gate-smoke-tightening.md`의 direct approved-save readiness gate 변경이 current tree와 재실행 기준으로 truthful한지 다시 확인해야 했습니다.
- 같은 날 latest `/verify`는 aggregate-trigger second-request branch 기준이었으므로, 오늘 기준 current truth와 next exact slice를 save-result family 기준으로 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 핵심 test change는 truthful합니다. `e2e/tests/web-smoke.spec.mjs:330-331`는 현재 `response-box` broad gate가 아니라 `response-text` visible + `저장했습니다.` gate로 반영되어 있습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 깨끗했습니다.
- canonical `make e2e-test`는 이번 verification round에서도 그대로 재현되지 못했습니다. 실제 재실행 결과는 `Error: http://127.0.0.1:8879 is already used`였고, latest `/work`가 적은 blockage와 일치합니다.
- 대신 isolated alternate-port 검증으로 `/tmp/projecth-playwright-8895.config.mjs`를 만들어 target scenario 1건만 다시 돌렸고, `승인 후 실제 note가 저장됩니다`는 `1 passed (11.6s)`로 통과했습니다.
- current tree에 남은 broad `responseBox.toContainText(...)` assertions는 `e2e/tests/web-smoke.spec.mjs:347`, `e2e/tests/web-smoke.spec.mjs:358`, `e2e/tests/web-smoke.spec.mjs:426`, `e2e/tests/web-smoke.spec.mjs:517`, `e2e/tests/web-smoke.spec.mjs:527`, `e2e/tests/web-smoke.spec.mjs:547`, `e2e/tests/web-smoke.spec.mjs:619`입니다.
- 그중 다음 smallest same-family current-risk reduction은 `late-flip` scenario의 first save-result gate line `347`입니다. 같은 scenario 안의 later post-reject line `358`보다 범위가 작고, rejected-verdict line `426`과 corrected-save family lines `517/527/547/619`보다 단순한 original-draft save confirmation 경로입니다.
- runtime `app/static/app.js:3153-3165`는 `responseBox`를 먼저 보이게 하고 `responseText.textContent`를 채운 뒤 메타/패널 렌더링으로 이어집니다. 그래서 late-flip initial save-result gate도 `response-box` 전체보다 `response-text`를 readiness gate로 쓰는 편이 더 deterministic합니다.

## 검증
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '320,362p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '420,436p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '508,552p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '610,622p'`
- `rg -n "await expect\\(responseBox\\)\\.toContainText\\(|page.getByTestId\\(\"response-box\"\\)\\.toContainText\\(" e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `make e2e-test`
  - 실패: `Error: http://127.0.0.1:8879 is already used, make sure that nothing is running on the port/url or set reuseExistingServer:true in config.webServer.`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs --grep '승인 후 실제 note가 저장됩니다' --config /tmp/projecth-playwright-8895.config.mjs`
  - `1 passed (11.6s)`
- `python3 -m unittest -v tests.test_web_app`
  - 이번은 test-only Playwright stabilization family 검수라 재실행하지 않았습니다.

## 남은 리스크
- latest `/work`의 코드 변경 자체와 direct-save target scenario는 current tree에서 맞지만, canonical `make e2e-test` full-suite는 포트 `8879` 충돌 때문에 이번 verification round에서도 그대로 재현하지 못했습니다.
- 남은 broad response-box text gate는 save-result families에 있고, 아직 late-flip, rejected-verdict, corrected-save 경로에 남아 있습니다.
- 다음 Claude slice는 가장 작은 same-family risk인 `late-flip` initial save-result path `e2e/tests/web-smoke.spec.mjs:347`의 `저장했습니다.` response-text gate tightening 1건으로 좁히는 편이 맞습니다.
