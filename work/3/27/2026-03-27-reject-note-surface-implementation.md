## 변경 파일
- `app/templates/index.html`
- `app/web.py`
- `storage/session_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `e2e/README.md`
- `work/3/27/2026-03-27-reject-note-surface-implementation.md`

## 사용 skill
- `frontend-skill`
- `security-gate`
- `doc-sync`
- `e2e-smoke-triage`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout 기준으로 shipped `내용 거절` baseline과 reject smoke는 이미 올라가 있었지만, optional `reason_note` input surface는 아직 계약만 있고 실제 UI/저장/브라우저 검증이 없었습니다.
- 이번 라운드 목표는 same response-card `내용 판정` 구역 안에서만 reject-note를 가장 작게 구현하고, approval semantics나 corrected-save semantics를 건드리지 않은 채 source-message trace와 browser smoke를 함께 고정하는 것이었습니다.

## 핵심 변경
- `내용 판정` 박스 안에 short inline textarea와 secondary `거절 메모 기록` 버튼을 추가했습니다.
  - latest outcome이 `rejected`일 때만 보입니다.
  - blank submit은 disabled 상태로 유지하고, first slice에서는 manual blank-note clear UX를 만들지 않았습니다.
- 새 `/api/content-reason-note` 경로를 추가했습니다.
  - same grounded-brief source message의 `content_reason_record.reason_note`만 in-place update합니다.
  - `content_reason_record.recorded_at`만 note update 시각으로 refresh하고, `corrected_outcome.recorded_at`는 reject verdict 시각으로 유지합니다.
  - 별도 content-linked task-log event `content_reason_note_recorded`를 남깁니다.
- existing stale clearing contract는 그대로 유지했습니다.
  - later correction submit이나 explicit save supersession이 latest outcome을 `rejected` 밖으로 옮기면, stale `content_reason_record`와 `reason_note`도 source message에서 함께 사라집니다.
- focused regression과 browser smoke를 같이 보강했습니다.
  - service/unit: note update, blank guard, `corrected_outcome.recorded_at` 불변, correction/save supersession clearing
  - Playwright: reject 후에만 note surface 노출, blank submit disabled, note submit, pending approval 유지, later explicit save supersession
- 문서를 shipped truth 기준으로 동기화했습니다.
  - reject-note surface를 future가 아니라 current behavior로 반영했습니다.
  - smoke count는 8개 그대로 유지하되, reject scenario 설명을 same-card note update까지 포함하도록 바꿨습니다.

## 검증
- `python3 -m py_compile app/web.py core/agent_loop.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 144 tests in 1.957s`
  - `OK`
- `make e2e-test`
  - `8 passed (1.2m)`
- `rg -n "reason_note|content_reason_record|explicit_content_rejection|내용 거절|content_reason_note" app/templates/index.html app/web.py core/agent_loop.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- `git diff --check`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “reject-note surface 부재”와 “reject path browser smoke의 note-level coverage 부재”는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 의도적으로 남긴 범위 제한:
  - blank note를 explicit submit으로 지우는 UX는 아직 없습니다.
  - reject label taxonomy는 여전히 `explicit_content_rejection` 하나뿐입니다.
- 여전히 남은 리스크:
  - late flip after explicit original-draft save 같은 더 긴 history path에서 note wording을 별도 browser scenario로 늘리지는 않았습니다.
  - future slice에서 manual clear UX를 넣더라도 approval surface나 corrected-save semantics와 섞이지 않도록 response-card/source-message contract를 계속 유지해야 합니다.
