## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- `seq 265` Gemini advice는 `work/4/17/2026-04-17-browser-history-card-sendrequest-followup-sequencing.md`를 next control 전에 retro-verify 하는 쪽이 가장 truthfully 맞다고 권고했습니다.
- 이번 verification round는 그 권고를 실제로 self-heal 가능한지 확인하기 위해, `app/static/app.js`의 `sendRequest(...)` promise-queue 구현과 `/work`가 적은 focused browser rerun 재현 가능성을 현재 sandbox에서 직접 다시 점검합니다.

## 핵심 변경
- 대상 `/work`의 핵심 코드 변경 자체는 현재 트리에 남아 있습니다.
  - `app/static/app.js`의 `state`에는 `currentRequestPromise: null` 필드가 있고,
  - `sendRequest(...)`는 `while (state.currentRequestPromise) { await ... }`로 in-flight request를 순차 대기한 뒤,
  - `state.isBusy` legacy guard를 유지하면서 `pending` promise를 `state.currentRequestPromise`에 걸고 종료 시 해제합니다.
- `/work`가 기준으로 삼은 browser scenario inventory도 현재 트리에 그대로 존재합니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 zero-strong-slot natural-reload follow-up / second-follow-up,
  - noisy single-source natural-reload follow-up / second-follow-up,
  - latest-update mixed-source natural-reload follow-up exact title이 그대로 있습니다.
- 하지만 이번 round에서는 `/work`가 적은 Playwright rerun을 현재 sandbox에서 재현하지 못했습니다.
  - `npx playwright test tests/web-smoke.spec.mjs -g "<exact title>" --reporter=line` 실행 시 Playwright `webServer`가 `python3 -m app.web --host 127.0.0.1 --port 8879`를 띄우는 단계에서 `PermissionError: [Errno 1] Operation not permitted`로 실패했습니다.
  - 같은 이유로 `python3 -m app.web --host 127.0.0.1 --port 8879`와 `--port 8881` 직접 probe도 모두 같은 bind permission error로 막혔습니다.
  - 현재 sandbox에서는 local web server bind 자체가 차단돼 있어 JSON-default browser rerun을 independent하게 다시 잠글 수 없습니다.
- 따라서 이 `/work`는 "코드와 scenario inventory는 현재 트리와 맞다"까지는 확인됐지만, `/work`가 적어 둔 focused browser rerun pass를 이번 round에서 독립 재실행으로 다시 보증하지는 못했습니다.
- 이 상태에서는 `seq 265` advisory를 Claude implement handoff로 바로 전환할 수 없습니다. advisory가 요구한 retro-verify 자체가 environment truth-sync blocker에 걸려 있기 때문입니다.

## 검증
- `sed -n '780,860p' app/static/app.js`
  - 결과: `sendRequest(...)`의 promise-queue 구현(`currentRequestPromise`, `while (...) await`, `pending` set/clear)을 확인했습니다.
- `rg -n "currentRequestPromise|entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\\.wiki/ko\\.wikipedia\\.org가 drift하지 않습니다 \\(browser natural-reload path\\)|entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\\.wiki/ko\\.wikipedia\\.org가 drift하지 않습니다|entity-card noisy single-source claim\\(출시일/2025/blog\\.example\\.com\\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\\.wiki/ko\\.wikipedia\\.org/blog\\.example\\.com provenance가 유지됩니다|entity-card noisy single-source claim\\(출시일/2025/blog\\.example\\.com\\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\\.wiki/ko\\.wikipedia\\.org/blog\\.example\\.com provenance가 유지됩니다|latest-update mixed-source 자연어 reload 후 follow-up에서 source path\\(store\\.steampowered\\.com, yna\\.co\\.kr\\) \\+ WEB badge, 최신 확인, 공식\\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - 결과: 코드 앵커와 exact browser title 5개를 재확인했습니다.
- `npx playwright test tests/web-smoke.spec.mjs -g "<exact title>" --reporter=line`
  - 결과: 재현 실패. Playwright `webServer`가 `python3 -m app.web --host 127.0.0.1 --port 8879` 시작 단계에서 `PermissionError: [Errno 1] Operation not permitted`로 종료됐습니다.
- `python3 -m app.web --host 127.0.0.1 --port 8879`
  - 결과: `PermissionError: [Errno 1] Operation not permitted`
- `python3 -m app.web --host 127.0.0.1 --port 8881`
  - 결과: `PermissionError: [Errno 1] Operation not permitted`
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - 결과: 출력 없음

## 남은 리스크
- 이번 round에서는 local webServer bind가 sandbox에서 막혀 JSON-default Playwright rerun을 independent하게 재현하지 못했습니다. 따라서 `work/4/17/2026-04-17-browser-history-card-sendrequest-followup-sequencing.md`의 browser pass claim은 현재 environment 기준으로 fully re-lock 되지 않았습니다.
- same-family latest verified pair인 `work/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity.md` / `verify/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity-verification.md`는 유지되지만, Gemini가 우선순위를 높게 본 `sendRequest` shared-helper fix는 여전히 retro-verify pending입니다.
- approval policy가 `never`이고 sandbox outside execution 승인도 불가하므로, 이 blocker는 이번 turn에서 Codex가 자력으로 해소할 수 없는 environment truth-sync stop에 가깝습니다.
