# 2026-04-17 sqlite-browser-history-card-natural-reload-chain-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- work-log-closeout

## 변경 이유

seq 248이 `_reuse_web_search_record` follow-up 분기에서 저장된 normalized summary 를 prepend 하도록 좁게 고쳐 seq 247의 단일 parity blocker(붉은사막 noisy single-source 자연어 reload follow-up / 두 번째 follow-up sqlite 실패 2건)를 닫았습니다. seq 249는 그 fix가 24개 natural-reload chain sqlite 시나리오 전체에 대해서도 실제로 truthful한지 확인하고, 전부 통과하면 sqlite browser gate 문서 inventory 를 79 → 103으로 한 번에 확장하라는 handoff였습니다. 이번 라운드는 제품 코드나 sqlite config 변경 없이 24개 exact sqlite Playwright 시나리오를 각각 개별 실행해 전부 통과함을 확인한 뒤, `README.md` / `docs/ACCEPTANCE_CRITERIA.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md` sqlite browser gate inventory를 한꺼번에 동기화했습니다. 24-scenario bundle이 같은 라운드에 truthfully 닫히므로 더 작은 docs-only micro-slice를 다시 분할하지 않고 handoff가 지시한 한 번의 bounded bundle로 완결했습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (제품 코드, sqlite Playwright config, test body 전부 무변경, JSON-default path 무관):
   - 24개 exact sqlite 시나리오 전부 `cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "<exact title>" --reporter=line` 개별 실행으로 통과(3.7~4.3s 범위, 재시도 없음). seq 248에서 고친 noisy 2건뿐 아니라 zero-strong-slot / dual-probe / 붉은사막 actual-search / latest-update mixed·single·news-only·noisy-community 계열 22건도 그대로 통과했습니다.

2. **sqlite browser gate inventory 4개 문서 동기화 (79 → 103)**:
   - `README.md`: sqlite browser gate 번호 목록에 80~103번으로 natural-reload follow-up / second-follow-up chain 24개 exact title을 그대로 추가.
   - `docs/ACCEPTANCE_CRITERIA.md`: sqlite backend gate scenarios block 끝에 같은 24개를 short-hand 라인으로 추가.
   - `docs/MILESTONES.md`: sqlite browser baseline 문장 끝에 `history-card natural-reload follow-up / second-follow-up chain contract` 항목을 reload-only contract 다음 단계로 명시(zero-strong-slot missing-only count-summary drift-prevention, dual-probe mixed count-summary meta retention, noisy-source exclusion, store-seeded natural-reload chain empty-meta no-leak 포함).
   - `docs/TASK_BACKLOG.md`: `Partial / Opt-In` 섹션의 sqlite browser baseline 문장에도 같은 `history-card natural-reload follow-up / second-follow-up chain contract` 항목을 reload-only contract 다음 단계로 명시.

