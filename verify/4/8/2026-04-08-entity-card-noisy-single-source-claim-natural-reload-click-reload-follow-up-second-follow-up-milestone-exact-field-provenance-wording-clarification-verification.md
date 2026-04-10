# entity-card noisy single-source claim natural-reload + click-reload follow-up-second-follow-up milestone exact-field provenance wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-click-reload-follow-up-second-follow-up-milestone-exact-field-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L97)의 entity-card noisy single-source claim natural-reload + click-reload follow-up/second-follow-up combined milestone wording을 exact-field provenance retention framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 history-card latest-update noisy-community click-reload family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L97)는 `/work` 주장대로 `출시일`, `2025`, `blog.example.com` 본문/detail 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, source_paths/context box의 `blog.example.com` provenance 포함을 직접 드러내는 wording으로 반영돼 있었습니다.
- current shipped docs와 smoke 계약선과의 정렬도 맞았습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L91), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L92), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L93), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L94), [README.md](/home/xpdlqj/code/projectH/README.md#L184), [README.md](/home/xpdlqj/code/projectH/README.md#L185), [README.md](/home/xpdlqj/code/projectH/README.md#L186), [README.md](/home/xpdlqj/code/projectH/README.md#L187), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1393), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1395), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1396), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6244), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6317), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6393), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6462)는 이미 same-family follow-up/second-follow-up exclusion + provenance retention truth를 직접 고정하고 있었고, current `docs/MILESTONES.md:97`도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card entity-card noisy single-source claim click-reload initial milestone exact-field provenance wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52)는 아직 `negative assertions ... positive assertions ... provenance` 형태의 generic framing으로 남아 있습니다. 반면 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L41), [README.md](/home/xpdlqj/code/projectH/README.md#L134), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1343), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1701)는 history-card entity-card click-reload initial noisy single-source contract를 `(출시일/2025/blog.example.com) 미노출 + 설명형 다중 출처 합의, 백과 기반, agreement-backed 사실 카드, namu.wiki/ko.wikipedia.org/blog.example.com provenance 유지`라는 direct exact-field wording으로 이미 고정합니다. same-family current-risk reduction으로는 `docs/MILESTONES.md:52`만 좁게 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-click-reload-follow-up-second-follow-up-milestone-exact-field-provenance-wording-clarification.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-follow-up-second-follow-up-milestone-exclusion-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '95,104p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,100p'`
- `nl -ba README.md | sed -n '182,193p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1403p'`
- `rg -n "zero-strong-slot|strong slot|no strong slot|single-source claim|noisy single-source" e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/MILESTONES.md | sed -n '44,76p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,59p'`
- `nl -ba README.md | sed -n '133,152p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1360p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1688,1715p'`
- `git status --short`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- current noisy single-source claim family에서는 follow-up/second-follow-up milestone combined line이 닫혔고, initial click-reload milestone line만 generic exact-field framing으로 남아 있습니다. 다음 라운드는 runtime이나 다른 answer-mode family로 넓히지 말고, 먼저 `docs/MILESTONES.md:52`를 current shipped truth에 맞게 직접화하는 편이 맞습니다.
