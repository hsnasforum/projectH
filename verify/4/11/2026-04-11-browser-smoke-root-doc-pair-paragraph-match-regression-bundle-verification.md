# browser smoke root-doc pair paragraph-match regression bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-browser-smoke-root-doc-pair-paragraph-match-regression-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 같은 `tests/test_docs_sync.py` 안에서 root-doc pair regression 의 scan unit 을 physical line 에서 paragraph block 으로 올렸다고 주장했으므로, 이번에는 helper 교체가 실제로 들어갔는지, `tests.test_docs_sync` 가 다시 green 인지, 그리고 현재 root docs 가 그 paragraph-level 계약을 실제로 만족하는지만 좁게 다시 확인했습니다. 범위는 `tests/test_docs_sync.py`, 해당 unittest 재실행, 그리고 관련 root docs surface direct comparison 으로 제한했습니다.

## 핵심 변경

- 최신 `/work` 는 현재 기준 truthful 합니다. [tests/test_docs_sync.py](/home/xpdlqj/code/projectH/tests/test_docs_sync.py) 에 `_split_into_paragraph_blocks(...)` 와 `_block_contains_all(...)` 가 실제로 추가되어 있고, `ClickReloadComposerPlainFollowUpRootDocPairTest` 의 match helper 는 paragraph block 단위로 동작합니다.
- `python3 -m unittest -v tests.test_docs_sync` 를 다시 실행한 결과 5개 테스트가 모두 `ok` 였습니다. `/work` 의 검증 섹션에 적힌 test list 와 현재 재실행 결과가 일치합니다.
- direct comparison 상 현재 root docs truth 도 paragraph-level regression 과 맞습니다. 새 click-reload composer plain follow-up pair 는 [README.md:251](/home/xpdlqj/code/projectH/README.md#L251), [README.md:252](/home/xpdlqj/code/projectH/README.md#L252), [docs/ACCEPTANCE_CRITERIA.md:1473](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1473), [docs/ACCEPTANCE_CRITERIA.md:1474](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1474), [docs/MILESTONES.md:147](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L147), [docs/MILESTONES.md:148](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L148), [docs/TASK_BACKLOG.md:141](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L141), [docs/TASK_BACKLOG.md:142](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L142), [docs/NEXT_STEPS.md:23](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23) 에 남아 있고, 현재 test pass 는 각 required root doc / pair 조합이 paragraph block 기준으로 exactly one match 를 가진다는 뜻과도 일치합니다.
- 다만 current regression 의 block boundary 는 여전히 blank line only 입니다. 그래서 heading 과 bullet 이 blank line 없이 붙거나, 같은 block 안에 pair wording 이 두 번 들어가는 구조 drift 는 아직 과하게 넓은 block 하나로 뭉개질 수 있습니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n "history-card entity-card|history-card latest-update|plain follow-up|load_web_search_record_id|#claim-coverage-box|Current smoke scenarios:|core browser scenarios" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- 이번 라운드는 focused regression robustness 검수이므로 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 하지 않았습니다.

## 남은 리스크

- same-family docs-parity regression 은 이제 count parity, anchor shape, pair presence, pair uniqueness, paragraph-level wrapping robustness 까지 자동 가드합니다. 하지만 현재 block boundary 가 blank line only 라서, markdown heading/list item 경계가 섞인 구조나 같은 block 내부 duplicate wording 은 아직 거칠게 다뤄집니다.
- 따라서 다음 same-family current-risk reduction 은 또 다른 docs prose round 가 아니라, 같은 `tests/test_docs_sync.py` 안에서 scan unit 을 lightweight markdown item block 으로 정제해 root-doc pair matching 을 더 구조적으로 만드는 bounded robustness 확장으로 잡는 편이 맞습니다.
- 현재 repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 test/docs family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, 기존 다른 `/work` / `/verify` 변경은 건드리지 않았습니다.
