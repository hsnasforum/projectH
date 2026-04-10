# history-card latest-update noisy-community click-reload follow-up-second-follow-up milestone exclusion wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-follow-up-second-follow-up-milestone-exclusion-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L96)의 history-card latest-update noisy-community click-reload follow-up/second-follow-up combined milestone wording을 generic `negative assertion with ... positive assertion` framing에서 exact exclusion wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 latest-update noisy-community natural-reload family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L96)는 `/work` 주장대로 `negative in origin detail, response body, context box + ... positive retention` wording으로 반영돼 있었고, history-card latest-update noisy-community click-reload follow-up/second-follow-up milestone clarification이 실제 tree에 남아 있었습니다.
- current shipped docs와 smoke 계약선과의 정렬도 맞았습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L89), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L90), [README.md](/home/xpdlqj/code/projectH/README.md#L182), [README.md](/home/xpdlqj/code/projectH/README.md#L183), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1392), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6106), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6173)는 이미 origin detail, response body, context box에서 `보조 커뮤니티`, `brunch`를 배제하고 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`만 유지하는 exclusion contract를 직접 드러내고 있었고, current `docs/MILESTONES.md:96`도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `entity-card noisy single-source claim natural-reload + click-reload follow-up-second-follow-up milestone exact-field provenance wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L97)는 natural-reload와 click-reload follow-up/second-follow-up 4개 케이스를 한 줄의 compressed provenance truth-sync wording으로 묶고 있습니다. 반면 current [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L91), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L92), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L93), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L94), [README.md](/home/xpdlqj/code/projectH/README.md#L184), [README.md](/home/xpdlqj/code/projectH/README.md#L185), [README.md](/home/xpdlqj/code/projectH/README.md#L186), [README.md](/home/xpdlqj/code/projectH/README.md#L187), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1393), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1395), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1396), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6244), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6317), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6393), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6462)는 exact-field exclusion과 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance retention을 더 직접적으로 드러냅니다. current `MILESTONES`가 이 family를 한 줄로 묶고 있으므로, 다음 smallest coherent slice는 `docs/MILESTONES.md:97` combined line만 좁게 정렬하는 것입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-follow-up-second-follow-up-milestone-exclusion-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-milestone-exclusion-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '95,101p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,96p'`
- `nl -ba README.md | sed -n '182,189p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1398p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6106,6325p'`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-follow-up-second-follow-up-exact-field-provenance-wording-clarification.md`
- `sed -n '1,240p' work/4/8/2026-04-08-history-card-entity-card-noisy-single-source-claim-click-reload-follow-up-second-follow-up-exact-field-provenance-wording-clarification.md`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- entity-card noisy single-source claim family planning docs에는 `docs/MILESTONES.md:97` combined line만 current root docs/test보다 압축된 provenance truth-sync wording으로 남아 있습니다. 다음 라운드는 runtime이나 다른 answer-mode family로 넓히지 말고, 먼저 그 combined line을 current shipped truth에 맞게 직접화하는 편이 맞습니다.
