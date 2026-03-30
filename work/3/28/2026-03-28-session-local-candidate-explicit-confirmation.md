# 2026-03-28 session_local_candidate explicit confirmation

## 변경 파일
- `storage/session_store.py`
- `app/web.py`
- `app/templates/index.html`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/28/2026-03-28-session-local-candidate-explicit-confirmation.md`

## 사용 skill
- `approval-flow-audit`: explicit confirmation이 save approval, corrected-save, approval reject/reissue와 섞이지 않도록 경계를 점검했습니다.
- `security-gate`: source-message anchored trace, stale confirmation clear, 별도 task-log event가 current candidate semantics를 넘어서지 않는지 확인했습니다.
- `doc-sync`: shipped explicit confirmation surface와 trace shape를 spec / architecture / acceptance / milestones / backlog / next-steps / README에 동기화했습니다.
- `release-check`: 실제 실행한 `py_compile`, focused unittest, `git diff --check`, 키워드 검색, `make e2e-test` 결과만 기준으로 검증 상태를 정리했습니다.
- `work-log-closeout`: 이번 구현 round의 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 직전 `2026-03-28-durable-candidate-promotion-guardrail` closeout에서 이어받은 핵심 리스크는 shipped `session_local_candidate`와 future `durable_candidate` 사이를 잇는 first candidate-linked explicit confirmation surface shape가 아직 구현되지 않았다는 점이었습니다.
- 이번 라운드의 목적은 그 confirmation을 실제 코드와 테스트로 추가하되, current source-message candidate / approval-backed save support / future durable projection 경계를 흐리지 않는 최소 구현으로 닫는 것이었습니다.

## 핵심 변경
- grounded-brief response card 안에 approval surface 밖의 작은 utility action `이 수정 방향 재사용 확인`을 추가했습니다. current `session_local_candidate`가 있을 때만 열리며, save approval / 내용 거절 / reject-note / feedback과 다른 positive reuse confirmation copy로 분리했습니다.
- same source message에 `candidate_confirmation_record`를 additive optional trace로 저장하도록 구현했습니다.
  - `candidate_id`
  - `candidate_family = correction_rewrite_preference`
  - `candidate_updated_at`
  - `artifact_id`
  - `source_message_id`
  - `confirmation_scope = candidate_reuse`
  - `confirmation_label = explicit_reuse_confirmation`
  - `recorded_at`
- current `session_local_candidate` payload는 그대로 유지했습니다. 이번 slice에서는 `has_explicit_confirmation`, `promotion_basis`, `promotion_eligibility`, `durable_candidate`를 emit하지 않고, confirmation은 sibling trace로만 유지합니다.
- confirmation은 approval-backed save와 별도 흐름으로 유지했습니다. save support는 계속 `session_local_candidate.supporting_signal_refs`에만 남고, explicit confirmation 없이는 confirmed candidate처럼 보이지 않도록 분리했습니다.
- stale confirmation guardrail을 넣었습니다. 현재 candidate의 `updated_at`와 confirmation record의 `candidate_updated_at`가 다르면 current session serialization에서 숨기고, 이후 correction / reject / non-corrected outcome이 기록되면 stored `candidate_confirmation_record`도 제거합니다.
- 별도 task-log event `candidate_confirmation_recorded`를 추가했습니다. detail에는 `candidate_id`, `artifact_id`, `source_message_id`, `candidate_family`, `candidate_updated_at`, `confirmation_scope`, `confirmation_label`을 남깁니다.
- 직전 closeout에서 남아 있던 “explicit confirmation surface shape 미정” 리스크는 이번 라운드에서 해소했습니다. 반면 truthful recurrence key와 future durable projection contract는 여전히 다음 slice 리스크로 남겼습니다.

## 검증
- 실행함: `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 159 tests in 1.759s`
  - `OK`
- 실행함: `git diff --check`
- 실행함: `rg -n "session_local_candidate|candidate_confirmation|explicit_reuse_confirmation|has_explicit_confirmation|correction_rewrite_preference|promotion_basis|promotion_eligibility|historical_save_identity_signal|superseded_reject_signal" app/templates/index.html app/web.py core/agent_loop.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 실행함: `make e2e-test`
  - 실패: `e2e/tests/web-smoke.spec.mjs` 10개 중 7개 실패, 3개 통과
  - 관찰: 실패는 `response-box`에 고정 fixture 문구를 기대하는 기존 시나리오들이 live `OLLAMA` 응답과 어긋나는 패턴이었고, 새 candidate confirmation action 자체를 직접 검증하는 전용 e2e 시나리오는 이번 라운드에 추가하지 않았습니다.

## 남은 리스크
- 이전 closeout에서 이어받은 “future explicit confirmation surface shape 미정” 리스크는 이번 라운드에서 source-message anchored `candidate_confirmation_record`와 response-card action으로 해소했습니다.
- 이번 라운드에서 새로 줄인 리스크는 approval-backed save가 explicit confirmation처럼 보이는 혼동과, stale confirmation이 current candidate를 잘못 대표할 수 있는 위험입니다.
- 여전히 남은 리스크는 future `durable_candidate` projection이 이 shipped confirmation trace를 어떤 최소 규칙으로 소비할지 아직 확정되지 않았다는 점입니다.
- repeated same-session recurrence key와 merge helper reopen 조건도 여전히 open question으로 남아 있습니다.
- `make e2e-test`는 현재 live `OLLAMA` 응답과 기존 고정 기대치가 어긋나 실패하므로, 브라우저 smoke를 계속 신뢰 가능한 회귀로 유지하려면 mock/runtime contract 정리 또는 기대치 재설정이 다음 정리 과제로 남습니다.
