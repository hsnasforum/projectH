## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-noisy-source-exclusion-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-noisy-source-exclusion-smoke-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 아직 직전 latest-update noisy-source exclusion 라운드(`verify/4/7/2026-04-07-history-card-latest-update-noisy-source-exclusion-smoke-tightening-verification.md`)를 가리키고 있어, 이번 entity-card noisy-source exclusion 라운드 기준의 새 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 Playwright 추가 주장은 current tree와 일치합니다. `e2e/tests/web-smoke.spec.mjs:1701-1837`에는 entity-card history-card reload 뒤 noisy single-source claim이 본문과 origin detail에 다시 노출되지 않는지 검증하는 시나리오가 실제로 있고, positive assert로 `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `확인된 사실:`, `교차 확인`을, negative assert로 `blog.example.com`, `출시일`, `2025`, `로그인 회원가입 구독 광고` 미노출을 잠그고 있습니다.
- 문서 동기화도 맞습니다. `README.md:134`, `docs/ACCEPTANCE_CRITERIA.md:1343`, `docs/MILESTONES.md:52`, `docs/TASK_BACKLOG.md:41`, `docs/NEXT_STEPS.md:16`은 scenario 22와 entity-card noisy-source exclusion contract를 반영하고 있고, `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `22`였습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 다음 exact slice는 `history-card entity-card dual-probe source-path continuity smoke tightening`으로 고정하는 편이 맞습니다. same history-card reload family에서 service regression은 이미 `tests/test_web_app.py:8508-8655`에 있어 entity-card dual-probe reload 뒤 `active_context.source_paths`에 두 probe URL이 모두 보존되는지 잠그고, UI는 `app/static/app.js:2390-2411`에서 그 값을 `#context-box`에 `출처:` 줄로 렌더링합니다. 반면 current e2e는 history-card reload 시나리오들(`e2e/tests/web-smoke.spec.mjs:1112-1837`)에서 response body, origin badge, noisy exclusion만 확인할 뿐 `#context-box` source-path continuity는 아직 직접 검증하지 않습니다. 따라서 same-family current-risk reduction 우선순위상 entity-card click reload 뒤 dual-probe source-path continuity를 브라우저에서 1건으로 잠그는 편이 가장 직접적입니다. 위 판단은 current tree와 existing regression coverage gap을 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-entity-card-noisy-source-exclusion-smoke-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-latest-update-noisy-source-exclusion-smoke-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -lt work/4/7 verify/4/7`
- `git status --short`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n "22 browser scenarios|scenario 22|entity-card noisy-source exclusion|noisy single-source claim|출시일|2025|history-card entity-card" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1568,1820p'`
- `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `22`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다" --reporter=line`
  - `1 passed (6.3s)`
- `rg -n "reload_preserves|follow_up_preserves|latest_update.*reload|entity_card.*reload|claim_coverage_progress_summary|stored_summary_text|stored_response_origin" tests/test_web_app.py`
- `rg -n "claim-coverage-hint|claim coverage|progress summary|stored summary|summary_text|follow-up|다시 불러오기|history-card" e2e/tests/web-smoke.spec.mjs`
- `nl -ba tests/test_web_app.py | sed -n '14540,15020p'`
- `nl -ba app/static/app.js | sed -n '2388,2425p'`
- `rg -n "#context-box|renderContext\\(|source_paths|출처:" e2e/tests/web-smoke.spec.mjs`
- `nl -ba tests/test_web_app.py | sed -n '8508,8750p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1814,1845p'`
- `rg -n "dual probe|source_paths|pearlabyss.com/ko-KR/Board/Detail\\?_boardNo=200|pearlabyss.com/ko-KR/Board/Detail\\?_boardNo=300|문맥 종류|현재 문서: 붉은사막" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- latest `/work`는 truthful하게 닫혔지만, history-card entity-card reload 경로의 dual-probe source-path continuity는 아직 브라우저 smoke로 잠겨 있지 않습니다.
- unrelated dirty worktree가 여전히 큽니다. 이번 verification은 latest `/work` truth와 다음 slice 고정에 필요한 파일만 다시 확인했습니다.
- `make e2e-test`와 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 Playwright-only smoke tightening과 문서 count 동기화 범위였고, shared browser helper 변경도 없었습니다.
