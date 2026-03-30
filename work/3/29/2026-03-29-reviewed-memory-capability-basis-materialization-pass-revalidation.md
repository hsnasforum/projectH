# 2026-03-29 reviewed-memory capability-basis materialization-pass revalidation

## 변경 파일
- `work/3/29/2026-03-29-reviewed-memory-capability-basis-materialization-pass-revalidation.md`

## 사용 skill
- `mvp-scope`: current shipped capability layer와 future truthful basis layer를 다시 분리해, 이번 라운드에서 실제로 열 수 있는 범위를 재판정했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 basis source로 오해되지 않는지 다시 점검했습니다.
- `doc-sync`: root docs와 `plandoc` wording이 이미 current implementation truth와 맞는지 확인했습니다.
- `release-check`: 이번 라운드에서 실제 실행한 syntax, unittest, e2e, diff, `rg` 결과만 기준으로 상태를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 revalidation 결과를 기록했습니다.

## 변경 이유
- 이전 closeout에서 aggregate serializer는 future `reviewed_memory_capability_basis` layer를 probe하지만, current repo에 truthful later capability source가 아직 없어서 absence를 유지하도록 구현됐습니다.
- 이번 라운드의 질문은 그 상태가 여전히 맞는지, 아니면 current repo 안에 exact same-session aggregate scope에서 basis를 truthfully materialize할 source가 새로 존재하는지 재확인하는 것이었습니다.

## 핵심 변경
- current `app/web.py`, current tests, current docs를 다시 점검한 결과, truthful `reviewed_memory_capability_basis` source는 여전히 없습니다.
- 따라서 이번 라운드에서는 product code나 product docs를 더 넓히지 않았습니다.
- current truthful state는 그대로 유지됩니다:
  - `reviewed_memory_capability_basis`는 current payload에서 계속 absence
  - `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`
  - aggregate card `검토 메모 적용 시작`은 계속 visible-but-disabled
  - `reviewed_memory_transition_record`는 계속 absence
- `candidate_review_record`, queue presence, approval-backed save, historical adjunct, `task_log` replay가 basis source가 아니라는 점도 current code/tests/docs 전체에서 다시 확인했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - current repo 안에 truthful later capability-basis source가 실제로 있는지와, 없다면 absence를 계속 유지해야 하는지가 다음 구현 전 마지막 판단점이었습니다.
- 이번 라운드에서 해소한 리스크:
  - current implementation, regression, docs가 모두 같은 결론을 가리킨다는 점을 다시 확인했습니다. 즉 current repo에는 still truthful basis source가 없고, fake materialization을 열면 안 됩니다.
- 여전히 남은 리스크:
  - `reviewed_memory_capability_basis`를 truthfully materialize할 exact later source는 아직 없습니다.
  - 그래서 `unblocked_all_required`, enabled aggregate card, note input, emitted transition record, reviewed-memory apply result는 계속 later layer입니다.
  - repeated-signal promotion, cross-session counting, user-level memory도 계속 닫혀 있습니다.
