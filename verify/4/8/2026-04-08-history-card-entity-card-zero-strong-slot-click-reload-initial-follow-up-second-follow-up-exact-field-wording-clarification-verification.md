# history-card entity-card zero-strong-slot click-reload initial + follow-up + second-follow-up exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-zero-strong-slot-click-reload-initial-follow-up-second-follow-up-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 zero-strong-slot click-reload family의 initial/follow-up/second-follow-up title 3개가 exact-field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 noisy single-source claim click-reload wording family를 닫아 둔 상태였으므로, 이번 zero-strong-slot click-reload sibling family도 실제로 닫고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:3682`, `e2e/tests/web-smoke.spec.mjs:3784`, `e2e/tests/web-smoke.spec.mjs:3901`에는 `/work`가 주장한 zero-strong-slot click-reload title wording이 실제로 반영돼 있었고, `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity truth를 직접 드러냅니다.
- click-reload body/docs truth도 current tree와 맞았습니다. initial body는 `e2e/tests/web-smoke.spec.mjs:3757`, `e2e/tests/web-smoke.spec.mjs:3758`, `e2e/tests/web-smoke.spec.mjs:3759`, `e2e/tests/web-smoke.spec.mjs:3761`, `e2e/tests/web-smoke.spec.mjs:3762`, `e2e/tests/web-smoke.spec.mjs:3763`, `e2e/tests/web-smoke.spec.mjs:3766`, `e2e/tests/web-smoke.spec.mjs:3767`, `e2e/tests/web-smoke.spec.mjs:3768`, `e2e/tests/web-smoke.spec.mjs:3771`, `e2e/tests/web-smoke.spec.mjs:3772`, `e2e/tests/web-smoke.spec.mjs:3773`에서 same continuity를 직접 검증하고, follow-up body는 `e2e/tests/web-smoke.spec.mjs:3877`, `e2e/tests/web-smoke.spec.mjs:3878`, `e2e/tests/web-smoke.spec.mjs:3880`, `e2e/tests/web-smoke.spec.mjs:3881`, `e2e/tests/web-smoke.spec.mjs:3884`, `e2e/tests/web-smoke.spec.mjs:3885`, `e2e/tests/web-smoke.spec.mjs:3888`, `e2e/tests/web-smoke.spec.mjs:3889`, `e2e/tests/web-smoke.spec.mjs:3890`, second-follow-up body는 `e2e/tests/web-smoke.spec.mjs:3989`, `e2e/tests/web-smoke.spec.mjs:3990`, `e2e/tests/web-smoke.spec.mjs:3992`, `e2e/tests/web-smoke.spec.mjs:3993`, `e2e/tests/web-smoke.spec.mjs:3994`, `e2e/tests/web-smoke.spec.mjs:3997`, `e2e/tests/web-smoke.spec.mjs:3998`, `e2e/tests/web-smoke.spec.mjs:4001`, `e2e/tests/web-smoke.spec.mjs:4002`, `e2e/tests/web-smoke.spec.mjs:4003`에서 same continuity truth를 직접 검증합니다. docs `README.md:147`, `README.md:148`, `README.md:149`, `docs/MILESTONES.md:65`, `docs/MILESTONES.md:66`, `docs/MILESTONES.md:67`, `docs/ACCEPTANCE_CRITERIA.md:1356`, `docs/ACCEPTANCE_CRITERIA.md:1357`, `docs/ACCEPTANCE_CRITERIA.md:1358`, `docs/TASK_BACKLOG.md:54`, `docs/TASK_BACKLOG.md:55`, `docs/TASK_BACKLOG.md:56`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*다시 불러오기 후" --reporter=line`은 `3 passed (19.3s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- zero-strong-slot click-reload wording family는 이번 라운드 기준으로 닫혔습니다. 다음 Claude 슬라이스는 `entity-card zero-strong-slot natural-reload initial + follow-up exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:4014`, `e2e/tests/web-smoke.spec.mjs:4122`의 browser natural-reload title 2개는 아직 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity truth를 title에서 직접 드러내지 않습니다. 같은 family body는 initial `e2e/tests/web-smoke.spec.mjs:4097`, `e2e/tests/web-smoke.spec.mjs:4098`, `e2e/tests/web-smoke.spec.mjs:4100`, `e2e/tests/web-smoke.spec.mjs:4101`, `e2e/tests/web-smoke.spec.mjs:4102`, `e2e/tests/web-smoke.spec.mjs:4104`, `e2e/tests/web-smoke.spec.mjs:4105`, `e2e/tests/web-smoke.spec.mjs:4106`, `e2e/tests/web-smoke.spec.mjs:4109`, `e2e/tests/web-smoke.spec.mjs:4110`, `e2e/tests/web-smoke.spec.mjs:4111`, follow-up `e2e/tests/web-smoke.spec.mjs:4219`, `e2e/tests/web-smoke.spec.mjs:4220`, `e2e/tests/web-smoke.spec.mjs:4222`, `e2e/tests/web-smoke.spec.mjs:4223`, `e2e/tests/web-smoke.spec.mjs:4224`, `e2e/tests/web-smoke.spec.mjs:4226`, `e2e/tests/web-smoke.spec.mjs:4227`, `e2e/tests/web-smoke.spec.mjs:4228`, `e2e/tests/web-smoke.spec.mjs:4231`, `e2e/tests/web-smoke.spec.mjs:4232`, `e2e/tests/web-smoke.spec.mjs:4233`에서 same continuity truth를 직접 검증합니다. docs `README.md:150`, `README.md:151`, `docs/MILESTONES.md:68`, `docs/MILESTONES.md:69`, `docs/ACCEPTANCE_CRITERIA.md:1359`, `docs/ACCEPTANCE_CRITERIA.md:1360`, `docs/TASK_BACKLOG.md:57`, `docs/TASK_BACKLOG.md:58`도 이미 same truth를 고정합니다. initial/follow-up이 같은 natural-reload continuity contract를 공유하므로, 이 둘을 한 coherent slice로 닫는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-entity-card-zero-strong-slot-click-reload-initial-follow-up-second-follow-up-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-noisy-single-source-claim-click-reload-follow-up-second-follow-up-exact-field-provenance-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3682,4004p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4014,4250p'`
- `nl -ba README.md | sed -n '147,151p'`
- `nl -ba docs/MILESTONES.md | sed -n '65,69p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1356,1360p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '54,58p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*다시 불러오기 후" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `e2e/tests/web-smoke.spec.mjs:4014`, `e2e/tests/web-smoke.spec.mjs:4122`의 zero-strong-slot browser natural-reload title 2개는 아직 continuity truth를 충분히 직접 드러내지 않습니다. 현재 body와 문서는 이미 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity를 직접 고정하므로, 다음 라운드에서는 title wording만 맞추는 것이 가장 작은 same-family current-risk reduction입니다.
- 다른 answer-mode family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
