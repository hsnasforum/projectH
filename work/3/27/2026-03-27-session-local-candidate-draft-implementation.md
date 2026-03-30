## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-session-local-candidate-normalization-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout까지 source-message-anchored signal과 narrow replay adjunct는 shipped 되었지만, 그 위의 first normalized `session_local_candidate`는 아직 문서 계약만 있고 실제 projection은 없었습니다.
- 이번 라운드에서는 current signal / historical adjunct / candidate / future durable candidate 경계를 흐리지 않으면서, 가장 작은 `correction_rewrite_preference` candidate draft를 실제 source-message serialization에 추가할 필요가 있었습니다.

## 핵심 변경
- `app/web.py`의 grounded-brief source message serialization에 optional computed `session_local_candidate`를 추가했습니다.
- first shipped family는 `correction_rewrite_preference`만 지원하고, same source message의 `original_response_snapshot.draft_text`와 non-empty `corrected_text`, 그리고 `corrected_outcome.outcome = corrected`가 모두 현재 상태에 남아 있을 때만 candidate를 만듭니다.
- candidate는 `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`과 flatten 하지 않고 별도 adjunct로 유지했습니다.
- `supporting_signal_refs`는 current `session_local_memory_signal.content_signal`만 primary basis로 잡고, current `save_signal.latest_approval_id`가 아직 살아 있을 때만 `session_local_memory_signal.save_signal`을 supporting evidence로 추가합니다.
- `historical_save_identity_signal`과 `superseded_reject_signal`은 first shipped candidate에서 supporting context조차 아직 참조하지 않도록 유지했습니다.
- 회귀 테스트로 아래를 고정했습니다:
  - initial / rejected-only path에서는 candidate가 생기지 않음
  - explicit corrected pair가 있을 때만 candidate가 생김
  - current save support가 있을 때만 `explicit_edit_plus_save_support`가 됨
  - later re-correct 뒤에는 save support가 빠지고 historical save adjunct와 candidate가 분리됨
  - accepted-as-is-only save path는 candidate basis가 아님
- root docs와 plandoc을 현재 shipped first slice 기준으로 동기화했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 155 tests in 1.805s`
  - `OK`
- `git diff --check`
- `rg -n "session_local_candidate|candidate_family|correction_rewrite_preference|supporting_signal_refs|evidence_strength|session_local_memory_signal|historical_save_identity_signal|superseded_reject_signal" storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “first normalized candidate를 실제로 내릴 때 signal/adjunct와 flatten 되지 않게 유지해야 한다”는 리스크는 이번 라운드에서 해소했습니다.
- approval-backed save를 current save support only로 제한했기 때문에, later correction 뒤 historical save adjunct를 candidate support로 다시 사용할지 여부는 여전히 열려 있습니다.
- 여전히 남은 핵심 리스크는 두 가지입니다:
  - first `session_local_candidate.statement`를 고정 문자열로 유지할지, 더 좁은 rewrite-summary helper로 바꿀지
  - 같은 세션에서 여러 correction pair가 생길 때 same-family draft를 그대로 둘지, 작은 merge helper를 둘지
