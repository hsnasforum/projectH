## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-superseded-reject-replay-helper-contract.md`
- `work/3/27/2026-03-27-superseded-reject-replay-helper-contract.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout 기준으로 shipped `session_local_memory_signal`은 current-state-only projection이라 later correction/save 뒤 superseded reject / reject-note가 source message에서 사라지면 signal에서도 빠질 수 있었습니다.
- durable-candidate 이전 단계에서 이 content-side superseded trace를 다시 surface에 올릴 가치가 있는지 먼저 좁혀야 했고, task-log를 canonical source로 승격시키지 않는 최소 계약이 필요했습니다.

## 핵심 변경
- 이번 라운드에서는 `Option B`를 선택했습니다.
- shipped `session_local_memory_signal`은 계속 current-state-only, read-only, source-message-anchored projection으로 유지합니다.
- next slice로는 same anchor의 superseded `rejected` verdict와 optional reject-note만 다루는 좁은 historical adjunct를 권고했습니다.
- 추천 shape는 source-message serialization 아래 optional `superseded_reject_signal` 하나이며, current `content_signal`과 분리된 audit-derived helper로만 둡니다.
- 이 helper는 saved body copy, approval preview body copy, approval-friction relabeling, inferred preference, cross-artifact aggregate를 replay하지 않도록 문서로 고정했습니다.
- `latest_approval_id` loss 같은 save-axis 이슈는 별도 open question으로 분리했습니다.

## 검증
- 실행함: `rg -n "session_local_memory_signal|replay helper|superseded reject|audit-only|content_reason_record|latest_approval_id|durable_candidate" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-superseded-reject-replay-helper-contract.md`
- 실행함: `git diff --check`
- 실행하지 않음: `python3 -m py_compile ...`
- 실행하지 않음: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행하지 않음: `make e2e-test`

## 남은 리스크
- current-state-only `session_local_memory_signal`과 future replay adjunct가 함께 들어오면 operator가 current verdict와 replayed superseded verdict를 혼동할 수 있으므로 field separation과 copy naming을 매우 보수적으로 유지해야 합니다.
- first replay helper를 task-log full replay나 mini history list로 넓히면 current MVP 범위를 바로 넘게 됩니다.
- `save_signal.latest_approval_id`가 later explicit action 뒤에 떨어질 수 있는 save-axis limitation은 여전히 남아 있으며, 이번 라운드에서는 intentionally 건드리지 않았습니다.
