# browser smoke inventory docs parity regression bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-browser-smoke-inventory-docs-parity-regression-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 browser smoke inventory family 의 focused regression 추가 라운드라고 주장했으므로, 이번에는 docs-only 비교에 머물지 않고 실제 신규 regression 모듈과 그 실행 결과가 현재 루트 docs truth 를 제대로 잠그는지 좁게 다시 확인했습니다. 범위는 `tests/test_docs_sync.py`, 그 unittest 재실행, 그리고 테스트가 참조하는 root docs surface direct comparison 으로 제한했습니다.

## 핵심 변경

- 최신 `/work` 는 현재 기준 truthful 합니다. `tests/test_docs_sync.py` 가 실제로 존재하고, browser smoke inventory docs parity 를 세 가지로 잠급니다:
  - `docs/ACCEPTANCE_CRITERIA.md` 와 `docs/NEXT_STEPS.md` 의 `125 core browser scenarios` count 일치
  - `README.md` `Current smoke scenarios:` 번호 목록의 마지막 번호가 같은 inventory count 로 닫히는지 확인
  - `docs/NEXT_STEPS.md` 가 `docs/ACCEPTANCE_CRITERIA.md:<line>` 형태의 brittle line anchor 를 쓰지 않는지 확인
- 제가 다시 실행한 `python3 -m unittest -v tests.test_docs_sync` 는 3개 테스트 모두 `ok` 로 통과했습니다. `/work` 에 적힌 테스트 이름과 결과 요약도 현재 재실행 결과와 일치합니다.
- direct file comparison 상 현재 root docs truth 도 테스트와 맞습니다: [docs/ACCEPTANCE_CRITERIA.md:1352](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352) 와 [docs/NEXT_STEPS.md:23](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23) 가 모두 `125 core browser scenarios` 를 가리키고, [README.md:251](/home/xpdlqj/code/projectH/README.md#L251) 와 [README.md:252](/home/xpdlqj/code/projectH/README.md#L252), [docs/MILESTONES.md:147](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L147) 와 [docs/MILESTONES.md:148](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L148), [docs/TASK_BACKLOG.md:141](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L141) 와 [docs/TASK_BACKLOG.md:142](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L142) 에 새 click-reload composer plain-follow-up pair 가 그대로 남아 있습니다.
- 다만 현재 regression 범위는 count/README closure/NEXT_STEPS anchor 까지만 잠급니다. 방금 확인한 root-doc pair surfaces 자체는 아직 `tests/test_docs_sync.py` 가 직접 보호하지 않습니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
- `rg -n "Playwright smoke covers 125 core browser scenarios|Playwright smoke currently covers 125 core browser scenarios|Current smoke scenarios:|docs/ACCEPTANCE_CRITERIA\\.md:\\d+" README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
- `rg -n "plain follow-up|load_web_search_record_id|history-card entity-card|history-card latest-update" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '247,252p'`
- `nl -ba docs/MILESTONES.md | sed -n '144,150p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '137,143p'`
- 이번 라운드는 focused regression 추가 검수이므로 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 하지 않았습니다.

## 남은 리스크

- same-family docs drift 의 재발 방지는 일부 닫혔지만 아직 완전하지 않습니다. 현재 `tests/test_docs_sync.py` 는 count parity 와 NEXT_STEPS anchor shape 만 보호하고, 새 click-reload composer plain-follow-up pair 가 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 에 계속 남아 있는지는 자동으로 검출하지 않습니다.
- 따라서 다음 current-risk reduction 은 또 다른 docs prose 수정이 아니라, 같은 `tests/test_docs_sync.py` 안에서 root-doc pair coverage 를 잠그는 bounded regression 확장이어야 합니다.
- 현재 repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 test/docs family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, 기존 다른 `/work` / `/verify` 변경은 건드리지 않았습니다.
