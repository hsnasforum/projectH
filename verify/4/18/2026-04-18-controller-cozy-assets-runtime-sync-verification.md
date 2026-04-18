# 2026-04-18 README controller smoke inventory truth-sync verification

## 변경 파일
- `verify/4/18/2026-04-18-controller-cozy-assets-runtime-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- `work/4/18/2026-04-18-readme-controller-smoke-inventory-truth-sync.md`가 controller smoke inventory를 실제 `e2e/tests/controller-smoke.spec.mjs`와 맞췄다고 기록했으므로, docs-only 범위에서 README 진술과 현재 smoke/config truth를 다시 대조해야 했습니다.
- 이번 라운드는 `README.md` 한 파일만 바뀐 docs-only truth-sync round이므로, 직접 파일 비교와 `git diff --check`만 다시 확인하고 code/unit/Playwright rerun으로 넓히지 않았습니다.

## 핵심 변경
- latest `/work`의 큰 방향은 맞습니다. `README.md`는 이제 dedicated controller smoke 실행 경로를 `make controller-test`와 `cd e2e && CONTROLLER_SMOKE_PORT=<free-port> npx playwright test -c playwright.controller.config.mjs --reporter=line`로 적고 있고, scenario 1-9도 현재 `e2e/tests/controller-smoke.spec.mjs`, `e2e/playwright.controller.config.mjs`, `Makefile`과 일치합니다.
- 다만 `/work`는 아직 완전히 truthful하지 않습니다. `README.md`와 `/work`의 10번 시나리오는 `window.testPickIdleTargets("Claude", 20)`가 `claude_desk` 안의 20개 좌표를 assert한다고 적었지만, 현재 `e2e/tests/controller-smoke.spec.mjs`는 `window.testHistoryPenalty(...)`가 빈 배열을 반환하는지와 picked point의 `x` 좌표가 `claude_desk` 가로 범위 안에 있는지만 검사합니다. 즉 current README는 shipped runtime 구현(`controller/js/cozy.js::sampleIdleTarget()`은 x/y 모두 home zone 안에서 샘플링)과는 맞지만, "현재 smoke inventory가 spec 파일과 exact match"라는 latest `/work` 주장과는 한 단계 어긋납니다.
- 따라서 이번 `/work`는 "README inventory의 대부분을 바로잡았다"는 수준에서는 맞지만, 10번 시나리오의 exact assertion 범위까지 완전히 닫았다고 보기는 어렵습니다. 남은 drift는 controller runtime bug라기보다 controller smoke coverage / docs-spec exactness gap에 가깝습니다.

## 검증
- `git diff --check -- README.md`
  - 결과: 통과
- 직접 대조:
  - 대상: `README.md`, `e2e/tests/controller-smoke.spec.mjs`, `e2e/playwright.controller.config.mjs`, `Makefile`, `controller/js/cozy.js`
  - 결과: run instruction과 scenario 1-9는 current truth와 일치, scenario 10은 README와 `/work`가 current Playwright assertion보다 더 강하게 서술함을 확인
- 이번 라운드에서는 unit test나 Playwright smoke를 다시 실행하지 않았습니다.
  - 이유: latest `/work`가 code/test/runtime 변경을 주장하지 않은 docs-only truth-sync round이기 때문입니다.

## 남은 리스크
- `README.md`의 10번 smoke bullet과 latest `/work` closeout은 current `e2e/tests/controller-smoke.spec.mjs`보다 강한 보장을 적고 있습니다. 후속 라운드에서는 문구를 약화시키기보다, shipped `sampleIdleTarget()` 동작에 맞춰 scenario 10을 full home-zone bounds까지 검증하도록 tighten하는 편이 same-family current-risk reduction으로 더 적절합니다.
- controller smoke는 verify sandbox에서 local bind 제한을 계속 받을 수 있으므로, 다음 라운드에서 isolated Playwright rerun을 시도하더라도 bind 실패 여부를 `/work`에 명시해야 합니다.
