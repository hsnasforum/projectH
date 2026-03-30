## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md`
- `plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 emitted transition record의 shape와 materialization contract는 닫혔지만, 현재 repo에 truthful first-action trigger source가 실제로 없는 상태에서 fake emitted record를 만들지 않는 current implementation round가 아직 코드와 회귀로 닫히지 않았습니다.
- 이번 라운드에서는 current aggregate payload에 future surface 진입점을 추가하되, real `future_reviewed_memory_apply` trigger / `canonical_transition_id` / `operator_reason_or_note` / `emitted_at` source가 없다는 current truth를 그대로 유지하는 absence-preserving implementation이 필요했습니다.

## 핵심 변경
- `app/web.py`에 aggregate-level helper `_build_recurrence_aggregate_reviewed_memory_transition_record(...)`를 추가하고, `recurrence_aggregate_candidates` item build 흐름에서 future emitted-record surface를 평가하도록 연결했습니다.
- helper는 current `reviewed_memory_transition_audit_contract`와 current `reviewed_memory_capability_status`가 exact shipped contract와 일치할 때만 future layer를 평가하지만, 현재 repo에는 truthful first-action trigger source가 없으므로 계속 `None`을 반환하도록 유지했습니다.
- 따라서 current aggregate payload는 `reviewed_memory_transition_record`를 여전히 내보내지 않고, `reviewed_memory_transition_audit_contract`는 그대로 `contract_only_not_emitted`를 유지합니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 ordinary aggregate payload에서 `reviewed_memory_transition_record`가 계속 absence인지, helper가 `None`인지, `task_log` replay-like data만으로 object가 생기지 않는지를 검증하는 회귀를 추가했습니다.
- root docs와 `plandoc`은 current implementation truth에 맞춰, “aggregate serializer가 future layer를 평가하지만 truthful trigger source가 없으므로 absence를 보존한다”와 “다음 slice는 emitted-record 합성이 아니라 operator-visible `future_reviewed_memory_apply` trigger source”라는 점으로 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_transition_record|transition_record_version|canonical_transition_id|operator_reason_or_note|record_stage|task_log_mirror_relation|future_reviewed_memory_apply" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “shape만 닫힌 emitted record를 current payload가 언제 truthfully materialize할 수 있는지 모른 채 later work가 fake record를 합성할 수 있음”은 이번 라운드에서 absence-preserving helper와 회귀로 줄였습니다.
- 이번 라운드에서 해소한 리스크는 current payload가 contract 존재, support trace, `task_log` replay만으로 emitted record처럼 보일 수 있는 여지였습니다.
- 여전히 남은 리스크는 truthful first emitted action source 자체가 없다는 점입니다. 다음 reopen은 emitted record object widening이 아니라, one exact operator-visible `future_reviewed_memory_apply` trigger source를 어디서 어떻게 만들지에 대한 더 작은 구현 slice여야 합니다.
