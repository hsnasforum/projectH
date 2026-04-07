## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-dual-probe-source-path-continuity-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-dual-probe-source-path-continuity-smoke-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 아직 직전 entity-card noisy-source exclusion 라운드(`verify/4/7/2026-04-07-history-card-entity-card-noisy-source-exclusion-smoke-tightening-verification.md`)를 가리키고 있어, 이번 entity-card dual-probe source-path continuity 라운드 기준의 새 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 Playwright 추가와 문서 동기화 주장은 current tree와 일치합니다. `e2e/tests/web-smoke.spec.mjs:1840-1949`에는 entity-card history-card reload 뒤 `#context-box`에 dual-probe source path 두 개가 유지되는지 검증하는 시나리오가 실제로 있고, `README.md:135`, `docs/ACCEPTANCE_CRITERIA.md:1344`, `docs/MILESTONES.md:53`, `docs/TASK_BACKLOG.md:42`, `docs/NEXT_STEPS.md:16`도 scenario 23 기준으로 맞춰져 있습니다. `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `23`이었고, `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 격리 재실행도 다시 통과했습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다" --reporter=line` 결과는 `1 passed (6.3s)`였습니다.
- 다음 exact slice는 `history-card latest-update mixed-source source-path continuity smoke tightening`으로 고정했습니다. same history-card reload family에서 latest-update 경로는 현재 `e2e/tests/web-smoke.spec.mjs:1222-1330`의 reload origin badge continuity, `e2e/tests/web-smoke.spec.mjs:1449-1571`의 follow-up continuity, `e2e/tests/web-smoke.spec.mjs:1573-1699`의 noisy-source exclusion까지만 잠겨 있고, `#context-box`의 `출처:` 줄은 아직 직접 검증하지 않습니다. 반면 UI는 `app/static/app.js:2397-2405`에서 `active_context.source_paths`를 `#context-box`에 렌더링하고, reload 경로는 `core/agent_loop.py:5453-5568`에서 `source_paths`를 구성한 뒤 `core/agent_loop.py:6308-6364`에서 history-card reload 시 `active_context`로 다시 노출합니다. 또한 latest-update service regression은 `tests/test_web_app.py:8155-8445`에서 mixed-source reload exact field continuity를 이미 잠그고 있습니다. 따라서 같은 family의 다음 current-risk reduction으로는 mixed-source latest-update record reload 뒤 `store.steampowered.com`과 `yna.co.kr` source path가 `#context-box`에 유지되는지 브라우저 smoke로 1건 더 잠그는 편이 가장 좁고 직접적입니다. 이 마지막 판단은 current tree와 existing coverage gap을 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-entity-card-dual-probe-source-path-continuity-smoke-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-noisy-source-exclusion-smoke-tightening-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `ls -lt work/4/7 verify/4/7`
- `git status --short`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n "23 browser scenarios|scenario 23|dual-probe source-path continuity|source path가 context box|pearlabyss.com/200|pearlabyss.com/300|history-card entity-card" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py app/static/app.js`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1696,1905p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `23`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.3s)`
- `rg -n "source_paths|dual probe|latest_update.*source_paths|latest_update.*reload.*source|actual_latest|latest_update.*active_context|load_web_search_record_id.*source_paths" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba tests/test_web_app.py | sed -n '8155,8445p'`
- `nl -ba tests/test_web_app.py | sed -n '8508,8750p'`
- `nl -ba tests/test_web_app.py | sed -n '5600,5735p'`
- `nl -ba core/agent_loop.py | sed -n '5450,5575p'`
- `nl -ba core/agent_loop.py | sed -n '6304,6368p'`
- `nl -ba app/static/app.js | sed -n '2396,2405p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1216,1585p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1838,1975p'`
- `rg -n "source_paths|출처:|context-box" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py app/static/app.js`

## 남은 리스크
- latest `/work`는 truthful하게 닫혔지만, history-card latest-update mixed-source reload 경로의 source-path continuity는 아직 브라우저 smoke로 잠겨 있지 않습니다.
- unrelated dirty worktree가 여전히 큽니다. 이번 verification은 latest `/work` truth와 다음 slice 고정에 필요한 파일만 다시 확인했습니다.
- `make e2e-test`와 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 Playwright-only smoke tightening과 문서 count 동기화 범위였고, shared browser helper 변경도 없었습니다.
