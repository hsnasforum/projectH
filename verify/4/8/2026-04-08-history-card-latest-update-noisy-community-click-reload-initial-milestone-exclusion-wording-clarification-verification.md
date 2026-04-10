# history-card latest-update noisy-community click-reload initial milestone exclusion wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-milestone-exclusion-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51)의 history-card latest-update noisy-community click-reload initial milestone wording을 direct exclusion framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 noisy single-source initial milestone family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51)는 `/work` 주장대로 `보조 커뮤니티` / `brunch` negative in response body, origin detail, and context box wording으로 반영돼 있었습니다.
- current shipped root docs와의 정렬도 맞았습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L40), [README.md](/home/xpdlqj/code/projectH/README.md#L133), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1342)는 이미 same initial click-reload noisy-community exclusion truth를 직접 드러내고 있었고, current `docs/MILESTONES.md:51`도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card latest-update noisy-community click-reload initial exclusion exact-field smoke clarification`으로 고정했습니다. current initial smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1573)와 initial body [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1676), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1687)은 origin detail과 response body exclusion만 직접 검증합니다. 반면 docs는 context box exclusion까지 current shipped truth로 적고 있고, same-family follow-up/second-follow-up smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6106), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6173), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6164), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6235)는 `hankyung.com`, `mk.co.kr` positive retention과 `brunch` context box exclusion을 직접 고정합니다. same-family current-risk reduction으로는 initial click-reload scenario title/body를 그 exact-field contract에 맞게 직접화하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-milestone-exclusion-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-noisy-single-source-claim-click-reload-initial-milestone-exact-field-provenance-wording-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '46,53p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '38,42p'`
- `nl -ba README.md | sed -n '129,135p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1338,1344p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1573,1698p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6106,6240p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8 docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next slice selection까지만 다뤘으므로, initial noisy-community click-reload browser contract 자체는 다시 실행해 판정하지 않았습니다.
- current initial noisy-community click-reload smoke는 docs가 말하는 context box exclusion + positive retention truth를 title/body에서 아직 직접 고정하지 않습니다. 다음 라운드는 다른 family로 넓히지 말고, 먼저 그 initial scenario 하나를 exact-field smoke로 좁게 닫는 편이 맞습니다.
