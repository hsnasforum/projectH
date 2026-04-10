## 변경 파일
- `.pipeline/claude_handoff.md`

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `NEXT_STEPS Current Checkpoint Web Investigation` wording clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- 검수 시작 시점의 same-day latest `/verify`와 existing `.pipeline/claude_handoff.md`는 직전 `PRODUCT_SPEC Product Modes` 슬라이스 기준이었으므로, persistent verification truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-next-steps-current-checkpoint-web-investigation-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/NEXT_STEPS.md:15`는 `/work` 주장대로 아래 current shipped web-investigation checkpoint truth를 반영하고 있습니다.
  - permission-gated secondary mode with `enabled` / `disabled` / `ask` per-session states
  - document-first guardrail
  - local JSON history with in-session reload and history-card badges
  - entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
  - claim-coverage panel with status tags and actionable hints
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:68-69`, `README.md:128`, `docs/ACCEPTANCE_CRITERIA.md:37`, `docs/ACCEPTANCE_CRITERIA.md:53`
  - deeper product-spec contract: `docs/PRODUCT_SPEC.md:151-155`, `docs/PRODUCT_SPEC.md:307-312`
- next slice는 같은 web-investigation wording family의 다음 entry-point current-risk reduction으로 `TASK_BACKLOG Web Investigation wording clarification` 한 개로 고정했습니다.
  - current `docs/TASK_BACKLOG.md:7`, `docs/TASK_BACKLOG.md:23-24`는 `secondary mode: permission-gated web investigation`, `Permission-gated web investigation with local history`, `Claim coverage and slot reinvestigation scaffolding` 수준의 generic wording에 머물러 있습니다.
  - 반면 current shipped truth는 이미 `docs/NEXT_STEPS.md:15`, `README.md:68-69`, `README.md:128`, `docs/PRODUCT_SPEC.md:151-155`, `docs/PRODUCT_SPEC.md:307-312`, `docs/ACCEPTANCE_CRITERIA.md:37`, `docs/ACCEPTANCE_CRITERIA.md:53`에 더 직접적으로 고정돼 있습니다.
  - `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:59`, `docs/PRODUCT_PROPOSAL.md:135`도 더 generic하지만, `docs/TASK_BACKLOG.md`가 current product identity와 implemented surface entry point라서 same-family tie-break상 먼저 좁히는 편이 맞습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 `TASK_BACKLOG Web Investigation wording clarification` 기준으로 갱신했습니다.

## 검증
- `git diff -- docs/NEXT_STEPS.md`
- `git diff --check -- docs/NEXT_STEPS.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '3,18p'`
- `nl -ba README.md | sed -n '68,69p;124,128p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '151,155p;307,312p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,38p;53,55p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,25p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;48,60p;129,136p'`
- `nl -ba docs/MILESTONES.md | sed -n '5,10p'`
- `rg -n "guarded secondary mode|permission-gated web investigation with local JSON history|secondary mode: permission-gated web investigation|Permission-gated web investigation with local history|web investigation history when secondary mode is used" README.md docs -S`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-next-steps-current-checkpoint-web-investigation-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-next-steps-current-checkpoint-web-investigation-wording-clarification-verification.md`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/TASK_BACKLOG.md:7`, `docs/TASK_BACKLOG.md:23-24`는 아직 current shipped web-investigation truth를 fully 직접 반영하지 못합니다.
- `docs/PRODUCT_PROPOSAL.md:26`, `docs/PRODUCT_PROPOSAL.md:59`, `docs/PRODUCT_PROPOSAL.md:135`도 더 높은 수준의 generic wording이 남아 있지만, 이번 handoff에서는 current product identity entry point인 backlog 한 개만 다음 슬라이스로 고정했습니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
