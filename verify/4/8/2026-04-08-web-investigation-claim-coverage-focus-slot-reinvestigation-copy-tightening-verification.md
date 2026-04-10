## 변경 파일
- `verify/4/8/2026-04-08-web-investigation-claim-coverage-focus-slot-reinvestigation-copy-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-web-investigation-claim-coverage-focus-slot-reinvestigation-copy-tightening.md`가 claim-coverage focus-slot copy, browser smoke, docs sync를 truthfully 반영하는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `entity-card stored-history tagged-header normalization` 라운드 기준이어서, 이번 latest `/work`를 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 구현·문서·rerun 주장은 대부분 truthful했습니다.
  - `app/static/app.js:2329-2345`에 `buildFocusSlotExplanation()`가 실제로 추가되어 focus-slot용 plain-language 설명을 만듭니다.
  - `app/static/app.js:2381-2395`에서 `is_focus_slot`일 때 전용 설명 라인을 출력하고, focus-slot에서는 기존 `변화:` meta를 숨깁니다.
  - `e2e/tests/web-smoke.spec.mjs:1031-1084`에 `/work`가 말한 2개 browser scenario가 실제로 추가되어 있습니다.
  - `docs/PRODUCT_SPEC.md:287-291`, `docs/ACCEPTANCE_CRITERIA.md:41`, `README.md:192-193`의 wording도 현재 구현과 맞습니다.
- `/work`가 적은 focused verification도 실제로 다시 통과했습니다.
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
  - Playwright 2건
  - `git diff --check`
- 다만 latest `/work`는 완전히 truthful하지는 않습니다.
  - `## 남은 리스크`에서 `regressed` edge case가 "현재 백엔드에서 생성하지 않는다"고 적었지만, current backend는 이미 `regressed`를 생성합니다.
  - 근거:
    - `core/agent_loop.py:4192-4200`는 `current_rank < previous_rank`일 때 `progress_state = "regressed"`와 `progress_label = "약해짐"`을 기록합니다.
    - `core/agent_loop.py:4303-4305`는 focus-slot regression summary도 별도로 만듭니다.
  - 반면 current browser helper는 `app/static/app.js:2345`에서 regressed 상태를 전용 문구 없이 generic `→ 재조사 대상 슬롯입니다.`로만 처리합니다.
- 따라서 이번 라운드는 "구현과 rerun은 맞지만, 남은 리스크 설명은 일부 부정확"으로 정리하는 편이 맞습니다.
- next slice는 same-family current-risk reduction인 `Web Investigation focus-slot regressed-state explanation tightening`으로 고정했습니다.
  - 이미 shipped backend가 `regressed`를 emit할 수 있으므로, current browser fallback generic copy는 실제 user-visible gap입니다.
  - 이 slice는 existing helper와 same browser scenario family 안에서 닫을 수 있어, 새로운 quality axis나 broader docs cleanup보다 우선입니다.
- `docs/NEXT_STEPS.md:16`은 여전히 Playwright smoke를 `75 browser scenarios`로 적고 있지만, actual `e2e/tests/web-smoke.spec.mjs` count는 `81`입니다 (`rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`).
  - 이는 current docs drift이지만, next default slice로는 user-visible current-risk reduction인 regressed-state copy tightening을 먼저 두는 편이 맞다고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 stale 상태에서 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-web-investigation-claim-coverage-focus-slot-reinvestigation-copy-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-web-investigation-entity-card-stored-history-tagged-header-normalization-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- app/static/app.js e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md README.md`
- `nl -ba app/static/app.js | sed -n '2320,2395p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1020,1108p'`
- `nl -ba core/agent_loop.py | sed -n '4188,4200p;4298,4306p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '286,320p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,60p;1398,1410p'`
- `nl -ba README.md | sed -n '186,198p'`
- `nl -ba docs/MILESTONES.md | sed -n '107,116p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '100,110p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,16p'`
- `rg -n "buildFocusSlotExplanation|재조사 대상 슬롯|재조사 후 보강된 슬롯|재조사 결과:|재조사 대상이지만|재조사 대상이며" app/static/app.js e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md README.md -S`
- `rg -n "regressed|약해짐|progress_state = \\\"regressed\\\"|progress_label = \\\"약해짐\\\"|재조사 대상 슬롯입니다" core/agent_loop.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs -S`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_reinvestigation_serializes_claim_progress`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 대상 슬롯의 진행 상태를 명확히 렌더링합니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다" --reporter=line`
- `git diff --check`
- full browser suite(`make e2e-test`)는 이번 slice가 shared browser helper/route family 전체를 바꾸는 수준이 아니어서 재실행하지 않았습니다.

## 남은 리스크
- current browser focus-slot copy는 `regressed` 상태를 전용 설명 없이 generic fallback으로만 보여 주므로, 실제 reinvestigation regression이 발생하면 사용자가 "무엇이 약해졌는지"를 한눈에 읽기 어렵습니다.
- `docs/NEXT_STEPS.md:16`의 Playwright scenario count는 현재 tree와 맞지 않아 docs truth drift가 남아 있습니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검수 범위 밖이라 손대지 않았습니다.
