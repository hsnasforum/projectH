# 2026-03-28 candidate-recurrence-key-draft-implementation

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
- `plandoc/2026-03-28-recurrence-key-contract.md`
- `work/3/28/2026-03-28-candidate-recurrence-key-draft-implementation.md`

## 사용 skill
- `doc-sync`: 구현 후 recurrence key 상태를 root docs와 `plandoc`에 현재 구현 기준으로 맞췄습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `git diff --check`, `rg`, `make e2e-test` 결과만 기준으로 handoff 상태를 정리했습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 라운드 변경과 남은 리스크를 남겼습니다.

## 변경 이유
- 직전 closeout `2026-03-28-recurrence-key-contract.md`에서 남은 핵심 리스크는 repeated-signal promotion에 필요한 truthful recurrence identity가 아직 코드에 없다는 점이었습니다.
- `candidate_family` alone, fixed statement alone, review acceptance alone으로는 같은 rewrite preference recurrence를 정직하게 판단할 수 없어서, first deterministic source-message key를 실제 구현으로 닫을 필요가 있었습니다.

## 핵심 변경
- serialized grounded-brief source message에 optional sibling `candidate_recurrence_key`를 추가했습니다.
  - 위치는 `app/web.py`의 session serialization 경로입니다.
  - field는 `candidate_family`, `key_scope`, `key_version`, `derivation_source`, `source_candidate_id`, `source_candidate_updated_at`, `normalized_delta_fingerprint`, optional `rewrite_dimensions`, `stability`, `derived_at`입니다.
- key derivation basis를 explicit original-vs-corrected pair only로 고정했습니다.
  - `original_response_snapshot.draft_text`와 explicit `corrected_text`를 정규화한 뒤, `difflib.SequenceMatcher` opcode delta를 canonical JSON으로 만들고 `sha256` fingerprint를 계산합니다.
  - `rewrite_dimensions`는 deterministic `change_types`, `changed_segment_count`, `line_count_delta`, `character_count_delta`만 노출합니다.
- omission rule을 코드로 닫았습니다.
  - snapshot missing
  - corrected text missing
  - `corrected_outcome.outcome != corrected`
  - normalized no-op pair
  - current source-message `session_local_candidate` missing 또는 current candidate anchor mismatch
  - 위 경우는 `candidate_recurrence_key`를 아예 omit 합니다.
- basis boundary를 유지했습니다.
  - review acceptance, approval-backed save, `superseded_reject_signal`, `historical_save_identity_signal`는 key basis에 쓰지 않았습니다.
  - `session_local_candidate`, `durable_candidate`, `candidate_review_record` shape와 semantics는 그대로 두고, recurrence key만 additive read-only sibling으로 계산합니다.
- focused regression을 추가했습니다.
  - explicit corrected pair일 때만 key가 생기는지
  - same pair면 stable fingerprint가 나오는지
  - accepted-as-is / rejected-only / review-acceptance-without-pair path에서는 key가 생기지 않는지
  - review recording 후에도 key와 기존 durable/review semantics가 유지되는지

## 검증
- 실행:
  - `python3 -m py_compile app/web.py`
  - `python3 -m py_compile /home/xpdlqj/code/projectH/app/web.py /home/xpdlqj/code/projectH/tests/test_web_app.py /home/xpdlqj/code/projectH/tests/test_smoke.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - `git diff --check`
  - `rg -n "candidate_recurrence_key|normalized_delta_fingerprint|rewrite_dimensions|candidate_review_record|durable_candidate|session_local_candidate|candidate_family" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-recurrence-key-contract.md`
  - `make e2e-test`
- 결과:
  - `unittest`: 165 tests passed
  - `make e2e-test`: 11 passed
  - `git diff --check`: 통과

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - repeated-signal promotion에 필요한 truthful recurrence identity가 없어서 same-family merge나 broader durable promotion이 과장될 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - explicit original-vs-corrected pair only 기반의 deterministic source-message `candidate_recurrence_key` draft를 실제 코드와 회귀로 고정했습니다.
  - review acceptance, approval-backed save, historical adjunct가 recurrence key basis로 오인되는 경계를 구현으로 닫았습니다.
- 여전히 남은 리스크:
  - repeated-signal promotion, same-family merge helper, multi-source aggregation은 여전히 미구현이며 계속 닫혀 있습니다.
  - 첫 aggregation을 same-session only로 둘지 cross-session까지 열지 아직 open question입니다.
  - `rewrite_dimensions`를 어디까지 노출할지와 category별 recurrence threshold는 아직 후속 설계가 필요합니다.
