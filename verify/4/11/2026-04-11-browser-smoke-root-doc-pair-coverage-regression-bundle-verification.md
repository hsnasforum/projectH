# browser smoke root-doc pair coverage regression bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-browser-smoke-root-doc-pair-coverage-regression-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 browser smoke docs-parity regression 을 같은 `tests/test_docs_sync.py` 안에서 확장했다고 주장했으므로, 이번에는 신규 test class 의 실제 존재, 재실행 결과, 그리고 현재 root docs 가 그 fragment contract 를 실제로 만족하는지만 좁게 다시 확인했습니다. 범위는 `tests/test_docs_sync.py`, 해당 unittest 재실행, 그리고 테스트가 읽는 root docs surface direct comparison 으로 제한했습니다.

## 핵심 변경

- 최신 `/work` 는 현재 기준 truthful 합니다. [tests/test_docs_sync.py](/home/xpdlqj/code/projectH/tests/test_docs_sync.py) 에 `ClickReloadComposerPlainFollowUpRootDocPairTest` 가 실제로 추가되어 있고, `ROOT_DOC_PATHS` 를 통해 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 5개 root docs 를 순회합니다.
- 새 regression 은 entity-card / latest-update 두 pair 각각에 대해 `history-card ...`, `plain follow-up`, `load_web_search_record_id`, `#claim-coverage-box`, `visible` 또는 `hidden` fragment set 이 같은 줄에 모두 존재하는지를 검사합니다. `/work` 가 설명한 대소문자 무시 line-scan 구현도 현재 파일과 일치합니다.
- 제가 다시 실행한 `python3 -m unittest -v tests.test_docs_sync` 는 5개 테스트 모두 `ok` 로 통과했습니다. `/work` 의 검증 섹션에 적힌 테스트 목록과 현재 재실행 결과도 일치합니다.
- direct comparison 상 현재 root docs truth 도 새 regression 과 맞습니다: [README.md:251](/home/xpdlqj/code/projectH/README.md#L251), [README.md:252](/home/xpdlqj/code/projectH/README.md#L252), [docs/ACCEPTANCE_CRITERIA.md:1473](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1473), [docs/ACCEPTANCE_CRITERIA.md:1474](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1474), [docs/MILESTONES.md:147](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L147), [docs/MILESTONES.md:148](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L148), [docs/TASK_BACKLOG.md:141](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L141), [docs/TASK_BACKLOG.md:142](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L142), [docs/NEXT_STEPS.md:23](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23) 이 모두 해당 fragment 를 만족합니다.
- 다만 현재 regression 은 "존재한다" 까지만 잠급니다. 각 root doc 에서 해당 pair line 이 정확히 한 번만 존재하는지, 즉 중복 copy/paste drift 가 없는지까지는 아직 자동으로 확인하지 않습니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n "history-card entity-card|history-card latest-update|plain follow-up|load_web_search_record_id|#claim-coverage-box" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- 이번 라운드는 focused regression 확장 검수이므로 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 하지 않았습니다.

## 남은 리스크

- same-family docs-parity regression 은 이제 count parity, anchor shape, root-doc pair presence 까지 자동 가드합니다. 하지만 현재는 `at least one matching line` 만 보므로, 특정 root doc 에 같은 pair wording 이 중복 삽입되어도 test 가 green 으로 남을 수 있습니다.
- 따라서 다음 same-family current-risk reduction 은 또 다른 docs prose round 가 아니라, 같은 `tests/test_docs_sync.py` 안에서 각 root doc / pair 조합이 정확히 한 번만 매치되도록 잠그는 bounded regression 확장으로 잡는 편이 맞습니다.
- 현재 repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 test/docs family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, 기존 다른 `/work` / `/verify` 변경은 건드리지 않았습니다.
