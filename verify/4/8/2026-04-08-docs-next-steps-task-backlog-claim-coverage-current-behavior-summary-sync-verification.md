## 변경 파일
- `verify/4/8/2026-04-08-docs-next-steps-task-backlog-claim-coverage-current-behavior-summary-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-next-steps-task-backlog-claim-coverage-current-behavior-summary-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, same-family claim-coverage docs가 정말로 다 닫혔는지 검증해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `docs/project-brief.md` / `docs/PRODUCT_PROPOSAL.md` sync 라운드 기준이었으므로, 이번 `docs/NEXT_STEPS.md` / `docs/TASK_BACKLOG.md` 반영 결과에 맞춰 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 구현과 rerun 자체는 맞았지만, 완전히 truthful하지는 않았습니다.
  - `docs/NEXT_STEPS.md:15`와 `docs/TASK_BACKLOG.md:24`는 실제로 `dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`를 포함하도록 갱신되어 있습니다.
  - `/work`가 적은 verification claim도 그대로 맞았습니다.
    - `rg -n "slot reinvestigation scaffolding" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`는 0건이었고,
    - `rg -n "focus-slot reinvestigation explanation" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md README.md docs/PRODUCT_SPEC.md` 기준으로 관련 synced docs에 새 wording이 들어가 있으며,
    - `git diff --check`도 clean이었습니다.
- 다만 `/work`의 `남은 리스크`에 적힌 “claim-coverage 관련 문서 동기화는 이제 전체 문서 계층에서 완료됨”은 사실과 다릅니다.
  - 실제 shipped UI는 [`app/static/app.js:2342`](/home/xpdlqj/code/projectH/app/static/app.js#L2342)~[`app/static/app.js:2356`](/home/xpdlqj/code/projectH/app/static/app.js#L2356)에서 focus slot 설명을 `보강됨`, `약해짐`, `아직 단일 출처`, `아직 확인되지 않음`, 그리고 조건부 `현재 교차 확인 상태`까지 나눠 렌더링합니다.
  - [`docs/PRODUCT_SPEC.md:291`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md#L291)와 [`docs/ACCEPTANCE_CRITERIA.md:41`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L41)은 이미 이를 `improved`, `regressed`, `stayed single-source`, `remains unresolved` 수준으로 설명합니다.
  - 반면 다수의 current/smoke docs는 아직 `improved/regressed/unchanged`로만 요약하고 있습니다.
    - `README.md:69`
    - `README.md:127`
    - `docs/MILESTONES.md:37`
    - `docs/PRODUCT_PROPOSAL.md:61`
    - `docs/TASK_BACKLOG.md:24`
    - `docs/TASK_BACKLOG.md:25`
    - `docs/project-brief.md:81`
    - `docs/ACCEPTANCE_CRITERIA.md:1337`
    - `docs/PRODUCT_SPEC.md:106`
    - `docs/PRODUCT_SPEC.md:310`
    - `docs/NEXT_STEPS.md:15`
    - `docs/NEXT_STEPS.md:16`
- 다음 exact slice는 `Docs claim-coverage focus-slot explanation state-granularity truth sync`로 고정했습니다.
  - 같은 family에서 남은 current-risk는 “설명 라인이 있다”는 사실보다, 그 설명이 실제로 어떤 상태를 구분하는지의 granularity가 문서마다 다르다는 점입니다.
  - 따라서 새 quality axis를 여는 것보다, 남아 있는 `improved/regressed/unchanged` 요약을 shipped 4-state semantics에 맞게 정리하는 편이 우선이라고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-docs-next-steps-task-backlog-claim-coverage-current-behavior-summary-sync.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-docs-project-brief-product-proposal-claim-coverage-current-behavior-explanation-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,16p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '23,25p'`
- `rg -n "claim coverage panel with status tags and actionable hints|claim-coverage panel with status tags and actionable hints|slot reinvestigation scaffolding|focus-slot reinvestigation explanation" docs README.md -S`
- `git diff -- docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `git diff --check`
- `rg -n "improved/regressed/unchanged" docs README.md -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '288,292p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '40,42p'`
- `nl -ba app/static/app.js | sed -n '2328,2370p'`

## 남은 리스크
- 다수 문서가 아직 focus-slot explanation을 `improved/regressed/unchanged`로만 요약해, 실제 shipped 4-state semantics와 미묘하게 어긋나 있습니다.
- 같은 family 문서 정리는 거의 닫혔지만, `/work` closeout의 “전체 문서 계층 완료” 같은 표현은 residual wording granularity까지 확인한 뒤에만 쓰는 편이 안전합니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
