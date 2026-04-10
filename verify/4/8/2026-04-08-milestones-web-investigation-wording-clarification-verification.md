## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-milestones-web-investigation-wording-clarification.md`가 claimed docs-only clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `MILESTONES Web Investigation wording clarification` 슬라이스 기준이어서, 최신 `/work`를 기준으로 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-milestones-web-investigation-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/MILESTONES.md:7`은 `/work` 주장대로 shipped web-investigation truth의 최소 milestone-level framing을 반영하고 있습니다.
  - permission-gated secondary mode with `enabled` / `disabled` / `ask` per-session states
  - document-first guardrail
- same-family web-investigation wording family도 root-level docs 기준으로 닫혔다고 확인했습니다.
  - `docs/NEXT_STEPS.md:15`
  - `docs/project-brief.md:16`
  - `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:65`
  - `docs/TASK_BACKLOG.md:7`
  - `docs/PRODUCT_SPEC.md:155`
- previous `.pipeline/claude_handoff.md`는 이미 닫힌 `MILESTONES Web Investigation wording clarification`을 계속 지시하고 있어 stale 상태였고, 이번 라운드에서 갱신했습니다.
- next slice는 새로운 current-risk reduction 축으로 `ACCEPTANCE_CRITERIA Web Investigation source-role trust wording clarification` 한 개로 고정했습니다.
  - current `docs/ACCEPTANCE_CRITERIA.md:53-55`는 answer-mode separation, claim-coverage source-role trust labels, response-origin compact trust labels를 아직 `In Progress`로 두고 있습니다.
  - 그러나 current implementation과 shipped tests는 이미 해당 surface를 구현·검증하고 있습니다.
    - `app/static/app.js:217-220`는 origin detail에 compact trust labels를 렌더링합니다.
    - `app/static/app.js:2241-2255`, `app/static/app.js:2367-2368`는 claim-coverage panel의 dedicated source-role trust line을 렌더링합니다.
    - `app/static/app.js:2893-2899`는 history-card source-role trust badges를 렌더링합니다.
    - `e2e/tests/web-smoke.spec.mjs:1031-1114`는 history-card trust badge/compact label contract를 검증합니다.
  - 반면 `docs/ACCEPTANCE_CRITERIA.md:24-28`은 같은 family의 다른 shipped surface를 이미 implemented acceptance로 다루고 있어, `:53-55`의 `In Progress` 표기는 현재 shipped contract를 misleading하게 만듭니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 `ACCEPTANCE_CRITERIA Web Investigation source-role trust wording clarification` 기준으로 갱신했습니다.

## 검증
- `git diff -- docs/MILESTONES.md`
- `git diff --check -- docs/MILESTONES.md`
- `nl -ba docs/MILESTONES.md | sed -n '5,12p'`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `rg -n "permission-gated secondary mode|Web investigation remains a secondary mode\\.|guarded secondary mode|permission-gated web investigation with local history|web investigation history when secondary mode is used|secondary mode: evidence-backed web investigation|document-first guardrail|claim coverage / verification state and in-session history reload" README.md docs plandoc -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '24,28p;50,56p'`
- `nl -ba app/static/app.js | sed -n '204,222p;2238,2378p;2888,2902p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1008,1024p;1031,1116p'`
- `ls -lt .pipeline/claude_handoff.md .pipeline/gemini_request.md .pipeline/gemini_advice.md .pipeline/operator_request.md`
- `stat -c '%y %n' work/4/8/2026-04-08-milestones-web-investigation-wording-clarification.md verify/4/8/2026-04-08-product-proposal-web-investigation-wording-clarification-verification.md .pipeline/claude_handoff.md`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/ACCEPTANCE_CRITERIA.md:53-55`는 아직 current shipped trust-label surface를 `In Progress`로 오해하게 만들 수 있습니다.
- 이 acceptance truth-sync까지 닫히면 web-investigation docs wording family는 한 단계 더 정리되지만, 이후에는 docs-only wording보다 actual quality improvements(`stronger source consensus`, `better weak-slot reinvestigation`)를 다시 우선 검토해야 합니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
