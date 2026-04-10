# entity-card crimson-desert natural-reload initial docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [README.md](/home/xpdlqj/code/projectH/README.md#L152), [README.md](/home/xpdlqj/code/projectH/README.md#L158), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)의 entity-card crimson-desert natural-reload initial docs wording을 compact exact-field/source-path pattern으로 맞췄다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 `/work` closeout 전체가 truthful한지 판정하고, same crimson-desert natural-reload family 안에서 다음 한 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 docs change 자체는 truthful했습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L152), [README.md](/home/xpdlqj/code/projectH/README.md#L158), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)에 `/work`가 주장한 compact wording이 실제로 반영돼 있었습니다.
- `/work`가 주장한 docs-only check도 truthful했습니다. `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- 다만 `/work` closeout 전체는 fully truthful하지 않았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L157), [README.md](/home/xpdlqj/code/projectH/README.md#L159), [README.md](/home/xpdlqj/code/projectH/README.md#L165), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1366), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1368), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)은 current actual-search natural-reload follow-up/second-follow-up contract를 적고 있지만, current browser smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4872), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4992), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5047)처럼 compact source-path/response-origin wording을 직접 드러내지 않습니다. 따라서 `/work`의 `crimson-desert natural-reload docs 전체(initial + follow-up + second-follow-up)가 모두 compact exact-field로 닫혔다`는 판단은 current tree 기준으로 과장입니다.
- 다음 슬라이스는 `entity-card crimson-desert actual-search natural-reload follow-up + second-follow-up docs exact-field wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L157), [README.md](/home/xpdlqj/code/projectH/README.md#L159), [README.md](/home/xpdlqj/code/projectH/README.md#L165), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1366), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1368), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)을 한 번에 맞추면, same actual-search natural-reload follow-up/second-follow-up scenario의 source-path와 response-origin wording을 하나의 coherent docs-only slice로 정렬할 수 있습니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-docs-exact-field-wording-clarification-verification.md`
- `nl -ba README.md | sed -n '152,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1376p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4238,4322p;4928,5052p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,86p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,76p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,220p'`
- `rg -n '붉은사막 actual-search|붉은사막 검색 결과|source path\\(namu\\.wiki, ko\\.wikipedia\\.org\\)|WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs | sed -n '1,220p'`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git status --short`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- initial docs 4줄 change 자체는 닫혔지만, same crimson-desert natural-reload family의 actual-search follow-up/second-follow-up docs [README.md](/home/xpdlqj/code/projectH/README.md#L157), [README.md](/home/xpdlqj/code/projectH/README.md#L159), [README.md](/home/xpdlqj/code/projectH/README.md#L165), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1366), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1368), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)은 아직 current test title 수준의 compact source-path/response-origin wording으로 정렬되지 않았습니다.
- 이번 verification은 docs-only 범위였으므로 browser rerun이나 broader end-to-end health는 다시 판정하지 않았습니다.
