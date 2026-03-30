## 변경 파일
- `app/templates/index.html`
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

## 사용 skill
- `frontend-skill`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 남아 있던 핵심 리스크는 `corrected`를 truthfully 기록할 실제 사용자 surface가 아직 없다는 점이었습니다.
- 이번 라운드 목표는 그 리스크를 가장 작은 제품 UI로 해소하면서, 기존 grounded-brief artifact anchor와 approval-safe save flow를 깨지 않는 것이었습니다.
- 특히 correction submit과 save approval를 같은 행동으로 섞지 않고, original grounded-brief source message를 content source of truth로 유지해야 했습니다.

## 핵심 변경
- 최근 grounded-brief response surface 안에 작은 multiline correction editor를 추가하고, editor를 current draft text로 seed했습니다.
- 사용자가 editor 내용을 명시적으로 제출하면 original grounded-brief source message에 `corrected_text`와 `corrected_outcome.outcome = corrected`를 기록하도록 구현했습니다.
- 같은 source message에서 기존 `artifact_id`, `source_message_id`, `original_response_snapshot` anchor를 그대로 재사용했습니다.
- unchanged submit은 `accepted_as_is`로 추론하지 않고 validation error로 막았습니다.
- correction submit은 별도 `/api/correction` 경로로 분리했고, current save approval는 그대로 별도 흐름으로 유지했습니다.
- session serialization과 correction-submit response에서 corrected state를 노출하도록 맞췄고, task log에는 `correction_submitted`와 `corrected_outcome_recorded` audit event를 남기도록 했습니다.
- 문서는 현재 shipped truth에 맞춰 업데이트했습니다:
  - `corrected`는 이제 explicit edited text submit으로만 기록됨
  - `rejected`는 여전히 미구현
  - current pending approval preview는 여전히 original draft 기준임

## 검증
- 실행함:
  - `python3 -m py_compile app/web.py core/agent_loop.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "corrected_text|corrected_outcome|accepted_as_is|outcome = corrected|correction" app/templates/index.html app/web.py core/agent_loop.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “truthful corrected surface 부재” 리스크는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 새로 명확해진 남은 리스크는 correction submit 이후 current pending approval preview가 자동으로 corrected text로 rebasing되지 않는다는 점입니다.
- 이 동작은 현재 deliberately truthful합니다. correction artifact 기록과 save approval를 섞지 않기 위해서이며, 다음 슬라이스에서만 명시적으로 설계해야 합니다.
- content-level `rejected` surface는 여전히 미구현입니다. approval reject, retry, no-save, feedback `incorrect`와 섞지 않도록 별도 control이 필요합니다.
