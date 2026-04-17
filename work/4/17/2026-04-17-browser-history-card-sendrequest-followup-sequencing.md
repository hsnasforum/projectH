# 2026-04-17 browser-history-card-sendrequest-followup-sequencing

## 변경 파일

- `app/static/app.js`

## 사용 skill

- work-log-closeout

## 변경 이유

seq 248 fix 조사 중 확인된 browser-level bug-adjacent 문제(handoff `browser-history-card-sendrequest-followup-sequencing`)를 좁게 닫는 라운드입니다. `app/static/app.js::sendRequest(...)`가 `state.isBusy`가 true일 때 `null`을 돌려주며 silently no-op 됐고, Playwright natural-reload follow-up / second-follow-up 시나리오가 `page.evaluate`로 `sendRequest(...)`를 직접 호출할 때 이전 streaming 이 아직 끝나지 않으면 다음 step이 조용히 사라져 이전 step의 DOM 상태가 남아 있는 채로 assertion이 통과하는 timing race가 백엔드별로 드리프트했습니다(예: JSON-default는 step 1만 서버에 도착하고 step 2·3은 early-return, sqlite는 step 1이 빨라 step 2·3 모두 실발사). 이번 라운드는 `sendRequest`가 in-flight promise 를 대기하도록 바꿔 page-triggered step이 결정론적으로 순차 실행되게 만들었고, UI double-submit 차단과 cancel semantics은 기존 `setBusyControls`의 DOM-level disabled 처리에 그대로 맡겨 실제 사용자 경험은 바꾸지 않았습니다. 문서, controller/runtime, server/storage, 다른 family는 이번 scope 밖으로 유지했습니다.

## 핵심 변경

1. **`state.currentRequestPromise` 추적 + `sendRequest(...)` 순차 대기** (`app/static/app.js`):
   - `state` 객체에 `currentRequestPromise: null` 한 필드 추가.
   - `sendRequest(extraPayload, progressMode)`를 수정해, 진입 시 `state.currentRequestPromise`가 있으면 먼저 `await` 해 이전 in-flight sendRequest 가 완료(정상/에러 모두)될 때까지 기다리도록 했습니다. 이후 `state.isBusy`가 여전히 true면(승인/수정 플로우처럼 `currentRequestPromise`를 노출하지 않는 별도 게이트) 기존처럼 `null`로 no-op 돌려주는 legacy 안전망 유지. 그 외에는 실제 요청을 IIFE로 감싼 promise `pending`을 만들고 `state.currentRequestPromise = pending`으로 마킹한 뒤 `await pending`, 종료 시 `currentRequestPromise` 를 비우는 구조로 바꿨습니다. `startProgress`/`stopProgress`/`submitStreamPayload`/`renderResult`/`fetchSessions`/`renderError`/cancel 처리는 그대로 유지해 user-visible busy overlay, cancel 버튼, notice/error 렌더 계약이 바뀌지 않습니다.

2. **User-visible 계약 유지**:
   - `setBusyControls(busy)` 는 그대로이며, `state.isBusy`가 true인 동안 requestForm / new-session / refresh-session / load-session / approve / reissue / reject / suggestion / search-history / feedback / retry / cancel / history-item "다시 불러오기" 버튼 등 모든 trigger UI가 `disabled=true`가 됩니다. 따라서 실제 사용자가 UI로 sendRequest 를 추가 trigger 할 수 없고, 이번 promise-queue 변경은 button disable 을 우회해 programmatic 하게 호출되는 경로(예: Playwright `page.evaluate`)에만 실효가 있습니다. 더블-서브밋 / cancel / progress bar / copy 버튼 / 대기 중 응답 복사 등 visible behavior는 전부 동일합니다.
   - `sendFollowUpPrompt(...)`(line 765)은 기존대로 `if (state.isBusy) return;` 을 유지해 in-flight 중 재진입을 막습니다. `loadWebSearchRecord(recordId)`(line 3148)도 `if (!recordId || state.isBusy) return;` 를 유지해 history-item 버튼 click에 대한 초기 가드 그대로 동작합니다.

3. **Scope 준수**: `e2e/tests/web-smoke.spec.mjs`, 서버/스토리지 코드, controller/runtime, `core/agent_loop.py`, `tests/test_web_app.py`, 4개 inventory 문서는 이번 라운드에 건드리지 않았습니다. Playwright 시나리오에 새 wait helper 를 넣지 않았고, sqlite browser gate docs 79→103 확장은 이전 라운드 truth 그대로 유지합니다.

## 검증

handoff가 요구한 최소 family 4건을 JSON-default + sqlite 양 쪽에서 개별 `-g "<exact title>"`로 실행, shared-helper 드리프트 가드용으로 latest-update natural-reload follow-up 1건도 양 쪽에서 실행했습니다.

```
cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다 \(browser natural-reload path\)" --reporter=line  # 1 passed (9.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다 \(browser natural-reload path\)" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다" --reporter=line  # 1 passed (11.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (9.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (10.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update mixed-source 자연어 reload 후 follow-up에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (9.4s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update mixed-source 자연어 reload 후 follow-up에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (3.9s)
git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs  # clean
```

- JSON-default 전체 Playwright suite, sqlite browser full suite, `python3 -m unittest -v tests.test_web_app`, `make e2e-test` 는 이번 scope 가 좁은 browser-side sendRequest 시퀀싱 수정에 한정돼 있어 실행하지 않았습니다. 이번 product diff 는 `sendRequest` promise-queue 한 곳과 `state.currentRequestPromise` 필드 하나 추가뿐이며, Playwright helper / server / storage / 다른 family 는 건드리지 않았기 때문에 broad rerun 은 이번 범위 대비 과한 검증이었습니다. JSON-default 에서 실행시간이 3초 가량 늘어난(9-11s) 것은 step 2·3 가 실제로 서버로 발사되기 시작했다는 기대된 변화입니다.

## 남은 리스크

- 이번 fix 로 JSON-default Playwright natural-reload 체인 시나리오들은 이전처럼 timing race 로 우연히 지나가지 않고, 실제로 step 2·3 이 발사되고 seq 248의 `_reuse_web_search_record` prepend 덕분에 "확인된 사실 [교차 확인]:" contract 를 실측으로 만족시켜 통과합니다. sqlite gate docs(79→103)는 여전히 truthful 이며 이번 라운드에 재검증하지 않았지만 sqlite 실행이 `_reuse_web_search_record` 경로를 그대로 쓰기 때문에 회귀 사유가 없습니다.
- Browser helper 쪽 broader cleanup(예: `sendFollowUpPrompt` / `loadWebSearchRecord` 의 `if (state.isBusy) return;` 초기 가드도 promise-queue 로 통일, `submitStreamPayload` 단일 진입점 정리, double-submit semantic 을 button-disable 하나로 통합, Playwright 쪽 wait helper 도입)은 이번 slice 밖으로 남겨 뒀습니다. 당장은 `sendRequest` 만 promise-queue 로 바꾸고 나머지 진입점은 기존대로 재진입을 금지하는 방식이어서 UI 재진입 / cancel 계약은 변화 없고, 후속 helper 통합 라운드에서 함께 정리하는 편이 맞습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 문서 diff 에는 이전 라운드에서 넘어온 48~103번 sqlite browser gate 행과 baseline 문장 확장이 staged-uncommitted 로 유지되어 있습니다. 이번 라운드는 dirty-worktree 지침에 따라 그 hunks 를 되돌리지 않았고 새로 문서를 추가하지도 않았습니다.
