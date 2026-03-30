# 2026-03-28 session_local_candidate draft implementation

## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md` (`현재 워크트리에서 untracked 상태`)
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/28/2026-03-28-session-local-candidate-draft-implementation.md`

## 사용 skill
- `mvp-scope`: current signal / historical adjunct / normalized candidate / future durable candidate 경계를 다시 좁혀 roadmap 문구를 정리했습니다.
- `approval-flow-audit`: approval-backed save가 first candidate의 primary basis로 오해되지 않도록 current `save_signal` supporting-only 규칙을 점검했습니다.
- `security-gate`: session serialization과 task-log helper가 canonical current-state source를 넘어서지 않는지 확인했습니다.
- `doc-sync`: candidate shape, evidence strength, next-step wording을 구현 truth와 맞게 문서에 동기화했습니다.
- `release-check`: 실제 실행한 `py_compile`, focused unittest, `git diff --check`, 키워드 검색 결과만 기준으로 검증 상태를 정리했습니다.
- `work-log-closeout`: 이번 구현 round의 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 2026-03-27 closeout들에서 남아 있던 핵심 리스크는 first `session_local_candidate`를 실제 코드로 넣되 current signal / historical adjunct / approval-backed save의 경계를 흐리지 않는 것이었습니다.
- 현재 워크트리에는 candidate 초안 구현이 이미 들어와 있었지만, 이번 라운드에서 고정한 계약과 비교하면 `evidence_strength`가 save support에 따라 두 단계로 넓어져 있어 first slice를 더 보수적으로 좁힐 필요가 있었습니다.

## 핵심 변경
- `app/web.py`의 computed `session_local_candidate`를 `correction_rewrite_preference` 1개 family로 유지하면서, `evidence_strength`를 단일 보수값 `explicit_single_artifact`로 고정했습니다.
- same source message의 explicit original-vs-corrected pair가 없거나, normalized original draft와 `corrected_text`가 동일하면 candidate를 만들지 않도록 current omission rule을 회귀 테스트로 고정했습니다.
- current `save_signal.latest_approval_id`가 남아 있을 때만 `session_local_memory_signal.save_signal`을 `supporting_signal_refs`에 추가하되, approval-backed save는 여전히 supporting evidence only로 남기고 evidence level을 올리지 않도록 유지했습니다.
- `superseded_reject_signal` / `historical_save_identity_signal`은 계속 candidate basis 바깥에 두고, candidate가 current signal들과 flatten되지 않는 구조를 유지했습니다.
- 문서는 first candidate statement 고정, 단일 conservative evidence strength, next step을 repeated same-session merge helper / promotion guardrail 쪽으로 이동시키는 방향으로 동기화했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 156 tests in 1.661s`
  - `OK`
- `git diff --check`
- `rg -n "session_local_candidate|candidate_family|correction_rewrite_preference|supporting_signal_refs|evidence_strength|session_local_memory_signal|historical_save_identity_signal|superseded_reject_signal" storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “first candidate statement를 helper로 넓힐지 여부” 리스크는 이번 라운드에서 fixed deterministic sentence 유지로 해소했습니다.
- 이전 closeout에서 남아 있던 “approval-backed save가 first candidate basis로 과장될 수 있다”는 리스크도 이번 라운드에서 single conservative `evidence_strength`와 supporting-only ref 유지로 줄였습니다.
- 여전히 남은 리스크는 repeated same-session `correction_rewrite_preference` draft를 source-message 단위로만 둘지, 작은 merge helper를 둘지 미정이라는 점입니다.
- `durable_candidate`, review queue, user-level memory, broader save-history replay는 이번 라운드에서도 의도적으로 열지 않았으므로 promotion guardrail 정의는 다음 slice로 남습니다.
