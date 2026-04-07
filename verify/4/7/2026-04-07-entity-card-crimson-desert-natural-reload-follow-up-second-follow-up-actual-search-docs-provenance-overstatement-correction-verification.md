# entity-card crimson-desert natural-reload follow-up/second-follow-up actual-search docs provenance overstatement correction verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-provenance-overstatement-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload follow-up/second-follow-up actual-search docs에서 `blog.example.com` provenance overstatement를 걷어내고, same-family docs truth-sync가 completion 상태라고 주장했습니다. 이번 라운드에서는 그 docs-only correction이 current browser/service anchors와 실제로 맞는지 다시 확인할 필요가 있었습니다.
- rerun 결과 [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)이 now actual-search continuity truth인 `namu.wiki`, `ko.wikipedia.org`만 직접 가리키고, `blog.example.com` provenance는 noisy-exclusion line에만 남습니다.
- 그 정리는 dedicated actual-search anchors인 [e2e/tests/web-smoke.spec.mjs:4870](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4870), [e2e/tests/web-smoke.spec.mjs:5045](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5045), [tests/test_web_app.py:16443](/home/xpdlqj/code/projectH/tests/test_web_app.py:16443), [tests/test_web_app.py:16582](/home/xpdlqj/code/projectH/tests/test_web_app.py:16582)와 맞고, `blog.example.com` provenance continuity가 noisy-exclusion family인 [e2e/tests/web-smoke.spec.mjs:5107](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5107), [e2e/tests/web-smoke.spec.mjs:5186](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5186), [tests/test_web_app.py:17275](/home/xpdlqj/code/projectH/tests/test_web_app.py:17275), [tests/test_web_app.py:17332](/home/xpdlqj/code/projectH/tests/test_web_app.py:17332)에만 직접 잠겨 있는 구조와도 일치했습니다.

## 핵심 변경
- latest `/work`를 truthful로 판정했습니다. docs-only correction과 `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs = 75`, `git diff --check` clean 주장은 current tree와 일치했습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up-second-follow-up actual-search docs wording clarification`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-provenance-overstatement-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-natural-reload-follow-up-second-follow-up-source-path-plurality-truth-sync-completion-verification.md`
- `git diff --check -- README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '150,170p'`
- `nl -ba docs/MILESTONES.md | sed -n '68,88p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1358,1380p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '56,78p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n "entity-card 붉은사막|blog\\.example\\.com|actual-search|source-path plurality|second-follow-up" docs/NEXT_STEPS.md`
- `rg -n "entity-card 붉은사막|actual-search|noisy single-source|source-path plurality|response-origin continuity|natural-reload" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -n "붉은사막 자연어 reload 후 follow-up에서 source path|붉은사막 자연어 reload 후 두 번째 follow-up에서 source path|browser natural-reload follow-up source-path plurality|natural-reload second-follow-up source-path \\+ response-origin" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -o "entity-card 붉은사막[^,]*|actual-search[^,]*|source-path plurality[^,]*|blog\\.example\\.com provenance[^,]*" docs/NEXT_STEPS.md`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,5195p'`
- `rg -n "test_handle_chat_.*actual.*nat|test_handle_chat_.*entity_card_.*follow_up|test_handle_chat_.*second_follow_up|actual-nat-2fu-session|entity-noisy-nat-fu-session|entity-noisy-nat-2fu-session" tests/test_web_app.py`
- `nl -ba tests/test_web_app.py | sed -n '16435,17345p'`
- `git status --short README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md .pipeline/claude_handoff.md`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- same-family current-risk는 crimson natural-reload follow-up/second-follow-up continuity lines가 현재 docs에서 여전히 generic하게 보이는 점입니다. [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)은 now two-source truth를 적고 있지만, same section의 noisy-exclusion lines와 구분되는 `actual-search` naming을 직접 쓰지 않습니다.
- 반면 dedicated browser/service anchors는 [e2e/tests/web-smoke.spec.mjs:4871](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4871), [tests/test_web_app.py:16443](/home/xpdlqj/code/projectH/tests/test_web_app.py:16443), [tests/test_web_app.py:16582](/home/xpdlqj/code/projectH/tests/test_web_app.py:16582)처럼 actual-search branch를 명시합니다. 따라서 다음 라운드는 runtime/tests를 건드리지 않고 crimson natural-reload follow-up/second-follow-up docs wording에 `actual-search` qualifier를 넣어 same-family reading ambiguity를 줄이는 docs-only clarification이 가장 작고 reviewable합니다.
