# 2026-03-28 durable candidate projection implementation

## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-durable-candidate-projection-contract.md`

## 사용 skill
- `approval-flow-audit`: approval-backed save가 여전히 supporting evidence only인지, confirmation path와 섞이지 않았는지 확인했습니다.
- `doc-sync`: 구현 후 `durable_candidate` current payload 경계와 next slice를 root docs / plandoc에 맞췄습니다.
- `release-check`: py_compile, unittest, rg, diff-check, e2e 결과를 실제 실행 기준으로 정리했습니다.
- `work-log-closeout`: 오늘 closeout 형식과 검증 기록을 저장소 규칙에 맞춰 남겼습니다.

## 변경 이유
- 직전 closeout과 plandoc에서 남아 있던 가장 큰 리스크는 shipped `candidate_confirmation_record`를 실제 current payload의 first `durable_candidate` projection으로 아직 소비하지 못한다는 점이었습니다.
- 그 상태에서는 explicit confirmation이 audit trace로만 남고, same-source-message `eligible_for_review` projection contract가 코드에 닫히지 않아 이후 review queue를 열 근거가 부족했습니다.
- 이번 라운드는 별도 store, review queue, user-level memory를 열지 않고도 source-message-anchored read-only projection만 현재 구현에 추가하는 가장 작은 slice였습니다.

## 핵심 변경
- `app/web.py`의 session serialization 경로에 optional sibling `durable_candidate`를 추가했습니다. same source message의 현재 `session_local_candidate`와 현재 `candidate_confirmation_record`가 exact join(`artifact_id`, `source_message_id`, `candidate_id`, `candidate_updated_at`)될 때만 직렬화됩니다.
- first slice의 `durable_candidate`는 `candidate_scope = durable_candidate`, `supporting_confirmation_refs`, `has_explicit_confirmation = true`, `promotion_basis = explicit_confirmation`, `promotion_eligibility = eligible_for_review`, `created_at/updated_at = candidate_confirmation_record.recorded_at`를 가지며, `candidate_id`는 현재 source-message `session_local_candidate.candidate_id`를 그대로 재사용합니다.
- current `session_local_candidate` object는 그대로 유지했습니다. 여전히 `has_explicit_confirmation`, `promotion_basis`, `promotion_eligibility`를 갖지 않고, confirmation은 sibling trace로 남습니다.
- regression을 보강했습니다. web-app tests에는 projection 생성/소멸과 stale join omission을 추가했고, Playwright smoke의 candidate-confirmation 시나리오는 confirmation 이후 `durable_candidate` 존재를 현재 계약대로 검증하도록 업데이트했습니다.
- 문서는 current shipped `durable_candidate` projection, unchanged `session_local_candidate`, approval-backed save boundary, next slice를 review queue surface로 다시 정렬했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `git diff --check`
- `rg -n 'durable_candidate|candidate_confirmation_record|promotion_basis|promotion_eligibility|has_explicit_confirmation|session_local_candidate|historical_save_identity_signal|superseded_reject_signal' app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-durable-candidate-projection-contract.md`
- `make e2e-test`
  - 1차 실행은 기존 smoke expectation이 confirmation 이후에도 `durable_candidate` 부재를 기대해서 실패했습니다.
  - `e2e/tests/web-smoke.spec.mjs` expectation을 현재 계약으로 수정한 뒤 같은 `make e2e-test`를 다시 실행해 11개 전부 통과했습니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크 중 “explicit confirmation이 current payload의 first durable projection으로 아직 연결되지 않음”은 이번 라운드에서 해소했습니다.
- 이번 라운드에서 새로 줄인 리스크는 approval-backed save가 projection shortcut처럼 보일 수 있는 혼동입니다. 현재 projection은 explicit confirmation이 없으면 생기지 않고, save support는 계속 supporting evidence only로 남습니다.
- 여전히 남은 리스크는 operator가 `eligible_for_review` `durable_candidate`를 한곳에서 읽고 검토할 surface가 없다는 점입니다. 현재는 source-message payload에서만 보이며 review action / rollback / user-level memory는 아직 닫혀 있습니다.
- repeated-signal promotion은 여전히 막혀 있습니다. `candidate_family` alone으로는 merge나 second durable path를 열 수 없고, truthful recurrence key가 아직 없습니다.
- first slice가 source-message candidate id를 그대로 재사용하기 때문에, later review queue나 separate durable store가 생길 때 durable-scope id를 새로 mint할지 판단이 남아 있습니다.
