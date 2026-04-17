# 2026-04-17 sqlite-browser-history-card-click-reload-composer-followup-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- work-log-closeout

## 변경 이유

seq 250이 `sendRequest(...)` busy-state early-return 때문에 page-scoped step이 silently no-op 하던 결정성 문제를 좁게 닫은 뒤, handoff seq 251은 같은 family의 남은 current-risk인 "click reload → 실제 브라우저 composer를 거친 plain follow-up" 경로가 sqlite backend에서도 JSON-default와 동일하게 동작하는지를 확인하도록 지정했습니다. 이 경로는 `load_web_search_record_id` 를 실어 보내지 않고 UI composer(textarea → 전송 버튼) 를 통해 일반 질문을 보내는 흐름이라, prior `/work` 노트들이 계속 뒤로 미뤄 둔 실-사용자 가시 표면입니다. 이번 라운드는 제품 코드나 Playwright 본문 변경 없이 두 exact sqlite Playwright 시나리오를 `playwright.sqlite.config.mjs` 로 개별 실행해 현재 tree에서 이미 통과함을 확인하고, handoff의 "docs 이동은 sqlite scenarios가 실제로 닫혔을 때만" 규칙에 따라 sqlite browser gate inventory 4개 문서를 한 번에 확장했습니다 (103 → 105). 추가 helper refactor나 다른 family 확장은 scope 밖으로 유지했습니다.

## 핵심 변경

1. **sqlite browser composer follow-up parity 실측 통과 확인** (제품 코드, sqlite config, test body, app/static/app.js 모두 무변경):
   - `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 top-level claim_coverage를 유지합니다" --reporter=line` → 1 passed (4.7s)
   - `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 empty claim_coverage surfaces를 유지합니다" --reporter=line` → 1 passed (4.7s)
   - 두 시나리오는 모두 `e2e/tests/web-smoke.spec.mjs` 에 이미 존재하며 (line 2405, 3000), 현재 tree 기준으로 `load_web_search_record_id` 없는 composer plain follow-up 경로에서 entity-card는 top-level `claim_coverage` 유지, latest-update는 empty claim_coverage surfaces 유지라는 shipped 계약을 sqlite backend도 만족합니다.

2. **sqlite browser gate inventory 4개 문서 동기화 (103 → 105)**:
   - `README.md`: sqlite browser smoke gate 번호 목록에 104, 105번으로 두 composer plain follow-up title을 그대로 추가.
   - `docs/ACCEPTANCE_CRITERIA.md`: sqlite backend gate scenarios 끝에 같은 두 계약을 short-hand 라인으로 추가 (entity-card top-level claim_coverage retention, latest-update empty claim_coverage surfaces retention, `load_web_search_record_id` 없는 실제 browser composer 경로 명시).
   - `docs/MILESTONES.md`: sqlite browser baseline 문장 끝에 `history-card click-reload composer plain follow-up contract` 항목을 natural-reload chain contract 다음 단계로 추가 (entity-card top-level claim_coverage retention + latest-update empty claim_coverage surfaces retention through the real browser composer path without `load_web_search_record_id`).
   - `docs/TASK_BACKLOG.md`: `Partial / Opt-In` 섹션의 sqlite browser baseline 문장에도 같은 click-reload composer plain follow-up contract 항목을 natural-reload chain contract 뒤에 명시.

3. **Scope 준수**: `core/agent_loop.py`, `storage/*`, `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, controller/runtime, `tests/test_web_app.py` 는 이번 라운드에 건드리지 않았습니다. `sendRequest` 시퀀싱 수정(seq 250), `_reuse_web_search_record` prepend 수정(seq 248) 모두 그대로 유지되며, helper-wide refactor / 다른 family / 별도 docs-only round 는 열지 않았습니다.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 top-level claim_coverage를 유지합니다" --reporter=line  # 1 passed (4.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card latest-update click reload 후 composer를 거친 plain follow-up 경로가 load_web_search_record_id 없이 empty claim_coverage surfaces를 유지합니다" --reporter=line  # 1 passed (4.7s)
git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- JSON-default Playwright 재실행은 handoff 조건(code changes 시에만)에 따라 실행하지 않았습니다. 이번 라운드는 product code / test body / sqlite config 모두 무변경이고 sqlite 에서 이미 통과하기 때문입니다. 같은 두 JSON-default title 은 직전 round 까지 shipped 되어 있고 이번 라운드에 회귀가 발생할 사유가 없습니다.
- `make e2e-test`, sqlite browser full suite, `python3 -m unittest -v tests.test_web_app` 는 이번 scope 대비 과해 실행하지 않았습니다. 두 exact sqlite 시나리오는 각각 독립 rerun 으로 통과함을 확인했고, broader 실행이 필요할 제품 diff 는 없었습니다.

## 남은 리스크

- sqlite browser gate inventory 는 이번 라운드로 총 105 건까지 확장되었습니다. handoff scope 에 따라 docs-only follow-up 라운드를 따로 열지 않았고, 이번 sqlite 두 시나리오 실측 결과 + 4개 문서 sync 를 같은 라운드에서 마감했습니다.
- 이전 라운드 dirty-worktree hunks (click-reload follow-up / second-follow-up, 자연어 reload reload-only / chain, sqlite baseline 문장 확장) 는 그대로 유지했습니다. handoff dirty-worktree 지침에 따라 되돌리지 않았습니다. 이번 라운드 diff 는 104~105 행 2줄 추가 + 4개 baseline 문장 확장 1항목씩 추가입니다.
- seq 250의 `sendRequest` promise-queue 변경과 seq 248의 `_reuse_web_search_record` stored-summary prepend 는 그대로 유지되며, 이번 composer plain follow-up 경로도 같은 코드 path 위에서 잘 동작함을 확인했습니다. Browser helper 통일(다른 진입점의 `if (state.isBusy) return;` 을 promise-queue 로 통일, Playwright wait helper 도입 등)은 여전히 다음 라운드의 후속 정비 대상으로 남습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 이번 라운드는 sqlite backend 실측만 했고 JSON-default path 는 재실행하지 않았습니다. composer plain follow-up 계약은 JSON-default smoke 에서 이미 shipped 계약이라 회귀 사유가 없지만, 다음 라운드 release-check 가 필요한 경우 함께 재실행이 필요합니다.
