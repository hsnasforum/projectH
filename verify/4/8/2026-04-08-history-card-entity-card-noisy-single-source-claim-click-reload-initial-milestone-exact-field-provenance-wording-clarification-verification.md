# history-card entity-card noisy single-source claim click-reload initial milestone exact-field provenance wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-noisy-single-source-claim-click-reload-initial-milestone-exact-field-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52)의 history-card entity-card noisy single-source claim click-reload initial milestone wording을 exact-field provenance framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 noisy single-source claim follow-up/second-follow-up milestone family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52)는 `/work` 주장대로 `설명형 다중 출처 합의`, `백과 기반`, negative `출시일` / `2025` / `blog.example.com` in response body and origin detail, positive agreement-backed fact card, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance in context box/source_paths` wording으로 반영돼 있었습니다.
- current shipped docs와 smoke 계약선과의 정렬도 맞았습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L41), [README.md](/home/xpdlqj/code/projectH/README.md#L134), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1343), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1701)는 already same initial click-reload noisy single-source exclusion + provenance truth를 직접 드러내고 있었고, current `docs/MILESTONES.md:52`도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card latest-update noisy-community click-reload initial milestone exclusion wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51)는 아직 `noisy community source exclusion browser smoke covering negative assertions for ...` 형태의 generic framing으로 남아 있습니다. 반면 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L40), [README.md](/home/xpdlqj/code/projectH/README.md#L133), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1342)는 `보조 커뮤니티`, `brunch`의 본문/origin detail/context box 미노출을 더 직접적으로 적고 있고, current smoke initial scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1573)와 본문 검증 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1676)도 same initial click-reload noisy-community exclusion path를 직접 고정합니다. same docs-only milestone family에서 남은 smallest coherent slice는 `docs/MILESTONES.md:51` 한 줄만 좁게 정렬하는 것입니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-noisy-single-source-claim-click-reload-initial-milestone-exact-field-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-click-reload-follow-up-second-follow-up-milestone-exact-field-provenance-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '50,53p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,42p'`
- `nl -ba README.md | sed -n '133,135p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1344p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1573,1698p'`
- `git status --short`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- current MILESTONES initial latest-update noisy-community line만 generic exclusion framing으로 남아 있습니다. 다음 라운드는 runtime이나 다른 answer-mode family로 넓히지 말고, 먼저 `docs/MILESTONES.md:51`를 current root docs wording에 맞게 직접화하는 편이 맞습니다.
