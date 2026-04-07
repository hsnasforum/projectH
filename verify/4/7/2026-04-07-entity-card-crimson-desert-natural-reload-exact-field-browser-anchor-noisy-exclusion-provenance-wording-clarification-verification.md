# entity-card crimson-desert natural-reload exact-field browser-anchor noisy-exclusion provenance wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-browser-anchor-noisy-exclusion-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card 붉은사막 natural-reload initial exact-field browser anchor title/session naming이 already-tested noisy-exclusion + provenance truth를 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 code change, exact rerun, 그리고 남은 리스크 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 history-card noisy-single-source initial click-reload browser anchor를 already 닫았으므로, 이번에는 entity-card 붉은사막 natural-reload initial branch가 truthful하게 닫혔는지와 다음 adjacent current-risk가 어디에 남는지 좁혀야 했습니다.

## 핵심 변경
- latest `/work`는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4242`, `e2e/tests/web-smoke.spec.mjs:4243`의 title/session naming 보정은 current tree와 일치했고, same test body `e2e/tests/web-smoke.spec.mjs:4294`, `e2e/tests/web-smoke.spec.mjs:4297`, `e2e/tests/web-smoke.spec.mjs:4303`, `e2e/tests/web-smoke.spec.mjs:4306`가 검사하는 `설명형 다중 출처 합의`, `백과 기반`, negative `출시일`/`2025`/`blog.example.com`, provenance `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` truth와도 맞았습니다.
- `/work`가 적은 exact rerun도 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload" --reporter=line`은 `1 passed (7.9s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- `/work`가 남긴 source-path-only anchor follow-up suspicion도 current-risk로 타당합니다. root docs인 `README.md:158`, `docs/ACCEPTANCE_CRITERIA.md:1367`, `docs/TASK_BACKLOG.md:65`, `docs/MILESTONES.md:76`은 entity-card 붉은사막 natural-reload source-path contract를 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance plurality까지 직접 적습니다. 반면 browser anchor `e2e/tests/web-smoke.spec.mjs:4314`, `e2e/tests/web-smoke.spec.mjs:4315`는 still generic `source path가 context box에 유지됩니다`와 generic session naming만 남기지만, same test body `e2e/tests/web-smoke.spec.mjs:4360`, `e2e/tests/web-smoke.spec.mjs:4361`, `e2e/tests/web-smoke.spec.mjs:4362`, `e2e/tests/web-smoke.spec.mjs:4363`는 already exact provenance plurality truth를 직접 검사합니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert natural-reload source-path browser-anchor provenance wording clarification`으로 고정했습니다. runtime/assertion logic을 건드리지 않고 initial source-path-only browser anchor title/session naming만 docs/body truth에 맞추는 test-only wording clarification이 same-family smallest current-risk reduction입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-browser-anchor-noisy-exclusion-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-noisy-single-source-initial-click-reload-browser-anchor-provenance-wording-clarification-verification.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4242,4365p'`
- `nl -ba README.md | sed -n '152,158p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,77p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1368p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,66p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-anchor verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 entity-card 붉은사막 natural-reload source-path-only browser anchor wording weakness입니다. `e2e/tests/web-smoke.spec.mjs:4314`, `e2e/tests/web-smoke.spec.mjs:4315`의 generic title/session naming이 body가 이미 검사하는 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance plurality를 직접 드러내지 않습니다.
- 다음 라운드는 `e2e/tests/web-smoke.spec.mjs` initial natural-reload source-path-only anchor 1개만 다루는 test-only wording clarification으로 충분합니다. exact-field anchor, follow-up/second-follow-up anchors, service tests, docs, other families는 범위 밖입니다.
