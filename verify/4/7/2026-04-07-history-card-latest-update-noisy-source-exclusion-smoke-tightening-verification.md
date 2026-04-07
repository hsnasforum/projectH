## 변경 파일
- `verify/4/7/2026-04-07-history-card-latest-update-noisy-source-exclusion-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-latest-update-noisy-source-exclusion-smoke-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 아직 직전 latest-update follow-up continuity 라운드(`verify/4/7/2026-04-07-history-card-latest-update-follow-up-response-origin-continuity-tightening-verification.md`)를 가리키고 있어, 이번 noisy-source exclusion 라운드 기준의 새 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 Playwright 추가 주장은 current tree와 일치합니다. `e2e/tests/web-smoke.spec.mjs:1573-1699`에는 latest-update history-card reload 뒤 noisy community source가 본문과 origin detail에 다시 노출되지 않는지 검증하는 시나리오가 실제로 있고, positive assert로 `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을, negative assert로 `보조 커뮤니티`, `brunch`, `로그인 회원가입 구독 광고` 미노출을 잠그고 있습니다.
- 문서 동기화도 맞습니다. `README.md:133`, `docs/ACCEPTANCE_CRITERIA.md:1342`, `docs/MILESTONES.md:51`, `docs/TASK_BACKLOG.md:40`, `docs/NEXT_STEPS.md:16`은 scenario 21과 latest-update noisy-source exclusion contract를 반영하고 있고, `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `21`이었습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 다음 exact slice는 `history-card entity-card noisy-source exclusion smoke tightening`으로 고정하는 편이 맞습니다. same history-card reload family에서 entity-card 쪽 service regression은 이미 `tests/test_web_app.py:9431-9548`에 있어 load_web_search_record_id reload 뒤 noisy single-source claim이 다시 노출되지 않는지 잠그고, `tests/test_web_app.py:9551-9660`에는 natural reload에서 `source_roles = ["백과 기반"]` 유지까지 있습니다. 반면 current e2e는 `e2e/tests/web-smoke.spec.mjs:1112-1220`의 entity-card show-only reload continuity와 `e2e/tests/web-smoke.spec.mjs:1332-1447`의 entity-card follow-up continuity는 잠그지만, noisy single-source claim이나 noisy role이 click reload 뒤 다시 드러나지 않는지는 아직 직접 검증하지 않습니다. 따라서 same-family current-risk reduction 우선순위상 entity-card reload noisy-source exclusion browser smoke 1건이 가장 직접적입니다. 위 판단은 current tree와 existing regression coverage gap을 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-latest-update-noisy-source-exclusion-smoke-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-latest-update-follow-up-response-origin-continuity-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -lt work/4/7 verify/4/7`
- `git status --short`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n "21 browser scenarios|scenario 21|noisy community source|보조 커뮤니티|로그인 회원가입 구독 광고|history-card latest-update" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1220,1705p'`
- `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `21`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source가 본문과 origin detail에 노출되지 않습니다" --reporter=line`
  - `1 passed (4.6s)`
- `nl -ba README.md | sed -n '126,136p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1337,1344p'`
- `nl -ba docs/MILESTONES.md | sed -n '46,53p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '37,42p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `nl -ba tests/test_web_app.py | sed -n '9428,9664p'`
- `rg -n "history-card.*entity|entity-card|백과 기반|설명형 단일 출처|noisy single-source|noisy source|single-source claim" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- latest `/work`는 truthful하게 닫혔지만, history-card entity-card reload 경로의 noisy single-source exclusion은 아직 브라우저 smoke로 잠겨 있지 않습니다.
- unrelated dirty worktree가 여전히 큽니다. 이번 verification은 latest `/work` truth와 다음 slice 고정에 필요한 파일만 다시 확인했습니다.
- `make e2e-test`와 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 Playwright-only smoke tightening과 문서 count 동기화 범위였고, shared browser helper 변경도 없었습니다.
