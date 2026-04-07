# history-card entity-card noisy-single-source click-reload follow-up-second-follow-up browser-anchor provenance wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-noisy-single-source-click-reload-follow-up-second-follow-up-browser-anchor-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card noisy-single-source click-reload follow-up/second-follow-up browser anchor title과 session naming이 negative assertion + provenance truth와 맞게 정리되었다고 보고했습니다. 이번 라운드에서는 그 code change, rerun claim, 그리고 same-family closure 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 noisy-single-source natural-reload branch를 already 닫았으므로, 이번에는 click-reload branch가 실제로 닫혔는지와 남은 smallest current-risk가 어디에 남는지 좁혀야 했습니다.

## 핵심 변경
- latest `/work`는 부분만 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:6391`, `e2e/tests/web-smoke.spec.mjs:6392`, `e2e/tests/web-smoke.spec.mjs:6460`, `e2e/tests/web-smoke.spec.mjs:6461`의 click-reload follow-up/second-follow-up title/session naming 보정은 current tree와 일치했습니다.
- `/work`가 적은 rerun도 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim" --reporter=line`은 `2 passed (13.7s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- 다만 `/work`의 `남은 리스크 없음`과 family completion 서술은 과장입니다. initial click-reload browser anchor `e2e/tests/web-smoke.spec.mjs:1701`, `e2e/tests/web-smoke.spec.mjs:1702`는 still generic한 title/session naming만 남기지만, 같은 fixture body `e2e/tests/web-smoke.spec.mjs:1816`, `e2e/tests/web-smoke.spec.mjs:1821`, `e2e/tests/web-smoke.spec.mjs:1829`, `e2e/tests/web-smoke.spec.mjs:1835`는 이미 `설명형 다중 출처 합의`, negative `출시일`/`2025`/`blog.example.com`, 그리고 provenance `namu.wiki`/`ko.wikipedia.org`/`blog.example.com`까지 직접 검사합니다. root docs도 `docs/MILESTONES.md:52`, `docs/ACCEPTANCE_CRITERIA.md:1343`, `docs/TASK_BACKLOG.md:41`, `docs/NEXT_STEPS.md:16`에서 같은 truth를 더 구체적으로 적고 있습니다.
- 다음 Claude 슬라이스는 `history-card entity-card noisy-single-source initial-click-reload browser-anchor provenance wording clarification`으로 고정했습니다. 이미 검증된 initial click-reload contract를 runtime/assertion logic 변경 없이 title/session naming에만 truth-sync하는 test-only wording clarification이 same-family smallest current-risk reduction입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-entity-card-noisy-single-source-click-reload-follow-up-second-follow-up-browser-anchor-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-natural-reload-follow-up-second-follow-up-browser-anchor-provenance-wording-clarification-verification.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1698,1838p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6386,6474p'`
- `nl -ba docs/MILESTONES.md | sed -n '50,54p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1338,1397p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '38,43p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,95p'`
- `nl -ba README.md | sed -n '184,188p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,40p'`
- `rg -n "history-card entity-card noisy single-source claim|history-card entity-card 다시 불러오기 후 noisy single-source claim|history-card-reload-entity-noisy|출시일|2025|blog.example.com provenance" e2e/tests/web-smoke.spec.mjs README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card noisy single-source claim" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 initial click-reload browser anchor wording weakness입니다. `e2e/tests/web-smoke.spec.mjs:1701`, `e2e/tests/web-smoke.spec.mjs:1702`의 generic title/session naming이 이미 검증 중인 negative `출시일`/`2025`/`blog.example.com` assertions와 provenance `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` continuity를 직접 드러내지 않습니다.
- 다음 라운드는 `e2e/tests/web-smoke.spec.mjs` initial click-reload anchor만 다루는 test-only wording clarification으로 충분합니다. runtime behavior, fixture body assertions, docs, service tests, other reload families는 범위 밖입니다.
