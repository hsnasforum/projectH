# entity-card noisy-single-source natural-reload follow-up-second-follow-up browser-anchor provenance wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-natural-reload-follow-up-second-follow-up-browser-anchor-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 generic noisy-single-source natural-reload follow-up/second-follow-up browser anchors의 title/session naming을 provenance contract까지 드러내도록 정리했다고 보고했습니다. 이번 라운드에서는 그 code change, exact rerun, 그리고 다음 같은 family 슬라이스를 current tree 기준으로 다시 좁힐 필요가 있었습니다.
- same-day latest `/verify`가 crimson natural-reload noisy-exclusion branch를 already 정리했기 때문에, 이번에는 generic noisy-single-source branch가 truthful하게 닫혔는지와 남은 current-risk가 어디에 남는지 확인해야 했습니다.

## 핵심 변경
- latest `/work`는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:6242`, `e2e/tests/web-smoke.spec.mjs:6243`, `e2e/tests/web-smoke.spec.mjs:6315`, `e2e/tests/web-smoke.spec.mjs:6316`에서 generic noisy-single-source natural-reload follow-up/second-follow-up browser anchors가 now negative `출시일/2025/blog.example.com` assertion과 `blog.example.com provenance가 context box에 유지됩니다` wording을 title/session naming에 직접 드러냅니다.
- `/work`가 적은 exact rerun `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim" --reporter=line`도 current tree에서 `4 passed (25.1s)`로 일치했습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs`도 clean이었고 `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과도 `75`였습니다.
- 다음 Claude 슬라이스는 `history-card entity-card noisy-single-source click-reload follow-up-second-follow-up browser-anchor provenance wording clarification`으로 고정했습니다. natural-reload generic anchors는 닫혔지만, click-reload generic anchors `e2e/tests/web-smoke.spec.mjs:6391`, `e2e/tests/web-smoke.spec.mjs:6392`, `e2e/tests/web-smoke.spec.mjs:6460`, `e2e/tests/web-smoke.spec.mjs:6461`은 still generic wording만 남기고 있습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-natural-reload-follow-up-second-follow-up-browser-anchor-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-provenance-wording-clarification-verification.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6238,6472p'`
- `nl -ba README.md | sed -n '184,188p'`
- `nl -ba docs/MILESTONES.md | sed -n '96,98p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1393,1397p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,95p'`
- `nl -ba tests/test_web_app.py | sed -n '17433,17508p'`
- `rg -n '^test\\(\".*entity-card noisy single-source claim|entity-noisy-natural-reload-(followup|second-followup).*|entity-noisy-click-reload-(followup|second-followup).*' e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 history-card entity-card noisy-single-source click-reload browser anchor wording weakness입니다. `README.md:186`, `README.md:187`, `docs/ACCEPTANCE_CRITERIA.md:1395`, `docs/ACCEPTANCE_CRITERIA.md:1396`, `docs/TASK_BACKLOG.md:93`, `docs/TASK_BACKLOG.md:94`, `tests/test_web_app.py:17434`, `tests/test_web_app.py:17493`는 click-reload follow-up/second-follow-up에서 negative `출시일`/`2025`/`blog.example.com` assertions와 `blog.example.com` provenance continuity를 직접 적습니다.
- 반면 `e2e/tests/web-smoke.spec.mjs:6391`, `e2e/tests/web-smoke.spec.mjs:6392`, `e2e/tests/web-smoke.spec.mjs:6460`, `e2e/tests/web-smoke.spec.mjs:6461`은 still `다시 노출되지 않습니다`와 generic session naming만 남겨, already-tested provenance contract가 browser anchor title/session naming에서 직접 드러나지 않습니다. 다음 라운드는 runtime/assertion logic과 docs를 건드리지 않는 test-only wording clarification이 가장 작고 reviewable합니다.
