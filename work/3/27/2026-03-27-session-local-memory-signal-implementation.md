# 2026-03-27 session-local-memory-signal 구현

## 변경 파일
- `storage/session_store.py`
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/27/2026-03-27-session-local-memory-signal-implementation.md`

## 사용 skill
- `security-gate`: 세션 직렬화와 저장소 helper가 local-first / approval-based 경계를 넘지 않도록 확인했습니다.
- `doc-sync`: session-local projection이 shipped truth가 된 부분을 제품/아키텍처/acceptance/roadmap 문서에 같이 반영했습니다.
- `release-check`: 문법, focused regression, diff cleanliness, 관련 키워드 검색까지 실제 실행 결과만 맞춰 정리했습니다.
- `work-log-closeout`: 오늘 round closeout을 저장소 규칙에 맞는 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout에서 session-local memory signal은 계약만 고정되어 있었고, 실제 코드는 아직 source-message anchor에서 read-only projection을 계산하지 못했습니다.
- 다음 단계로 durable candidate나 user-level memory를 열기 전에, current persisted session state만으로 recoverable 한 explicit traces를 같은 anchor에서 읽을 수 있어야 했습니다.
- approval friction / content verdict / save history를 한 label로 뭉개지 않고, current-state-only limitation을 드러내는 가장 작은 구현이 필요했습니다.

## 핵심 변경
- `SessionStore`에 same-anchor lookup helper를 추가해 `artifact_id + source_message_id` 기준으로 latest approval reason과 latest save linkage를 current session state에서 계산하도록 했습니다.
- grounded-brief source message 직렬화에 computed optional `session_local_memory_signal`을 추가했습니다.
- signal shape는 `content_signal`, `approval_signal`, `save_signal` 세 축으로 분리했고, saved body / approval preview body / inferred preference는 넣지 않았습니다.
- first slice답게 separate memory store, schema bump, task-log replay canonicalization 없이 끝냈습니다.
- 회귀 테스트는 초기 grounded-brief source message signal, approval reject + corrected-save 분리, stale reject-note가 current-state signal에서 빠지고 save linkage는 남는 long-history case를 고정했습니다.
- 문서는 계약 문구를 shipped 구현 기준으로 바꾸고, next/backlog는 이제 “첫 signal 추가”가 아니라 “current-state-only limitation 다음에 무엇을 할지”로 이동시켰습니다.

## 검증
- `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 148 tests in 1.756s`
  - `OK`
- `git diff --check`
- `rg -n "session_local_memory_signal|content_signal|approval_signal|save_signal|content_reason_record|approval_reason_record|save_content_source" storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “first session-local signal이 아직 계약뿐이고 실제 projection이 없다”는 리스크는 이번 라운드에서 해소했습니다.
- 이번 라운드에서는 current-state-only projection까지는 고정했지만, superseded reject / reject-note를 다시 보여 주는 replay helper는 아직 없습니다.
- save axis의 `latest_approval_id`는 current session state에 여전히 노출되는 경우에만 보존됩니다. later correction 같은 explicit action 뒤에는 saved path/history는 남아도 approval id가 빠질 수 있습니다.
- response-level top mirror나 cross-artifact aggregate summary는 아직 없고, 이번 slice에서도 intentionally 추가하지 않았습니다.
