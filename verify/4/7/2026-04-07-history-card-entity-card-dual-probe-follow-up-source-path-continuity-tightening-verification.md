## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-dual-probe-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-dual-probe-follow-up-source-path-continuity-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 직전 latest-update news-only follow-up continuity 라운드(`verify/4/7/2026-04-07-history-card-latest-update-news-only-follow-up-response-origin-continuity-tightening-verification.md`)를 가리키고 있어, 이번 entity-card dual-probe follow-up source-path continuity 라운드 기준의 새 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 service test, Playwright 추가, 문서 동기화 주장은 current tree와 일치합니다. `tests/test_web_app.py:15161-15220`에는 entity-card dual-probe record를 `load_web_search_record_id + user_text` follow-up으로 이어갔을 때 `active_context.source_paths`에 `https://www.pearlabyss.com/200`, `https://www.pearlabyss.com/300`이 유지되는 회귀가 실제로 있고, `e2e/tests/web-smoke.spec.mjs:2691-2812`에는 같은 browser contract가 실제로 들어 있습니다. 문서도 `README.md:143`, `docs/ACCEPTANCE_CRITERIA.md:1352`, `docs/MILESTONES.md:61`, `docs/TASK_BACKLOG.md:50`, `docs/NEXT_STEPS.md:16`에서 scenario 31 기준으로 맞춰져 있습니다. `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `31`이었고, `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 좁은 재실행도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths`는 `OK (0.025s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다" --reporter=line`은 `1 passed (6.3s)`였습니다.
- 다음 exact slice는 `history-card latest-update mixed-source follow-up source-path continuity tightening`으로 고정했습니다. current tree에는 latest-update show-only source-path continuity가 mixed-source(`e2e/tests/web-smoke.spec.mjs:1951-2052`), single-source(`e2e/tests/web-smoke.spec.mjs:2363-2453`), news-only(`e2e/tests/web-smoke.spec.mjs:2260-2361`)까지 있고, follow-up response-origin continuity도 mixed-source(`tests/test_web_app.py:14935-15012`, `e2e/tests/web-smoke.spec.mjs:1449-1562`), single-source(`tests/test_web_app.py:15015-15082`, `e2e/tests/web-smoke.spec.mjs:2455-2566`), news-only(`tests/test_web_app.py:15084-15159`, `e2e/tests/web-smoke.spec.mjs:2568-2689`)까지 닫혀 있습니다. 반면 latest-update follow-up source-path continuity는 service와 browser 양쪽에서 아직 current tree에 없습니다. `rg -n "latest-update.*follow-up.*source path|follow-up.*mixed-source source path|follow-up.*single-source source path|follow-up.*news-only source path|source_paths.*latest_update.*follow_up|latest_update.*load_web_search_record_id.*source_paths" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`가 no match였습니다. 그중 mixed-source는 latest-update 기본축이자 기존 fixture 재사용성이 가장 높습니다. service 쪽 exact reload 기준점이 `tests/test_web_app.py:8155-8231`, `tests/test_web_app.py:8369-8445`에 이미 있고, browser 쪽도 mixed-source show-only source-path continuity(`e2e/tests/web-smoke.spec.mjs:1951-2052`)와 mixed-source follow-up response-origin continuity(`e2e/tests/web-smoke.spec.mjs:1449-1562`)가 이미 있어서 같은 family current-risk reduction 기준으로 가장 좁고 직접적입니다. 이 마지막 판단은 current tree와 existing coverage gap을 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-entity-card-dual-probe-follow-up-source-path-continuity-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-latest-update-news-only-follow-up-response-origin-continuity-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `ls -lt work/4/7 verify/4/7 | sed -n '1,120p'`
- `rg -n "dual-probe follow_up|dual-probe follow-up|history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다|31 browser scenarios|scenario 31|dual-probe source-path continuity|source path continuity" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba tests/test_web_app.py | sed -n '15140,15260p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2678,2805p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `31`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths`
  - `OK (0.025s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.3s)`
- `rg -n "31 browser scenarios|scenario 31|dual-probe|pearlabyss.com/200|pearlabyss.com/300|follow-up" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "latest-update.*follow-up.*source path|follow-up.*mixed-source source path|follow-up.*single-source source path|follow-up.*news-only source path|source_paths.*latest_update.*follow_up|latest_update.*load_web_search_record_id.*source_paths" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`
  - no match
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1938,2688p'`
- `nl -ba tests/test_web_app.py | sed -n '8138,8450p'`

## 남은 리스크
- latest `/work`는 truthful하게 닫혔지만, latest-update 계열은 reload 뒤 follow-up에서 `#context-box` source-path continuity를 직접 잠그는 서비스/브라우저 검증이 아직 없습니다.
- unrelated dirty worktree가 여전히 큽니다. 이번 verification은 latest `/work` truth와 다음 slice 고정에 필요한 파일만 다시 확인했습니다.
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 single-test + single-scenario 범위였고, shared browser helper나 runtime helper 변경도 없었습니다.
