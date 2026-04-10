# docs: NEXT_STEPS emitted-transition-record layer intro shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-next-steps-emitted-record-layer-intro-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 실제로 `docs/NEXT_STEPS.md:237`를 닫았는지 다시 확인할 필요가 있었습니다.
- 같은 reviewed-memory planning family에서 다음 Claude 슬라이스를 한 개로 다시 고정할 필요가 있었습니다.

## 핵심 변경
- 최신 `/work`는 truthful했습니다. `docs/NEXT_STEPS.md:237`는 이제 `the trigger-source / emitted-record layer is now shipped above the shipped blocked trigger-source affordance`로 바뀌어 있고, 같은 블록의 `docs/NEXT_STEPS.md:239`, `docs/NEXT_STEPS.md:244`, `docs/NEXT_STEPS.md:261` 및 parallel planning wording인 `docs/MILESTONES.md:278`, `docs/MILESTONES.md:314`, `docs/MILESTONES.md:316`과 맞습니다.
- 다음 same-family residual은 root authority docs 쪽입니다. `docs/PRODUCT_SPEC.md:1473`는 아직 blocked boundary를 `without opening promotion or apply`로 적고, `docs/PRODUCT_SPEC.md:1483`, `docs/PRODUCT_SPEC.md:1490`, `docs/PRODUCT_SPEC.md:1492`, `docs/PRODUCT_SPEC.md:1493`, `docs/ARCHITECTURE.md:858`, `docs/ARCHITECTURE.md:865`, `docs/ARCHITECTURE.md:871`, `docs/ACCEPTANCE_CRITERIA.md:648`, `docs/ACCEPTANCE_CRITERIA.md:654`는 rollback/disable/conflict/transition semantics를 still-later/future처럼 적습니다.
- 실제 shipped contract는 `app/handlers/aggregate.py:392`, `app/handlers/aggregate.py:467`, `app/handlers/aggregate.py:529`, `app/handlers/aggregate.py:636`, `app/web.py:302`, `tests/test_web_app.py:7288`, `tests/test_web_app.py:7300` 기준으로 apply result, stop-apply, reversal, conflict visibility까지 이미 열려 있습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA reviewed-memory precondition family current-shipped apply/effect wording truth sync`로 고정했습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-next-steps-emitted-record-layer-intro-shipped-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-next-steps-unblock-semantics-shipped-truth-sync-verification.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '232,246p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '246,284p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '396,408p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '648,668p'`
- `nl -ba docs/MILESTONES.md | sed -n '268,282p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1470,1496p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '858,878p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '645,660p'`
- `rg -n "before any emitted transition record|before any apply vocabulary|reviewed-memory apply .*later|emitted transition record .*later|next unresolved layer|first emitted-transition-record layer|trigger-source .*later|may now emit|now also implemented" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md`
- `rg -n "aggregate-transition-apply|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility|effect_stopped|effect_reversed|conflict_visibility_checked" app/handlers/aggregate.py app/web.py tests/test_web_app.py tests/test_smoke.py`
- `nl -ba app/handlers/aggregate.py | sed -n '380,520p'`
- `nl -ba app/handlers/aggregate.py | sed -n '520,670p'`
- `nl -ba tests/test_web_app.py | sed -n '7260,7325p'`
- `git diff --check`
- Python unit test와 Playwright는 이번 라운드에서 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`의 reviewed-memory precondition summary가 현재 shipped apply/effect semantics보다 더 늦은 단계처럼 읽혀 root authority docs drift가 남아 있습니다.
