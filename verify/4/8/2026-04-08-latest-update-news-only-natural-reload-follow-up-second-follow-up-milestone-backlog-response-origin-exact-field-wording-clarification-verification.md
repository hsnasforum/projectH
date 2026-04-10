# latest-update news-only natural-reload follow-up-second-follow-up milestone/backlog response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L94), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L86)의 latest-update news-only natural-reload follow-up/second-follow-up planning-doc wording을 response-origin exact-field drift-prevention framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 latest same-day `/verify`는 직전 single-source natural-reload family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L94)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L86)는 모두 `source-path + response-origin exact-field drift-prevention` wording으로 반영돼 있었고, `/work`가 주장한 latest-update news-only natural-reload follow-up/second-follow-up planning-doc clarification이 실제 tree에 남아 있었습니다.
- current root docs와 test wording과의 정렬도 맞았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L178), [README.md](/home/xpdlqj/code/projectH/README.md#L179), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1387), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1388), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5833), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5897)는 기사 source path 유지와 `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사` drift-prevention contract를 직접 드러내고 있었고, current planning docs도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `latest-update noisy-community natural-reload follow-up-second-follow-up milestone wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L95)는 아직 generic `exclusion service + browser smoke covering ... negative assertion with ... positive assertion` framing으로 남아 있습니다. 반면 current [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L87)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L88), [README.md](/home/xpdlqj/code/projectH/README.md#L180), [README.md](/home/xpdlqj/code/projectH/README.md#L181), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1389), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1390), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5965), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6034)는 origin detail, response body, context box에서 `보조 커뮤니티`와 `brunch`를 배제하고 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지하는 exclusion contract를 더 직접적으로 드러냅니다. current `TASK_BACKLOG`가 이미 같은 shipped truth를 더 직접적으로 표현하고 있으므로, 다음 smallest coherent slice는 `MILESTONES` combined line만 좁게 정렬하는 것입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-latest-update-single-source-natural-reload-follow-up-second-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '93,97p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '83,90p'`
- `nl -ba README.md | sed -n '176,184p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1385,1394p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5707,6098p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- latest-update noisy-community natural-reload planning docs에는 `MILESTONES` combined line만 generic exclusion framing이 남아 있습니다. 다음 라운드는 runtime이나 click-reload family로 넓히지 말고, 먼저 그 combined line을 current shipped truth에 맞게 직접화하는 편이 맞습니다.
