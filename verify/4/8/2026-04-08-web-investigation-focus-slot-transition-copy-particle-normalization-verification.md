## 변경 파일
- `verify/4/8/2026-04-08-web-investigation-focus-slot-transition-copy-particle-normalization-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-web-investigation-focus-slot-transition-copy-particle-normalization.md`가 focus-slot transition copy normalization, focused smoke, README sync를 truthfully 반영하는지 다시 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `focus-slot regressed-state explanation tightening` 라운드 기준이어서, 이번 latest `/work`를 반영한 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `app/static/app.js:2329-2346`에 `selectParticleEuroRo()` helper가 실제로 추가되어 focus-slot transition copy의 `로` / `으로`를 동적으로 고릅니다.
  - `app/static/app.js:2342-2346`에서 improved / regressed 문구가 `${curr}${particle}`로 바뀌어 `단일 출처로 약해졌습니다`가 실제로 렌더링됩니다.
  - `e2e/tests/web-smoke.spec.mjs:1098`의 regressed scenario assertion과 `README.md:194`의 scenario inventory도 `/work` 설명대로 갱신되어 있습니다.
- `/work`가 적은 focused verification도 결과 기준으로는 맞았습니다.
  - Playwright regressed scenario 1건 통과
  - Playwright improved scenario 1건 통과
  - `git diff --check` 통과
- 다만 이번 verification 중 Playwright 2건을 병렬로 띄운 첫 시도에서는 하나가 webServer port conflict(`OSError: [Errno 98] Address already in use`)로 실패했습니다.
  - 이는 verification harness contention이었고, 실패한 시나리오를 곧바로 순차 재실행해 통과를 확인했습니다.
  - 따라서 latest `/work`의 claimed checks truth에는 영향이 없고, 이번 `/verify`에는 실제 재실행 경위를 그대로 남깁니다.
- same-family user-visible wording polish인 focus-slot transition particle awkwardness는 이번 라운드로 닫혔다고 판단했습니다.
- 다음 slice는 `Docs NEXT_STEPS Playwright smoke count and claim-coverage inventory truth sync`로 고정했습니다.
  - `docs/NEXT_STEPS.md:16`은 아직 `Playwright smoke currently covers 75 browser scenarios`라고 적고 있지만, actual `e2e/tests/web-smoke.spec.mjs` count는 `82`입니다.
  - 이번 family에서 README의 80/81/82 시나리오는 truth-synced 되었지만, `docs/NEXT_STEPS.md` inventory는 아직 focus-slot improved/regressed smoke와 최신 scenario count를 반영하지 않아 docs truth drift가 남아 있습니다.
  - 이는 current shipped contract를 설명하는 docs mismatch이므로, 같은 family에서 다음 current-risk reduction으로 두는 편이 맞다고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 stale 상태에서 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-web-investigation-focus-slot-transition-copy-particle-normalization.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-web-investigation-focus-slot-regressed-state-explanation-tightening-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `git status --short`
- `rg -n "selectParticleEuroRo|단일 출처로 약해졌습니다|교차 확인으로 보강되었습니다|단일 출처으로" app/static/app.js e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md -S`
- `nl -ba app/static/app.js | sed -n '2328,2378p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1071,1102p'`
- `nl -ba README.md | sed -n '191,195p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,16p'`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `rg -n "75 browser scenarios|82\\.|81\\.|80\\.|browser scenarios|Playwright smoke currently covers" README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md -S`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "claim-coverage panel은 재조사 후 보강된 슬롯을 명확히 표시합니다" --reporter=line`
- `git diff --check`
- verification 중 Playwright 2건을 병렬로 먼저 띄웠고, 그중 regressed scenario 첫 시도는 webServer port conflict로 실패했습니다. 이후 해당 시나리오를 순차 재실행하여 통과를 확인했습니다.
- full browser suite(`make e2e-test`)는 이번 slice가 direct `renderClaimCoverage(...)` wording contract만 건드리는 범위라 재실행하지 않았습니다.

## 남은 리스크
- `docs/NEXT_STEPS.md:16`의 Playwright scenario count와 inventory가 current tree와 맞지 않아 docs truth drift가 남아 있습니다.
- verification harness 관점에서는 Playwright 시나리오를 병렬로 띄우면 webServer port contention이 다시 발생할 수 있으므로, 후속 verify에서는 같은 file 기반 isolated scenario를 순차로 돌리는 편이 안전합니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검수 범위 밖이라 손대지 않았습니다.
