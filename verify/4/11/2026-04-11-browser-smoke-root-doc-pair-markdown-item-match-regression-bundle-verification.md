# browser smoke root-doc pair markdown-item-match regression bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-browser-smoke-root-doc-pair-markdown-item-match-regression-bundle-verification.md`
- `.pipeline/operator_request.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 같은 `tests/test_docs_sync.py` 안에서 root-doc pair regression 의 scan unit 을 paragraph block 에서 lightweight markdown item 으로 올렸다고 주장했으므로, 이번에는 helper 교체가 실제로 들어갔는지, `tests.test_docs_sync` 가 다시 green 인지, 그리고 현재 root docs 가 그 tighter matcher 를 실제로 통과하는지만 좁게 다시 확인했습니다. 범위는 `tests/test_docs_sync.py`, 해당 unittest 재실행, root-doc fragment direct comparison, whitespace check 로 제한했습니다.

## 핵심 변경

- 최신 `/work` 는 현재 기준 truthful 합니다. `tests/test_docs_sync.py` 에 `_MARKDOWN_ITEM_START_PATTERN`, `_MARKDOWN_HEADING_PATTERN`, `_split_into_markdown_items(...)`, `_item_contains_all(...)` 가 실제로 들어가 있고, `ClickReloadComposerPlainFollowUpRootDocPairTest` 는 paragraph block 이 아니라 lightweight markdown item 단위로 pair uniqueness 를 검사합니다.
- `python3 -m unittest -v tests.test_docs_sync` 를 다시 실행한 결과 5개 테스트가 모두 `ok` 였고, `Ran 5 tests in 0.025s`, `OK` 로 끝났습니다. `/work` 의 검증 섹션에 적힌 재실행 주장과 현재 결과가 일치합니다.
- direct comparison 상 현재 root docs truth 도 tighter matcher 와 맞습니다. `rg` 재확인 결과 click-reload composer plain follow-up pair 와 smoke inventory fragment 들은 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 에 계속 남아 있고, 현재 green test 결과는 required root doc / pair 조합마다 markdown item 기준 exactly one match 가 유지된다는 뜻과도 일치합니다.
- 이번 round 에서 `/work` 가 주장한 범위 밖 변경은 보이지 않았습니다. docs body, browser/runtime code, Playwright spec, pipeline 구현은 건드리지 않은 tests-only regression tightening round 로 보는 것이 맞습니다.
- same-family docs-parity regression 은 이제 inventory count parity, stable acceptance reference shape, pair presence, pair uniqueness, line-wrapping robustness, adjacent markdown item boundary risk 까지 자동 가드합니다. 여기서 더 가면 fenced code, block quote, HTML 같은 markdown container edge case hardening 으로 넘어가는데, 그것은 현재 shipped contract 보다 test-helper completeness 쪽 성격이 더 강합니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n "history-card entity-card|history-card latest-update|plain follow-up|load_web_search_record_id|#claim-coverage-box|Current smoke scenarios:|core browser scenarios" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- 이번 라운드는 focused docs-sync regression verify 이므로 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 하지 않았습니다.

## 남은 리스크

- `_split_into_markdown_items(...)` 는 intentionally lightweight heuristic 이라 fenced code, block quote, HTML block, inline marker edge case 는 다루지 않습니다. 다만 이것은 현재 shipped root-doc pair truth 를 다시 깨뜨린 사실이 아니라, 더 깊은 matcher completeness 범주입니다.
- 같은 날 same-family docs-only/test-only truth-sync round 가 이미 여러 번 반복되었으므로, 이번 verify 라운드에서는 또 다른 narrower docs-sync micro-slice 를 자동 선택하지 않았습니다. 다음 자동화 재개 전에는 더 넓은 bundle hardening 을 계속할지, 아니면 현재 document-first MVP 에서 더 직접적인 user-visible/current-risk slice 로 옮길지 operator 결정이 필요합니다.
- repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 docs-sync regression family 와 next control slot 만 다뤘고, 다른 미완 변경은 건드리지 않았습니다.
