# history-card latest-update noisy-community click-reload initial exclusion exact-field smoke clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-exclusion-exact-field-smoke-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update noisy-community click-reload initial smoke title/body를 exact-field exclusion + positive-retention wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 smoke change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 `.pipeline/claude_handoff.md`는 방금 닫힌 smoke slice를 아직 next slice로 가리키고 있었으므로, newer `/work` 기준으로 current truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1573)는 initial noisy-community click-reload title을 `본문, origin detail, context box` negative assertion과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 직접 드러내도록 반영하고 있었고, current body [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1678), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1692)는 same exact-field contract를 실제 assertion으로 고정하고 있었습니다.
- `/work`가 주장한 focused verification도 재현됐습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였으며, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source" --reporter=line`은 `1 passed (6.9s)`로 다시 통과했습니다.
- 다음 슬라이스는 `history-card latest-update noisy-community click-reload initial docs exact-field wording clarification`으로 고정했습니다. current initial root docs [README.md](/home/xpdlqj/code/projectH/README.md#L133), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1342), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L40)는 아직 negative exclusion만 적고 있습니다.
- 반면 current initial smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1573), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1692)와 same-family sibling docs [README.md](/home/xpdlqj/code/projectH/README.md#L182), [README.md](/home/xpdlqj/code/projectH/README.md#L183), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1392), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L96), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L89), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L90)는 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 직접 적고 있습니다. same-family current-risk reduction으로는 initial root docs 4곳을 그 exact-field wording에 맞게 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-exclusion-exact-field-smoke-clarification.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-milestone-exclusion-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1570,1700p'`
- `nl -ba README.md | sed -n '133,183p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1393p'`
- `nl -ba docs/MILESTONES.md | sed -n '51,97p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,90p'`
- `git status --short -- .pipeline/claude_handoff.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused single-scenario smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- initial noisy-community click-reload browser contract 자체는 smoke 기준으로 닫혔지만, current root docs 4곳은 아직 same-family follow-up/second-follow-up이나 current smoke title만큼 exact-field positive-retention wording을 직접 드러내지 않습니다.
- 이번 verification은 latest smoke truth와 next slice selection까지만 다뤘으므로, 다음 라운드는 runtime이나 다른 answer-mode family로 넓히지 말고 initial docs wording 4곳만 좁게 정렬하는 편이 맞습니다.
