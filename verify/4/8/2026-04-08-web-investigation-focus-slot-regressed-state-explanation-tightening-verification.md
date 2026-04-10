## 변경 파일
- `verify/4/8/2026-04-08-web-investigation-focus-slot-regressed-state-explanation-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-web-investigation-focus-slot-regressed-state-explanation-tightening.md`가 regressed focus-slot copy 보강, focused smoke, docs sync를 truthfully 반영하는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `focus-slot regressed-state explanation tightening` 전 라운드 기준이어서, 이번 latest `/work`를 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `app/static/app.js:2336-2337`에 `progress_state === "regressed"` 분기가 실제로 추가되어 `→ 재조사 결과: ${prev} → ${curr}으로 약해졌습니다. 추가 교차 검증이 권장됩니다.`를 출력합니다.
  - `e2e/tests/web-smoke.spec.mjs:1086-1100`에 regressed focus-slot browser scenario가 실제로 추가되어 있습니다.
  - `docs/PRODUCT_SPEC.md:291`, `docs/ACCEPTANCE_CRITERIA.md:41`, `README.md:194`의 high-level wording / scenario inventory도 이번 구현과 일치합니다.
- `/work`가 적은 focused verification도 실제로 다시 통과했습니다.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - Playwright 2건
  - `git diff --check`
- same-family current-risk reduction인 regressed-state explanation gap은 이번 라운드로 닫혔다고 판단했습니다.
- 다음 slice는 same-family user-visible improvement인 `Web Investigation focus-slot transition copy particle normalization`으로 고정했습니다.
  - current browser-visible string은 `app/static/app.js:2337`에서 `${curr}으로`를 고정으로 붙여 `교차 확인 → 단일 출처으로 약해졌습니다`처럼 어색한 한국어를 만듭니다.
  - 이 awkward copy는 `e2e/tests/web-smoke.spec.mjs:1098`와 `README.md:194`에도 그대로 잠겨 있습니다.
  - same family 안에서 사용자에게 바로 보이는 wording polish이며, broader docs drift(`docs/NEXT_STEPS.md:16`의 Playwright count 75 vs actual 82)보다 우선순위가 높습니다.
- `docs/NEXT_STEPS.md:16`의 Playwright scenario count drift는 이번에도 남아 있습니다.
  - `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `82`였습니다.
  - 다만 tie-break 순서상 same-family user-visible improvement를 먼저 두는 편이 맞다고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 stale 상태에서 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-web-investigation-focus-slot-regressed-state-explanation-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-web-investigation-claim-coverage-focus-slot-reinvestigation-copy-tightening-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `git status --short`
- `rg -n "regressed|약해졌습니다|buildFocusSlotExplanation|약해진 슬롯|82\\." app/static/app.js e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md README.md docs/NEXT_STEPS.md -S`
- `nl -ba app/static/app.js | sed -n '2328,2398p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1068,1115p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '287,316p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '38,44p;1403,1405p'`
- `nl -ba README.md | sed -n '190,196p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '107,115p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '100,106p'`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `rg -n "단일 출처으로|교차 확인으로 보강되었습니다|약해졌습니다" app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md -S`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다" --reporter=line`
- `git diff --check`
- full browser suite(`make e2e-test`)는 이번 slice가 direct `renderClaimCoverage(...)` wording contract만 건드리는 범위라 재실행하지 않았습니다.

## 남은 리스크
- current browser copy는 regressed case를 설명하긴 하지만 `단일 출처으로`처럼 target label particle이 어색해, 사용자에게 polished한 상태로 보이진 않습니다.
- `docs/NEXT_STEPS.md:16`의 Playwright scenario count는 여전히 current tree와 맞지 않아 docs truth drift가 남아 있습니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검수 범위 밖이라 손대지 않았습니다.
