## 변경 파일
- `core/agent_loop.py`
- `app/web.py`
- `storage/session_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/27/2026-03-27-grounded-brief-corrected-outcome-capture.md`

## 사용 skill
- `approval-flow-audit`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 이어받은 리스크:
  - grounded-brief trace anchor와 normalized original-response snapshot은 구현됐지만 corrected outcome은 아직 비어 있었음
  - `artifact_id`와 `message_id`를 따라 현재 UX가 truthfully 지원하는 최소 accepted outcome을 어떻게 붙일지 아직 미정이었음
  - approval execute 후 system response와 original grounded-brief message 중 어디를 source of truth로 둘지 코드로 고정되지 않았음
- 이번 라운드에서 해소한 리스크:
  - grounded-brief original assistant message에 nested `corrected_outcome`을 실제로 추가함
  - 현재 UX가 명시적으로 지원하는 범위만 써서 `accepted_as_is`만 구현함
  - direct approved save와 approval-executed save 모두 같은 `artifact_id` anchor로 outcome을 복원할 수 있게 함
  - approval / task-log는 full outcome dump 대신 linkage 중심으로 유지함
- 여전히 남은 리스크:
  - corrected text 입력 surface가 없어서 `corrected` outcome은 아직 truthfully 캡처할 수 없음
  - approval reject는 content rejection과 동일하지 않아 `rejected` outcome으로 아직 매핑할 수 없음
  - separate artifact store, review queue, user-level memory는 여전히 future work임

## 핵심 변경
- `core/agent_loop.py`
  - `AgentResponse`에 optional `corrected_outcome`을 추가함
  - minimum shape를 nested object로 고정함:
    - `outcome`
    - `recorded_at`
    - `artifact_id`
    - `source_message_id`
    - optional `approval_id`
    - optional `saved_note_path`
  - direct save 분기에서는 original grounded-brief response 자체에 `accepted_as_is` outcome을 붙이도록 함
  - approval execute 분기에서는 새 system response에 outcome을 복사하지 않고, 기존 original grounded-brief source message를 찾아 outcome을 기록하도록 함
  - `corrected_outcome_recorded` task-log를 추가해 audit linkage를 남김
- `storage/session_store.py`
  - grounded-brief assistant message에서만 `corrected_outcome`을 normalize하도록 함
  - append 시 `source_message_id`를 현재 message id로 채울 수 있게 fallback normalization을 추가함
  - `record_corrected_outcome_for_artifact(...)`를 추가해 approval execute 후 existing source message를 patch할 수 있게 함
  - legacy message에 outcome이 없어도 기존 load가 깨지지 않도록 additive optional field로 유지함
- `app/web.py`
  - response payload와 session payload에 `corrected_outcome` 직렬화를 추가함
  - direct approved save 응답에서는 `corrected_outcome`을 그대로 노출함
  - approval execute system response에서는 `corrected_outcome`을 비워 두고, session 안 original grounded-brief message 쪽에서만 outcome을 확인하게 유지함
- 테스트
  - approval execute 후 original grounded-brief source message에 `accepted_as_is`가 기록되는지 검증함
  - direct approved save 응답과 session payload에 같은 `corrected_outcome`이 직렬화되는지 검증함
  - search summary direct save path도 같은 minimum contract를 따르는지 smoke regression을 추가함
- 문서
  - 현재 구현된 corrected-outcome 범위를 `accepted_as_is` only로 동기화함
  - `corrected` / `rejected`는 여전히 future라고 명시함
  - original grounded-brief message가 source of truth라는 점을 제품/아키텍처/인수 문서에 반영함

## 검증
- 실행함:
  - `python3 -m py_compile core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check -- core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - `rg -n "corrected_outcome|accepted_as_is|source_message_id|corrected_outcome_recorded" core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크 중 `grounded brief corrected-outcome capture 부재`는 해소했습니다.
- 이번 라운드에서 해소하지 않은 리스크:
  - corrected text를 입력하거나 비교할 실제 UX surface 부재
  - approval reject / reissue reason을 content outcome과 어떻게 분리할지에 대한 구현 부재
  - separate artifact store 없이 current message/session surface를 언제까지 source-of-truth로 유지할지
- 다음 slice 후보:
  - approval reject / reissue reason normalization을 같은 artifact anchor에 추가
  - `corrected` / `rejected`를 도입할 수 있는 truthful UX surface를 먼저 문서로 고정
  - later eval fixture가 `accepted_as_is`와 future corrected pairs를 어떻게 구분할지 trace contract 보강
