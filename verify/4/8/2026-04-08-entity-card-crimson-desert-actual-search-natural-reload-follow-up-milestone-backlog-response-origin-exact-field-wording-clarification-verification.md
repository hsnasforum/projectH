# entity-card crimson-desert actual-search natural-reload follow-up milestone/backlog response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L75), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L64)의 crimson-desert actual-search natural-reload follow-up planning-doc wording을 current root docs에 더 가깝게 맞췄다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 latest same-day `/verify`보다 newer한 `/work`가 하나 더 생겼으므로, current planning-doc truth를 다시 맞추고 next single slice를 새로 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L75)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L64)는 `namu.wiki` / `ko.wikipedia.org` source-path와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` exact-field drift-prevention을 함께 드러내고 있어, `/work`가 주장한 follow-up wording clarification이 실제 tree에 반영돼 있었습니다.
- current root docs와의 정렬도 맞았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L157), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1366), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4872) 기준으로 봐도 same crimson-desert actual-search natural-reload follow-up contract는 current tree에서 어긋나지 않았습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- current crimson-desert natural-reload planning-doc family는 이번 wording clarification까지 포함하면 follow-up/second-follow-up axis에서 더 이상 뚜렷한 milestone/backlog drift가 보이지 않았습니다. 다음 슬라이스는 adjacent docs-truth risk인 `entity-card dual-probe natural-reload follow-up milestone/backlog response-origin exact-field wording clarification`으로 고정했습니다. current [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L63)는 아직 `response-origin truth-sync`라고 적고 있지만, [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L74), [README.md](/home/xpdlqj/code/projectH/README.md#L156), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1365), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4737)는 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention을 더 직접적으로 드러내고 있습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-second-follow-up-milestone-backlog-source-path-wording-clarification-verification.md`
- `sed -n '1,260p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '72,88p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,76p'`
- `nl -ba README.md | sed -n '154,168p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1378p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,4876p;5043,5051p'`
- `rg -n "response-origin continuity|response-origin truth-sync|truth-sync|source-path plurality|source-path \\+ response-origin" docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- `ls -1t work/4/8`
- `ls -1t verify/4/8`
- `nl -ba docs/MILESTONES.md | sed -n '70,76p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,64p'`
- `nl -ba README.md | sed -n '152,156p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1365p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4737,4744p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short`
- `git status --short docs/MILESTONES.md docs/TASK_BACKLOG.md .pipeline/claude_handoff.md verify/4/8`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- planning-doc wording family에는 아직 generic `continuity` 또는 `truth-sync` 표현이 다른 scenario들에 남아 있습니다. 다만 이번 라운드에서는 current crimson-desert natural-reload axis보다 더 직접적인 adjacent mismatch인 dual-probe follow-up milestone/backlog line부터 좁게 다루는 편이 맞습니다.
