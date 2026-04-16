# 2026-04-16 controller smoke rerun hardening verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-controller-smoke-rerun-hardening.md`가 주장한 controller smoke rerun hardening 라운드가 현재 트리와 재실행 기준으로 사실인지 다시 확인하는 검증 라운드입니다.
- 사용자가 기존 verify 경로 `verify/4/16/2026-04-16-controller-background-preload-readiness-hardening-verification.md`를 재사용하도록 지정했으므로, 이번 note는 같은 경로를 update-in-place 하되 내용을 최신 `/work` 기준 truth로 교체합니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 대체로 사실입니다.
  - `e2e/playwright.controller.config.mjs`는 `process.env.CONTROLLER_SMOKE_PORT || "8781"`를 읽어 `use.baseURL`, `webServer.command`, `webServer.url` 세 곳에 동일한 포트를 반영합니다.
  - `Makefile`에는 `controller-test` target과 `.PHONY` 등록이 실제로 들어 있습니다.
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에는 `make controller-test` 진입점과 `CONTROLLER_SMOKE_PORT` 포트 오버라이드 설명이 반영돼 있습니다.
- 다만 최신 `/work`의 검증 주장은 현재 Codex sandbox에서는 재확인되지 않았습니다.
  - `make controller-test`
  - `CONTROLLER_SMOKE_PORT=8782 make controller-test`
  두 명령 모두 Playwright가 실제 테스트를 시작하기 전에 `controller.server` 기동 단계에서 `PermissionError: [Errno 1] Operation not permitted`로 실패했습니다.
- 현재 shipped truth는 다음과 같습니다.
  - controller smoke rerun hardening용 정적 wiring은 들어 있습니다. 기본 포트는 `8781`이고, 환경 변수로 다른 포트를 주면 config가 그 값을 따라갑니다.
  - canonical rerun entrypoint `make controller-test`도 현재 트리에 존재합니다.
  - controller는 여전히 internal/operator tooling이며 `app.web` release gate 밖입니다.
  - 다만 current sandbox에서는 listening socket 생성 자체가 차단되어 controller smoke pass 결과를 현장에서 재검증할 수 없습니다.

## 검증
- `ls -lt work/4/16 | sed -n '1,20p'`
  - 결과: `work/4/16/2026-04-16-controller-smoke-rerun-hardening.md`가 오늘 최신 `/work`임을 확인했습니다.
- `ls -lt verify/4/16 | sed -n '1,20p'`
  - 결과: 사용자가 지정한 `verify/4/16/2026-04-16-controller-background-preload-readiness-hardening-verification.md`가 오늘 최신 `/verify`였고, 같은 경로를 update-in-place 대상으로 재사용합니다.
- `git diff --name-only -- e2e/playwright.controller.config.mjs Makefile README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: latest `/work`가 적은 6개 파일이 현재 diff 대상으로 확인됐습니다.
- `git diff -- e2e/playwright.controller.config.mjs Makefile README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md | sed -n '1,280p'`
  - 결과: env-driven port wiring, `controller-test` target, root docs sync가 실제로 들어 있음을 확인했습니다.
- `rg -n "CONTROLLER_SMOKE_PORT|controller-test|make controller-test|playwright.controller.config|8781|8782" e2e/playwright.controller.config.mjs Makefile README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: config/Makefile/docs 전반에 default port `8781`, canonical target `make controller-test`, env override `CONTROLLER_SMOKE_PORT`가 일관되게 반영돼 있음을 확인했습니다.
- `make controller-test`
  - 결과: 실패. `controller.server` 기동 단계에서 `PermissionError: [Errno 1] Operation not permitted`가 발생해 Playwright가 시작되지 못했습니다.
- `CONTROLLER_SMOKE_PORT=8782 make controller-test`
  - 결과: 실패. 포트를 바꿔도 같은 `PermissionError: [Errno 1] Operation not permitted`가 발생했습니다.
- `make -n controller-test`
  - 결과: `cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line`로 canonical target wiring을 재확인했습니다.
- `node --input-type=module -e 'import("./e2e/playwright.controller.config.mjs").then(({default: cfg}) => { console.log(cfg.use.baseURL); console.log(cfg.webServer.command); console.log(cfg.webServer.url); })'`
  - 결과: `8781` default port가 `baseURL`, `webServer.command`, `webServer.url`에 일관되게 반영됐습니다.
- `CONTROLLER_SMOKE_PORT=8782 node --input-type=module -e 'import("./e2e/playwright.controller.config.mjs").then(({default: cfg}) => { console.log(cfg.use.baseURL); console.log(cfg.webServer.command); console.log(cfg.webServer.url); })'`
  - 결과: `8782` override가 `baseURL`, `webServer.command`, `webServer.url`에 일관되게 반영됐습니다.
- `python3 - <<'PY' ... socket.socket() ... PY`
  - 결과: 최소 재현에서도 `PermissionError: [Errno 1] Operation not permitted`가 발생해 current sandbox가 listening socket 생성 자체를 막고 있음을 확인했습니다.
- `git diff --check -- e2e/playwright.controller.config.mjs Makefile README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음

## 남은 리스크
- current sandbox에서는 `controller.server`가 socket을 열지 못해 `make controller-test` pass 여부를 재확인할 수 없습니다. 따라서 latest `/work`의 검증 결과는 현재 Codex 라운드 기준으로 fully revalidated 상태가 아닙니다.
- controller smoke는 여전히 `app.web` release gate 밖 별도 명령입니다.
- 다음 control은 우선순위 tie-break보다 truth-sync 정리가 먼저입니다. operator가 socket 허용 환경에서 같은 `/work` 검증을 다시 돌릴지, 아니면 이번 라운드를 static-only verification으로 수용할지 정해야 합니다.
