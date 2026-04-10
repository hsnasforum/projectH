## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-project-brief-web-investigation-wording-clarification.md`가 claimed docs-only clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `TASK_BACKLOG Web Investigation wording clarification` 슬라이스 기준이어서, 최신 `/work`를 기준으로 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-project-brief-web-investigation-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/project-brief.md`는 `/work` 주장대로 아래 shipped web-investigation truth를 반영하고 있습니다.
  - `docs/project-brief.md:15-16`: permission-gated secondary mode with `enabled` / `disabled` / `ask` per-session states, local JSON history, in-session reload, history-card badges, and document-first guardrail
  - `docs/project-brief.md:79-81`: history-card badge 종류(answer-mode / verification-strength / source-role trust), entity-card / latest-update answer-mode distinction, entity-card strong-badge downgrade, and claim-coverage panel with status tags and actionable hints
  - `docs/project-brief.md:107`: web-investigation trace wording이 local JSON history 및 history-card badge traces 기준으로 더 구체화됨
- same-family source-of-truth와도 일치했습니다.
  - `docs/TASK_BACKLOG.md:7`, `docs/TASK_BACKLOG.md:23-24`
  - `README.md:68-69`
  - `docs/NEXT_STEPS.md:15`
  - `docs/PRODUCT_SPEC.md:151-155`, `docs/PRODUCT_SPEC.md:307-312`
  - `docs/ACCEPTANCE_CRITERIA.md:37`
- previous `.pipeline/claude_handoff.md`는 이미 닫힌 `project-brief Web Investigation wording clarification`을 계속 지시하고 있어 stale 상태였고, 이번 라운드에서 갱신했습니다.
- next slice는 같은 wording family의 다음 current-risk reduction으로 `PRODUCT_PROPOSAL Web Investigation wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:59`, `docs/PRODUCT_PROPOSAL.md:63`, `docs/PRODUCT_PROPOSAL.md:135`는 web investigation을 여전히 generic하게 기술합니다.
  - `docs/MILESTONES.md:7`도 더 높은 수준의 generic wording이 남아 있지만, `docs/PRODUCT_PROPOSAL.md`가 root-level decision frame / product boundaries / data assets entry point라서 same-family tie-break상 먼저 좁히는 편이 맞습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 `PRODUCT_PROPOSAL Web Investigation wording clarification` 기준으로 갱신했습니다.

## 검증
- `git diff -- docs/project-brief.md`
- `git diff --check -- docs/project-brief.md`
- `nl -ba docs/project-brief.md | sed -n '13,18p;68,83p;100,109p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,25p'`
- `nl -ba README.md | sed -n '60,75p;120,132p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '151,155p;307,312p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,38p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;54,64p;130,136p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,10p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `rg -n "guarded secondary mode|permission-gated web investigation with local JSON history|web investigation history when secondary mode is used|secondary mode: evidence-backed web investigation|permission-gated web investigation with local history|secondary mode: permission-gated web investigation|claim coverage / verification state and in-session history reload|history-card badges|document-first guardrail" README.md docs plandoc -S`
- `ls -lt .pipeline/claude_handoff.md .pipeline/gemini_request.md .pipeline/gemini_advice.md .pipeline/operator_request.md`
- `stat -c '%y %n' work/4/8/2026-04-08-project-brief-web-investigation-wording-clarification.md verify/4/8/2026-04-08-task-backlog-web-investigation-wording-clarification-verification.md .pipeline/claude_handoff.md`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:59`, `docs/PRODUCT_PROPOSAL.md:63`, `docs/PRODUCT_PROPOSAL.md:135`는 아직 current shipped web-investigation truth를 fully 직접 반영하지 못합니다.
- `docs/MILESTONES.md:7`은 여전히 high-level wording에 머물지만, 이번 handoff에서는 `PRODUCT_PROPOSAL` 한 파일만 다음 슬라이스로 고정했습니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
