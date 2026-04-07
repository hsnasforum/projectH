## 변경 파일
- `verify/4/7/2026-04-07-history-card-latest-update-mixed-source-source-path-continuity-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-latest-update-mixed-source-source-path-continuity-smoke-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 아직 직전 entity-card dual-probe source-path continuity 라운드(`verify/4/7/2026-04-07-history-card-entity-card-dual-probe-source-path-continuity-smoke-tightening-verification.md`)를 가리키고 있어, 이번 latest-update mixed-source source-path continuity 라운드 기준의 새 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 Playwright 추가와 문서 동기화 주장은 current tree와 일치합니다. `e2e/tests/web-smoke.spec.mjs:1951-2052`에는 latest-update history-card reload 뒤 `#context-box`에 mixed-source source path 두 개가 유지되는지 검증하는 시나리오가 실제로 있고, `README.md:136`, `docs/ACCEPTANCE_CRITERIA.md:1345`, `docs/MILESTONES.md:54`, `docs/TASK_BACKLOG.md:43`, `docs/NEXT_STEPS.md:16`도 scenario 24 기준으로 맞춰져 있습니다. `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `24`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 격리 재실행도 다시 통과했습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 mixed-source source path가 context box에 유지됩니다" --reporter=line` 결과는 `1 passed (6.3s)`였습니다.
- 다음 exact slice는 `history-card latest-update single-source verification-label continuity smoke tightening`으로 고정했습니다. same history-card reload family에서 current e2e는 latest-update reload를 `공식+기사 교차 확인` + `보조 기사` · `공식 기반` mixed-source path로만 잠그고 있습니다(`e2e/tests/web-smoke.spec.mjs:1222-1330`, `1449-1571`, `1573-1699`, `1951-2052`). 반면 single-source latest-update reload에서 `단일 출처 참고` verification label과 `보조 출처` source role이 유지되는 브라우저 contract는 아직 없습니다. service 쪽은 이미 `tests/test_web_app.py:8233-8299`, `tests/test_web_app.py:8301-8367`에서 single-source latest_update reload exact field를 잠그고 있고, noisy community가 섞인 single-source latest_update label parity도 `tests/test_web_app.py:9856-9946`에서 확인합니다. 현재 브라우저의 generic history-badge smoke는 latest_update 카드 정적 렌더를 `설명형 단일 출처` / `설명형 출처` 조합으로만 확인할 뿐(`e2e/tests/web-smoke.spec.mjs:1078-1087`), actual history-card reload의 single-source label continuity는 검증하지 않습니다. 따라서 같은 family의 다음 current-risk reduction으로는 single-source latest-update record reload 뒤 origin detail이 `단일 출처 참고`와 `보조 출처`를 유지하는지 브라우저 smoke로 1건 더 잠그는 편이 가장 좁고 직접적입니다. 이 마지막 판단은 current tree와 existing coverage gap을 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-latest-update-mixed-source-source-path-continuity-smoke-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-dual-probe-source-path-continuity-smoke-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -lt work/4/7 verify/4/7`
- `git status --short`
- `rg -n "24 browser scenarios|scenario 24|mixed-source source-path continuity|store.steampowered.com|AKR20260401000100017|history-card latest-update" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1220,2090p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `24`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 mixed-source source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.3s)`
- `rg -n "claim_coverage|progress_summary|claim-coverage|verification state|history-card|load_web_search_record|show-only|response-origin|context box|source-path" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs app/static/app.js README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '980,1118p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1112,1220p'`
- `nl -ba tests/test_web_app.py | sed -n '8233,8367p'`
- `nl -ba tests/test_web_app.py | sed -n '9856,9946p'`
- `rg -n "단일 출처 참고|보조 출처|기사 교차 확인|설명형 단일 출처|설명형 출처" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`

## 남은 리스크
- latest `/work`는 truthful하게 닫혔지만, history-card latest-update single-source reload 경로의 verification-label continuity는 아직 브라우저 smoke로 잠겨 있지 않습니다.
- unrelated dirty worktree가 여전히 큽니다. 이번 verification은 latest `/work` truth와 다음 slice 고정에 필요한 파일만 다시 확인했습니다.
- `make e2e-test`와 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 Playwright-only smoke tightening과 문서 count 동기화 범위였고, shared browser helper 변경도 없었습니다.
