## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-acceptance-criteria-web-investigation-source-role-trust-wording-clarification.md`가 trust-label acceptance wording을 current shipped truth에 맞게 옮겼는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `ACCEPTANCE_CRITERIA Web Investigation source-role trust wording clarification` 슬라이스 기준이어서, 이번 latest `/work`까지 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 **부분적으로만 truthful**하다고 확인했습니다.
- truthful한 부분:
  - `docs/ACCEPTANCE_CRITERIA.md:37-39`는 `/work` 주장대로 current shipped trust-label surface와 일치합니다.
  - `app/static/app.js:217-220`, `app/static/app.js:2241-2255`, `app/static/app.js:2367-2368`, `app/static/app.js:2893-2899`, `e2e/tests/web-smoke.spec.mjs:1031-1114`는 answer-mode separation, claim-coverage source-role trust line, response-origin compact trust labels가 이미 구현·검증되었음을 다시 보여줍니다.
- 그러나 `/work`가 `실제 미완료`로 남겼던 `docs/ACCEPTANCE_CRITERIA.md:53-54`는 current code/test truth와 맞지 않습니다.
  - `Entity-card web investigation should prioritize agreement-backed facts over noisy snippets.`는 이미 shipped behavior입니다.
  - 근거:
    - `core/agent_loop.py:3967-3995`, `core/agent_loop.py:4053-4111`는 entity-card fact-card selection에서 multi-source consensus와 trusted-source 우선 선택을 구현합니다.
    - `tests/test_smoke.py:1966-2021`는 single blog claim보다 multi-source agreement를 우선하고 noisy claim/body 노출을 막는 현재 contract를 고정합니다.
    - `tests/test_web_app.py:9649-9895`, `tests/test_web_app.py:17275-17506`는 initial response, natural reload, click reload, follow-up, second follow-up에서 noisy single-source claim exclusion과 agreement-backed fact retention을 검증합니다.
    - `docs/MILESTONES.md:52`, `docs/MILESTONES.md:70`, `docs/MILESTONES.md:78`, `docs/MILESTONES.md:97`도 이미 같은 shipped behavior를 completed milestone로 기록합니다.
  - `Reinvestigation should improve weak slots before weak facts are shown as stable facts.`도 이미 shipped behavior입니다.
  - 근거:
    - `core/agent_loop.py:2448-2483`는 weak/missing slot 우선 재조사 suggestion을 만듭니다.
    - `core/agent_loop.py:4124-4160`는 weak slot을 `rendered_as = "uncertain"`로 serialize하고 stable fact-card와 분리합니다.
    - `core/agent_loop.py:4165-4208`는 reinvestigation progress / focus-slot annotation을 기록합니다.
    - `tests/test_smoke.py:1388-1402`, `tests/test_smoke.py:1948-1964`, `tests/test_web_app.py:5277-5305`, `tests/test_web_app.py:5418-5444`는 weak slot이 uncertain으로 남고 reinvestigation suggestion/progress가 current contract임을 검증합니다.
- 따라서 current misleading shipped-contract surface는 이제 `docs/ACCEPTANCE_CRITERIA.md:53-54`뿐 아니라 `docs/PRODUCT_SPEC.md:314-317`까지 포함한다고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 다음 exact slice를 `ACCEPTANCE_CRITERIA + PRODUCT_SPEC Web Investigation agreement/reinvestigation wording clarification`으로 갱신했습니다.

## 검증
- `sed -n '1,220p' work/4/8/2026-04-08-acceptance-criteria-web-investigation-source-role-trust-wording-clarification.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-milestones-web-investigation-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '24,56p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '96,110p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '280,320p'`
- `nl -ba docs/MILESTONES.md | sed -n '46,100p'`
- `nl -ba app/static/app.js | sed -n '204,222p;2238,2378p;2888,2902p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1008,1116p'`
- `nl -ba core/agent_loop.py | sed -n '2448,2515p;3948,4208p;7506,7535p'`
- `nl -ba tests/test_smoke.py | sed -n '1388,1404p;1948,2028p'`
- `nl -ba tests/test_web_app.py | sed -n '5268,5444p;9644,9895p;17275,17510p'`
- `rg -n "agreement-backed|single-source noise|noisy|weak-slot|reinvestigation|cross-verified|stronger source consensus|suppression of noisy|claim coverage" app/static/app.js core docs tests e2e -S`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-acceptance-criteria-web-investigation-source-role-trust-wording-clarification-verification.md`
- `ls -lt .pipeline/claude_handoff.md .pipeline/gemini_request.md .pipeline/gemini_advice.md .pipeline/operator_request.md`
- docs/pipeline-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/ACCEPTANCE_CRITERIA.md:53-54`와 `docs/PRODUCT_SPEC.md:314-317`는 여전히 current shipped web-investigation quality baseline을 과소표현합니다.
- 다음 slice는 shipped baseline과 future quality-improvement roadmap을 분리해서 적어야 하며, `docs/TASK_BACKLOG.md:102-105`의 high-level current-phase priorities 자체까지 함께 바꾸는 것으로 넓히면 안 됩니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