3. **Scope 준수**: `core/agent_loop.py`, `storage/sqlite_store.py`, `storage/session_store.py`, `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, controller/runtime 파일은 이번 라운드에 건드리지 않았습니다. `sendRequest` busy-state race cleanup, click-reload plain composer follow-up, 다른 family도 열지 않았습니다. 문서 diff에는 이전 라운드에서 이미 staged-uncommitted로 들어와 있던 48~79번 항목이 그대로 유지되며 이번 라운드는 80~103번 행만 새로 추가했습니다.

## 검증

24개 exact scenario를 각각 `-g "<exact title>"`로 sqlite Playwright config에서 개별 실행 (broader regex로 대체하지 않음, regex 특수문자는 백슬래시로 escape):

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card 자연어 reload 후 두 번째 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "history-card entity-card store-seeded actual-search 자연어 reload 체인에서 empty-meta no-leak contract가 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다 \(browser natural-reload path\)" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반, namu\.wiki/ko\.wikipedia\.org가 drift하지 않습니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card zero-strong-slot 자연어 reload 후 두 번째 follow-up에서 missing-only count-summary meta가 truthfully 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path\(pearlabyss\.com/200, pearlabyss\.com/300\)가 context box에 유지됩니다" --reporter=line  # 1 passed (3.7s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 mixed count-summary meta가 truthfully 유지됩니다" --reporter=line  # 1 passed (4.2s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 source path\(pearlabyss\.com/200, pearlabyss\.com/300\) \+ WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path\(namu\.wiki, ko\.wikipedia\.org\)가 context box에 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up에서 source path\(namu\.wiki, ko\.wikipedia\.org\)가 context box에 유지되고 WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반이 drift하지 않습니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 noisy single-source claim\(출시일/2025/blog\.example\.com\)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance continuity가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 noisy single-source claim\(출시일/2025/blog\.example\.com\)이 본문과 origin detail에 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance continuity가 유지됩니다" --reporter=line  # 1 passed (4.3s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update mixed-source 자연어 reload 후 follow-up에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update mixed-source 자연어 reload 후 두 번째 follow-up에서 source path\(store\.steampowered\.com, yna\.co\.kr\) \+ WEB badge, 최신 확인, 공식\+기사 교차 확인, 보조 기사 · 공식 기반이 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update single-source 자연어 reload 후 follow-up에서 source path\(example\.com/seoul-weather\) \+ WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다" --reporter=line  # 1 passed (3.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update single-source 자연어 reload 후 두 번째 follow-up에서 source path\(example\.com/seoul-weather\) \+ WEB badge, 최신 확인, 단일 출처 참고, 보조 출처가 유지됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update news-only 자연어 reload 후 follow-up에서 기사 source path\(hankyung\.com, mk\.co\.kr\) \+ WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update news-only 자연어 reload 후 두 번째 follow-up에서 기사 source path\(hankyung\.com, mk\.co\.kr\) \+ WEB badge, 최신 확인, 기사 교차 확인, 보조 기사가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update noisy community source가 자연어 reload 후 follow-up에서도 보조 커뮤니티/brunch 미노출 \+ 기사 교차 확인, 보조 기사, hankyung\.com · mk\.co\.kr 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "latest-update noisy community source가 자연어 reload 후 두 번째 follow-up에서도 보조 커뮤니티/brunch 미노출 \+ 기사 교차 확인, 보조 기사, hankyung\.com · mk\.co\.kr 유지됩니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (3.9s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "entity-card noisy single-source claim\(출시일/2025/blog\.example\.com\)이 자연어 reload 후 두 번째 follow-up에서도 미노출되고 설명형 다중 출처 합의, 백과 기반, namu\.wiki/ko\.wikipedia\.org/blog\.example\.com provenance가 유지됩니다" --reporter=line  # 1 passed (4.1s)
git diff --check -- core/agent_loop.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `python3 -m unittest -v tests.test_web_app`는 이번 라운드에 제품 코드 변경이 없었기 때문에 handoff 조건에 따라 재실행하지 않았습니다. seq 248에서 새로 추가했던 두 sqlite 서비스 회귀도 이미 같은 tree에 들어 있고 이번 라운드에는 해당 테스트 대상 코드 경로를 건드리지 않았습니다.
- `make e2e-test`, JSON-default Playwright 전체 suite, sqlite browser full suite는 이번 scope 대비 과해 실행하지 않았습니다. 이번 `/work`는 한정된 sqlite natural-reload chain bundle 24건 실측 + 4개 inventory 문서 sync 라운드였고, broader rerun이 필요할 정도로 넓은 제품 diff가 없었기 때문입니다.

## 남은 리스크

- 24-scenario sqlite natural-reload follow-up / second-follow-up chain contract는 이번 라운드에 sqlite backend로 closed. sqlite browser gate inventory는 총 103건으로 확장되었습니다. 이번 라운드에 진행된 것은 **docs 확장 자체까지 포함**되며 추가 docs-only micro-round 없이 한 번에 마감되었습니다.
- JSON-default browser test의 `sendRequest` `state.isBusy` early-return timing race는 seq 248 분석에서 드러난 bug-adjacent 문제이지만 이번 slice는 물론 sqlite 쪽에서도 이미 shipped contract에 맞게 동작하므로, handoff scope 제한(browser-wide sendRequest race cleanup 제외)에 따라 이번 라운드에도 손대지 않았습니다. 다음 browser-contract 라운드에서 `sendRequest` busy-state semantics + test scenario 구조 정리를 같이 처리하는 편이 맞습니다.
- `LOCAL_AI_WEB_SEARCH_HISTORY_DIR` 공유 정책은 이전 라운드와 동일합니다. sqlite/JSON Playwright config 동시 실행은 여전히 같은 `data/web-search/` 경로를 공유하므로 순차 실행 한정으로 안전합니다.
- 이번 라운드는 sqlite backend 실측만 했고 JSON-default path는 재실행하지 않았습니다. chain contract는 JSON-default smoke에서 이미 shipped 계약이라 회귀가 발생할 사유는 없지만, 다음 라운드 release-check가 필요한 경우 함께 재실행이 필요합니다.
- 문서 diff에는 이전 round에서 넘어온 48~79번 history-card click-reload follow-up / second-follow-up / natural-reload reload-only 행이 여전히 staged-uncommitted 상태로 섞여 있습니다. 이번 라운드 scope는 80~103번 행 추가와 baseline 문장 확장이었고, handoff dirty-worktree 지침에 따라 기존 hunks는 되돌리지 않았습니다.
