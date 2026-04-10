# history-card entity-card click-reload initial docs entity-prefix wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-click-reload-initial-docs-entity-prefix-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload initial docs 4곳의 entity-prefix wording이 current tree 기준으로 실제 반영됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 truthful한지 다시 확인해야 했습니다.
- same family click-reload docs set은 이번 `/work`로 닫혔으므로, 다음 Claude 라운드에는 인접한 docs family에서 아직 남아 있는 exact-field wording gap 1건만 남겨야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L129), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L47), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1338), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L36)에는 `/work`가 주장한 `history-card entity-card` prefix 정렬이 실제로 반영돼 있었고, 바로 아래 latest-update sibling line과 나란히 보아도 entity-card 대상임이 직접 드러납니다.
- docs-only claimed check도 truthful했습니다. `git diff -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- next slice는 `history-card entity-card zero-strong-slot click-reload initial docs response-origin exact-field wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L147), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L65), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1356), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L54)은 zero-strong-slot initial click-reload contract에서 `설명 카드`, `설명형 단일 출처`, `백과 기반`, source path만 적고 있어 `WEB` origin badge truth를 직접 드러내지 않습니다. 반면 current test title/body는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3682), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3712), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3757)에서 `WEB` badge 포함 exact-field truth를 직접 고정하므로, runtime을 건드리지 않고 docs response-origin wording만 보정하는 편이 가장 작은 다음 슬라이스입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-entity-card-click-reload-initial-docs-entity-prefix-wording-clarification.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-history-card-entity-card-click-reload-follow-up-docs-exact-field-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba README.md | sed -n '126,134p'`
- `nl -ba docs/MILESTONES.md | sed -n '44,52p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1336,1342p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '34,40p'`
- `rg -n '^test\\(\"' e2e/tests/web-smoke.spec.mjs | sed -n '1,180p'`
- `nl -ba README.md | sed -n '145,153p'`
- `nl -ba docs/MILESTONES.md | sed -n '61,69p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1354,1362p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '48,56p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3682,3770p'`
- `git diff -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- basic history-card entity-card click-reload docs family는 이번 라운드로 닫혔지만, zero-strong-slot initial docs는 아직 `WEB` origin badge truth를 직접 적지 않아 current test/body보다 설명이 한 단계 덜 정확합니다.
- 다른 browser family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
