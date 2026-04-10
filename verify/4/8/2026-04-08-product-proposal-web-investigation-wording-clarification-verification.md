## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-product-proposal-web-investigation-wording-clarification.md`가 claimed docs-only clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `PRODUCT_PROPOSAL Web Investigation wording clarification` 슬라이스 기준이어서, 최신 `/work`를 기준으로 persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-product-proposal-web-investigation-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_PROPOSAL.md`는 `/work` 주장대로 아래 shipped web-investigation truth를 반영하고 있습니다.
  - `docs/PRODUCT_PROPOSAL.md:26`: permission-gated secondary mode with `enabled` / `disabled` / `ask` per-session states, document-first guardrail, local JSON history, in-session reload, history-card badges, answer-mode distinction, and claim-coverage panel shipped truth
  - `docs/PRODUCT_PROPOSAL.md:59-61`: history-card badge 종류(answer-mode / verification-strength / source-role trust), entity-card / latest-update answer-mode distinction, entity-card strong-badge downgrade, and claim-coverage panel with status tags and actionable hints
  - `docs/PRODUCT_PROPOSAL.md:65`: secondary mode wording이 permission-gated + document-first guardrail 기준으로 구체화됨
  - `docs/PRODUCT_PROPOSAL.md:137`: web-investigation trace wording이 local JSON history 및 history-card badge traces 기준으로 더 구체화됨
- same-family source-of-truth와도 일치했습니다.
  - `docs/project-brief.md:15-16`, `docs/project-brief.md:79-81`, `docs/project-brief.md:107`
  - `docs/TASK_BACKLOG.md:7`, `docs/TASK_BACKLOG.md:23-24`
  - `README.md:68-69`
  - `docs/NEXT_STEPS.md:15`
  - `docs/PRODUCT_SPEC.md:151-155`, `docs/PRODUCT_SPEC.md:307-312`
  - `docs/ACCEPTANCE_CRITERIA.md:37`
- previous `.pipeline/claude_handoff.md`는 이미 닫힌 `PRODUCT_PROPOSAL Web Investigation wording clarification`을 계속 지시하고 있어 stale 상태였고, 이번 라운드에서 갱신했습니다.
- next slice는 같은 wording family의 다음 current-risk reduction으로 `MILESTONES Web Investigation wording clarification` 한 개로 고정했습니다.
  - current `docs/MILESTONES.md:7`은 아직 `Web investigation remains a secondary mode.` 수준의 generic wording에 머뭅니다.
  - 이번 라운드의 `rg` 재대조 기준으로, same-family root-level 문서 중 남은 generic wording은 사실상 `docs/MILESTONES.md:7` 한 줄만 확인됐습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 `MILESTONES Web Investigation wording clarification` 기준으로 갱신했습니다.

## 검증
- `git diff -- docs/PRODUCT_PROPOSAL.md`
- `git diff --check -- docs/PRODUCT_PROPOSAL.md`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;54,66p;130,138p'`
- `nl -ba docs/project-brief.md | sed -n '13,18p;68,83p;100,109p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,25p'`
- `nl -ba README.md | sed -n '60,75p;120,132p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '151,155p;307,312p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,38p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,12p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,16p'`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `rg -n "guarded secondary mode|permission-gated web investigation with local JSON history|web investigation history when secondary mode is used|Secondary mode: evidence-backed web investigation|secondary mode: evidence-backed web investigation|Web investigation remains a secondary mode\\.|permission-gated secondary mode|document-first guardrail" README.md docs plandoc -S`
- `ls -lt .pipeline/claude_handoff.md .pipeline/gemini_request.md .pipeline/gemini_advice.md .pipeline/operator_request.md`
- `stat -c '%y %n' work/4/8/2026-04-08-product-proposal-web-investigation-wording-clarification.md verify/4/8/2026-04-08-project-brief-web-investigation-wording-clarification-verification.md .pipeline/claude_handoff.md`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/MILESTONES.md:7`은 아직 current shipped web-investigation truth를 직접 반영하지 못합니다.
- `docs/MILESTONES.md` 정리 후에는 같은 wording family의 root-level current-contract 문서 축이 사실상 닫힐 가능성이 높지만, 그 판단은 다음 verification 라운드에서 다시 확인해야 합니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, unrelated `work/` / `verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
