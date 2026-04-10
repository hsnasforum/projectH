## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `PRODUCT_SPEC Stored Evidence, Logs, And Feedback` wording clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- `PRODUCT_SPEC Current Outputs` / `Approval Points` / `Stored Evidence` top-level summary family를 닫은 뒤, 같은 문서에서 다음 Claude slice를 한 개로 고정해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-product-spec-stored-evidence-logs-feedback-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_SPEC.md:114-119`는 `/work` 주장대로 아래 storage/audit truth를 반영하고 있습니다.
  - session JSON: `messages`, `active_context`(correction-submit `summary_hint` follow-up basis), `pending_approvals`, `permissions`, timestamps
  - response metadata: evidence/source trust labels, summary chunks applied-range, response origin badge/answer-mode/verification/source-role, claim coverage status/fact-strength summary, feedback label+reason, source-message candidate/trace fields
  - computed current-session payload: `recurrence_aggregate_candidates`, `review_queue_items`
  - additive JSONL task log: requests/approvals/writes/rejects/reissues/cancels/feedback/candidate-confirmation/candidate-review events
  - local web-search history JSON: answer-mode/verification/source-role badges
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:56-64`, `README.md:68`, `docs/ACCEPTANCE_CRITERIA.md:81-99`
  - deeper product-spec contract: `docs/PRODUCT_SPEC.md:224-277`
- next slice는 같은 `PRODUCT_SPEC` top-level summary family에서 가장 자연스러운 후속으로 `PRODUCT_SPEC Web Investigation Rules wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:307-313`은 `read-only external search`, `permission-gated execution`, `response origin and source-role labeling`, `claim coverage and slot reinvestigation scaffolding`처럼 generic bullet에 머물러 있습니다.
  - 반면 current shipped truth는 이미 `README.md:68-69`, `README.md:128`, `docs/ACCEPTANCE_CRITERIA.md:37`, `docs/ACCEPTANCE_CRITERIA.md:53`, `docs/ACCEPTANCE_CRITERIA.md:1337-1341`, `docs/PRODUCT_SPEC.md:281-288`에 더 직접적으로 고정돼 있습니다.
  - web investigation rules는 one coherent user-visible contract family이므로 history badges, `WEB`/answer-mode/origin detail, entity-card/latest-update separation, claim coverage/fact-strength summary를 한 문단 안에서 같이 맞추는 편이 더 맞습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '112,121p;224,277p'`
- `nl -ba README.md | sed -n '56,69p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '80,99p'`
- `rg -n "Stored Evidence, Logs, And Feedback|session JSON|response metadata|task log|web-search history|response_feedback_recorded|active_context|permissions|claim coverage|summary chunks|response origin|grounded-brief trace|answer-mode|source-role" README.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '94,121p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '121,180p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '280,340p;380,450p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '305,321p'`
- `rg -n "Web Investigation Rules|permission-gated read-only external search|answer-mode|verification-strength|source-role|entity-card|latest-update|claim coverage|slot reinvestigation|history cards show|WEB badge|설명 카드|최신 확인" README.md docs/ACCEPTANCE_CRITERIA.md docs/PRODUCT_SPEC.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md -S`
- `nl -ba README.md | sed -n '68,69p;128,128p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,38p;53,53p;1337,1341p'`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:307-313`의 `Web Investigation Rules` top-level summary는 아직 current shipped web-investigation surface를 fully 직접 반영하지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
