## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-acceptance-criteria-product-spec-agreement-reinvestigation-wording-clarification.md`가 `ACCEPTANCE_CRITERIA` / `PRODUCT_SPEC`의 agreement-over-noise, weak-slot reinvestigation wording을 current shipped truth에 맞게 정리했는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `ACCEPTANCE_CRITERIA + PRODUCT_SPEC Web Investigation agreement/reinvestigation wording clarification` 슬라이스 기준이어서, 이번 latest `/work`까지 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
- current `docs/ACCEPTANCE_CRITERIA.md:40-41`은 `/work` 주장대로 현재 shipped baseline을 올바르게 반영합니다.
  - entity-card responses prefer agreement-backed facts over noisy single-source claims
  - weak/missing slots stay uncertain and reinvestigation targets weak/missing slots first
- current `docs/PRODUCT_SPEC.md:313-317`도 `/work` 주장대로 현재 shipped baseline과 future quality-improvement direction을 분리합니다.
  - `docs/PRODUCT_SPEC.md:313-314`는 shipped baseline
  - `docs/PRODUCT_SPEC.md:317`는 future quality-improvement direction reference
- 위 wording은 current implementation/test truth와 일치합니다.
  - `core/agent_loop.py:2448-2483`는 weak/missing slot 우선 reinvestigation suggestion을 만듭니다.
  - `core/agent_loop.py:3967-3995`, `core/agent_loop.py:4053-4111`는 agreement-backed entity facts를 noisy single-source claims보다 우선 선택합니다.
  - `core/agent_loop.py:4124-4160`는 weak slots를 `rendered_as = "uncertain"`로 serialize합니다.
  - `tests/test_smoke.py:1388-1402`, `tests/test_smoke.py:1966-2021`, `tests/test_web_app.py:5277-5305`, `tests/test_web_app.py:5418-5444`, `tests/test_web_app.py:9649-9895`, `tests/test_web_app.py:17275-17506`는 위 shipped behavior를 잠급니다.
- same-family web-investigation docs truth-sync family는 이번 라운드로 닫혔다고 판단했습니다.
- previous `.pipeline/claude_handoff.md`는 이미 닫힌 docs truth-sync 슬라이스를 계속 가리키고 있어 stale 상태였고, 이번 라운드에서 갱신했습니다.
- next slice는 same-family current-risk reduction으로 `Web Investigation verified-vs-uncertain explanation tightening` 한 개로 고정했습니다.
  - `docs/PRODUCT_SPEC.md:293`이 아직 `stronger explanation of verified vs uncertain claims`를 in-progress로 남기고 있습니다.
  - current shipped UX는 이미 status labels / uncertain rendering / progress summary를 제공하지만, 현재 explanation은 response body와 claim-coverage hint에 나뉘어 있어 verified vs uncertain vs unresolved mapping을 더 명확히 할 여지가 남아 있습니다.
  - 근거:
    - `core/agent_loop.py:4537-4574`는 `한 줄 정의`, `확인된 사실`, `단일 출처 정보`, `확인되지 않은 항목` section wording을 구성합니다.
    - `app/static/app.js:2329-2385`는 claim-coverage panel status/hint copy를 구성합니다.
    - `e2e/tests/web-smoke.spec.mjs:1003-1029`, `e2e/tests/web-smoke.spec.mjs:1129-1226`는 현재 browser-visible wording baseline을 잠그고 있습니다.
  - verification gap-only 축인 `docs/ACCEPTANCE_CRITERIA.md:1403-1404`는 user-visible shipped flow를 직접 막는 상태가 아니므로 기본 다음 슬라이스로 올리지 않았습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 `Web Investigation verified-vs-uncertain explanation tightening` 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-acceptance-criteria-product-spec-agreement-reinvestigation-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-acceptance-criteria-web-investigation-source-role-trust-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '34,60p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '286,322p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '100,106p'`
- `nl -ba app/static/app.js | sed -n '2329,2398p;2410,2465p'`
- `nl -ba core/agent_loop.py | sed -n '2448,2483p;3967,4160p;4537,4574p;5898,5932p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '995,1032p;1129,1226p;1848,1856p'`
- `rg -n "agreement-backed facts over noisy snippets|Reinvestigation should improve weak slots|stronger source consensus|better weak-slot reinvestigation|better suppression of noisy or irrelevant sources|agreement-over-noise|weak-slot reinvestigation|noisy single-source|uncertain" docs README.md plandoc -S`
- `rg -n "verified vs uncertain|교차 확인|단일 출처|미확인|fact-strength|summary bar|rendered_as|uncertain" app/static/app.js core tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs -S`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `awk '/[ \t]+$/{print FNR ":" $0}' .pipeline/claude_handoff.md verify/4/8/2026-04-08-acceptance-criteria-product-spec-agreement-reinvestigation-wording-clarification-verification.md`
- `ls -lt .pipeline/claude_handoff.md .pipeline/gemini_request.md .pipeline/gemini_advice.md .pipeline/operator_request.md`
- docs/pipeline-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- 다음 slice 전까지는 verified vs uncertain claim explanation이 response body / claim-coverage hint / verification label에 분산되어 있어, current shipped logic 대비 사용자 이해가 충분히 강하지 않을 수 있습니다.
- `docs/ACCEPTANCE_CRITERIA.md:1403-1404`의 regression-fixture / evaluation-coverage 항목은 여전히 남지만, 현재 shipped user flow를 직접 막는 상태는 아닙니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
