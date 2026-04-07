# entity-card crimson-desert natural-reload actual-search second-follow-up browser-anchor naming clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-second-follow-up-browser-anchor-naming-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload actual-search second-follow-up browser anchor title/session naming을 source-path + response-origin continuity truth에 맞추는 test-only clarification을 보고했습니다.
- same-day latest `/verify`가 바로 직전 source-path browser-fixture truth-sync round를 닫았으므로, 이번 라운드에서는 second-follow-up naming change가 실제 tree와 맞는지, 그리고 그 결과 같은 family에서 다음 한 슬라이스를 어디까지 좁힐 수 있는지 다시 확인할 필요가 있었습니다.

## 핵심 변경
- latest `/work`를 truthful로 판정했습니다. [e2e/tests/web-smoke.spec.mjs:5045](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5045)의 test title은 now `source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다`를 직접 드러내고, [e2e/tests/web-smoke.spec.mjs:5046](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5046)의 session id도 `entity-actual-search-natural-reload-second-followup-sp-origin`으로 맞춰져 있습니다.
- `/work`의 남은 리스크 메모였던 fixture body alignment concern은 현재 tree에서 재현되지 않았습니다. [e2e/tests/web-smoke.spec.mjs:5066](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5066)과 [e2e/tests/web-smoke.spec.mjs:5073](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5073)도 이미 `설명형 다중 출처 합의`로 정렬되어 있었습니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert natural-reload follow-up-second-follow-up noisy-exclusion browser-anchor provenance wording clarification`으로 고정했습니다. root docs와 service anchors는 두 noisy-exclusion browser scenarios를 negative assertions + `blog.example.com` provenance continuity까지 분명히 적는데, current browser titles/session naming은 still generic `continuity가 유지됩니다` 수준이라 same-family에서 남은 가장 작은 wording risk가 이 축에 모여 있습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-second-follow-up-browser-anchor-naming-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-source-path-browser-fixture-truth-sync-correction-verification.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5038,5110p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5106,5255p'`
- `nl -ba tests/test_web_app.py | sed -n '17312,17405p'`
- `nl -ba README.md | sed -n '164,168p'`
- `nl -ba docs/MILESTONES.md | sed -n '77,80p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1368,1371p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '66,69p'`
- `rg -n "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up|entity-actual-search-natural-reload-second-followup|설명형 다중 출처 합의|설명형 단일 출처" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 noisy-exclusion browser anchor wording weakness입니다. [README.md:166](/home/xpdlqj/code/projectH/README.md:166), [README.md:167](/home/xpdlqj/code/projectH/README.md:167), [docs/MILESTONES.md:78](/home/xpdlqj/code/projectH/docs/MILESTONES.md:78), [docs/MILESTONES.md:79](/home/xpdlqj/code/projectH/docs/MILESTONES.md:79), [docs/ACCEPTANCE_CRITERIA.md:1369](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1369), [docs/ACCEPTANCE_CRITERIA.md:1370](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1370), [docs/TASK_BACKLOG.md:67](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:67), [docs/TASK_BACKLOG.md:68](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:68), [tests/test_web_app.py:17317](/home/xpdlqj/code/projectH/tests/test_web_app.py:17317), [tests/test_web_app.py:17376](/home/xpdlqj/code/projectH/tests/test_web_app.py:17376)는 negative `출시일`/`2025`/`blog.example.com` assertions와 provenance continuity를 직접 적습니다.
- 반면 browser anchors [e2e/tests/web-smoke.spec.mjs:5107](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5107), [e2e/tests/web-smoke.spec.mjs:5108](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5108), [e2e/tests/web-smoke.spec.mjs:5186](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5186), [e2e/tests/web-smoke.spec.mjs:5187](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5187)는 still generic `continuity가 유지됩니다` 수준이라 provenance/negative-assertion contract를 title/session naming에서 직접 드러내지 않습니다. test body 자체는 이미 해당 사실을 검사하므로, 다음 라운드는 runtime/assertion logic이나 docs를 건드리지 않는 test-only wording clarification이 가장 작고 reviewable합니다.
