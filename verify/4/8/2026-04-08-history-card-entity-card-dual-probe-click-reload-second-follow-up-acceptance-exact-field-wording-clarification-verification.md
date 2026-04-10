# history-card entity-card dual-probe click-reload second-follow-up acceptance exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card dual-probe click-reload second-follow-up acceptance 1줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 initial/follow-up acceptance verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1374)는 `/work` 주장대로 `response-origin exact-field drift 없음` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- dual-probe click-reload acceptance family는 initial/follow-up/second-follow-up까지 이번 라운드로 닫혔습니다. 다음 슬라이스는 `history-card entity-card actual-search click-reload initial + follow-up + second-follow-up acceptance exact-field wording clarification`으로 고정했습니다.
- 근거는 current planning/root docs/test 중 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L80), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L81), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L82), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L69), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L70), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L71), [README.md](/home/xpdlqj/code/projectH/README.md#L160), [README.md](/home/xpdlqj/code/projectH/README.md#L161), [README.md](/home/xpdlqj/code/projectH/README.md#L162), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1856), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2835), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2957)은 이미 `namu.wiki`, `ko.wikipedia.org`, `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` contract를 직접 고정하는 반면, [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1371), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1372), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)은 아직 generic `response-origin continuity` / `drift 없음` framing으로 남아 있기 때문입니다.
- initial/follow-up/second-follow-up 3줄은 same file·same family·same acceptance axis이므로, 한 번에 exact-field wording으로 정렬하는 편이 더 작은 coherent slice입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1376p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "history-card entity-card .*second-follow-up|entity-card dual-probe natural-reload second-follow-up|history-card entity-card .*actual-search|latest-update .*response-origin continuity|response-origin drift 없음" work/4/8 verify/4/8 docs/ACCEPTANCE_CRITERIA.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-source-path-truth-sync.md && echo nat2fu_truthsync_exists || echo nat2fu_truthsync_missing`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification.md && echo click2fu_acceptance_exists || echo click2fu_acceptance_missing`
- `rg -n "actual-search click-reload.*milestone|actual-search click-reload.*acceptance|history-card entity-card actual-search click-reload" work/4/8 verify/4/8`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2932,2952p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1373p'`
- `nl -ba README.md | sed -n '160,162p'`
- `test -f work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-second-follow-up-acceptance-exact-field-wording-clarification.md && echo actual_acceptance_bundle_exists || echo actual_acceptance_bundle_missing`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2818,2860p;2916,2950p;3038,3090p'`
- `nl -ba docs/MILESTONES.md | sed -n '80,82p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '69,71p'`
- `rg -n "history-card entity-card 다시 불러오기.*actual-search source path|history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search|history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search" e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current shipped acceptance lines [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1371), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1372), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)은 아직 generic wording으로 남아 있습니다.
- `entity-card dual-probe natural-reload second-follow-up` 쪽의 smoke title/body source-path wording divergence는 이번 라운드에서는 next-slice 후보 비교 근거로만 확인했고, 아직 별도 truth-sync 라운드로 닫지 않았습니다.
