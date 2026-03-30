# 2026-03-27 rejected content verdict implementation

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
- `work/3/27/2026-03-27-rejected-content-verdict-implementation.md`

## 사용 skill
- `frontend-skill`: response panel 안에서 `내용 거절` action을 correction / corrected-save / approval box와 겹치지 않는 작은 utility control로 배치했습니다.
- `approval-flow-audit`: content verdict와 approval reject를 섞지 않고, 기존 pending approval를 자동 취소하지 않는 additive 경로로 제한했습니다.
- `security-gate`: 별도 reject store 없이 source message와 로컬 task-log에만 얇게 기록하도록 유지했습니다.
- `doc-sync`: shipped behavior와 next slice를 README / product / architecture / acceptance / roadmap 문서에 맞춰 동기화했습니다.
- `release-check`: 실제 실행한 검증만 closeout과 최종 보고에 반영하도록 점검했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경, 검증, 남은 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- 직전 closeout에서는 `rejected` content-verdict contract만 문서로 고정되어 있었고, 실제 UI / session / task-log 경로는 아직 없었습니다.
- approval reject, no-save, retry, feedback `incorrect`를 content reject로 추론하지 않는 current contract를 유지하려면, grounded-brief response card에 distinct explicit control을 실제로 구현해야 했습니다.
- 이번 라운드는 corrected-save semantics나 approval semantics는 건드리지 않고, source message 기반의 최소 `rejected` 기록 경로만 additive하게 넣는 구현 작업으로 제한했습니다.

## 핵심 변경
- response panel에서 feedback 아래, correction box 위에 distinct `내용 판정` 구역과 `내용 거절` action을 추가했습니다.
- `내용 거절`은 approval box 바깥에서만 동작하고, 눌렀을 때 grounded-brief source message에 바로 아래를 기록합니다:
  - `corrected_outcome.outcome = rejected`
  - `artifact_id`
  - `source_message_id`
  - `recorded_at`
- 같은 source message에 approval-linked `approval_reason_record`와 별도인 `content_reason_record`를 추가했습니다:
  - `reason_scope = content_reject`
  - `reason_label = explicit_content_rejection`
  - `recorded_at`
  - `artifact_id`
  - `artifact_kind = grounded_brief`
  - `source_message_id`
- reject button helper copy는 아래 truth를 짧게 드러내도록 했습니다:
  - 저장 승인 거절과는 별도
  - 현재 열린 저장 승인은 자동 취소되지 않음
  - 아래 correction / corrected-save 흐름은 여전히 별도 사용 가능
- `storage/session_store.py`에서 `content_reason_record` 정규화와 `record_rejected_content_verdict_for_message()`를 추가했고, later correction submit이나 explicit save가 latest outcome을 `rejected`에서 다른 값으로 바꾸면 stale reject reason이 같이 사라지도록 정리했습니다.
- corrected-save approval execution은 기존 `preserve_existing` 동작을 좁혀, 기존 outcome이 실제로 `corrected`일 때만 그 값을 유지하도록 바꿨습니다. 덕분에 reject 뒤 corrected-save를 승인하면 latest outcome은 다시 `corrected`로 돌아옵니다.
- task-log에는 `content_verdict_recorded`와 `corrected_outcome_recorded`가 모두 남도록 했고, reject path의 detail에 `content_reason_record`도 포함했습니다.
- transcript / response quick meta에는 `내용 거절 기록됨`을 추가해 현재 verdict를 UI에서 바로 식별할 수 있게 했습니다.
- focused regression을 추가했습니다:
  - render-index에 new control / copy 존재 확인
  - `submit_content_verdict()`의 session / response / task-log shape 확인
  - reject 뒤 correction submit이 latest verdict를 `corrected`로 덮고 stale `content_reason_record`를 지우는지 확인
  - reject 뒤 corrected-save approval가 latest verdict를 다시 `corrected`로 되돌리는지 확인
- 문서는 이제 `rejected`를 current shipped behavior로 기록하고, 남은 것은 reject-note UX와 browser smoke 같은 후속 slice로만 남겼습니다.

## 검증
- 실행함: `python3 -m py_compile app/web.py core/agent_loop.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `git diff --check`
- 실행함: `rg -n '내용 거절|rejected|content_reject|explicit_content_rejection|corrected_outcome|approval_reason_record' app/templates/index.html app/web.py core/agent_loop.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크였던 “`rejected`를 truthfully 기록할 실제 control 부재”는 이번 라운드에서 해소했습니다.
- 이전부터 남아 있던 corrected-save reissue / overwrite edge와 stale snapshot diff indicator 부재는 이번 라운드 범위 밖이라 그대로 남아 있습니다.
- 이번 라운드 후 남은 가장 가까운 리스크는 `내용 거절` path가 아직 Playwright smoke에 올라가 있지 않다는 점입니다.
- `reason_note` 입력 surface는 여전히 없으므로, reject reason은 첫 fixed label only 계약에 머물러 있습니다.
- explicit original-draft save 이후 다시 `내용 거절`을 누르는 late flip path는 현재 contract상 허용되지만, 그 히스토리를 브라우저에서 얼마나 잘 설명할지에 대한 UI refinement는 아직 남아 있습니다.
