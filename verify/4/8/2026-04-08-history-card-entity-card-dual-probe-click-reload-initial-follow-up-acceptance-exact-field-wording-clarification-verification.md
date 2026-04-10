# history-card entity-card dual-probe click-reload initial + follow-up acceptance exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card dual-probe click-reload initial/follow-up acceptance 2줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 follow-up planning verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1344), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352)는 모두 `/work` 주장대로 dual-probe source path와 response-origin exact-field drift wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card entity-card dual-probe click-reload second-follow-up acceptance exact-field wording clarification`으로 고정했습니다.
- 근거는 current planning/docs/test 중 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L83), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L72), [README.md](/home/xpdlqj/code/projectH/README.md#L163), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3081)은 이미 `pearlabyss.com/200`, `pearlabyss.com/300`, `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` exact-field contract를 직접 고정하는 반면, [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1374)는 아직 generic `response-origin drift 없음` framing으로 남아 있기 때문입니다.
- second-follow-up click-reload acceptance 한 줄은 same-family current-risk reduction이고, current click-reload dual-probe docs family에서 남은 가장 작은 acceptance drift입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-follow-up-acceptance-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-milestone-backlog-response-origin-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1354p;1372,1376p'`
- `nl -ba README.md | sed -n '133,145p;161,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '51,53p;61,61p;82,84p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,42p;50,50p;71,73p'`
- `rg -n "dual-probe|설명형 다중 출처 합의|pearlabyss.com/200|pearlabyss.com/300" docs/ACCEPTANCE_CRITERIA.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/MILESTONES.md | sed -n '82,84p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '71,73p'`
- `nl -ba README.md | sed -n '163,164p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3074,3092p;4800,4818p'`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification.md && echo click_second_acceptance_exists || echo click_second_acceptance_missing`
- `test -f work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification.md && echo natural_second_acceptance_exists || echo natural_second_acceptance_missing`
- `rg -n "natural-reload second-follow-up|docs browser-prefix|ko-KR/Board/Detail\\?_boardNo=200|pearlabyss.com/200, pearlabyss.com/300" work/4/8 verify/4/8`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1376p'`
- `nl -ba README.md | sed -n '164,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '84,84p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '73,73p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4470,4495p;4725,4750p;4798,4815p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4807,4865p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4865,4895p'`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current shipped acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1374)는 아직 generic wording으로 남아 있습니다.
- `entity-card dual-probe natural-reload second-follow-up` 쪽은 smoke title과 body/source-path wording이 완전히 동일하지 않지만, 이번 라운드에서는 latest `/work` truth와 next slice selection까지만 다뤘습니다.
