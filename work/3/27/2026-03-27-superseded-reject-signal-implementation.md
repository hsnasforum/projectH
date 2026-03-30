# 2026-03-27 superseded_reject_signal 구현

## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-superseded-reject-replay-helper-contract.md`
- `work/3/27/2026-03-27-superseded-reject-signal-implementation.md`

## 사용 skill
- `security-gate`: session serialization이 current-state canonical source를 흔들지 않고 task-log audit을 helper-only로 쓰는지 점검했습니다.
- `doc-sync`: shipped `superseded_reject_signal` 구현에 맞춰 spec / architecture / acceptance / roadmap 문구를 동기화했습니다.
- `release-check`: py_compile, focused unittest, diff cleanliness, 관련 키워드 검색까지 실제 실행 결과만 정리했습니다.
- `work-log-closeout`: 이번 round closeout을 저장소 규칙 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout 기준으로 shipped `session_local_memory_signal`은 current-state-only라 later correction/save 뒤 superseded reject / reject-note가 signal에서 사라질 수 있었습니다.
- durable-candidate 이전 단계에서 content-side explicit reject trace를 다시 볼 수 있는 최소 replay helper가 필요했지만, task-log를 canonical current-state source로 승격시키면 안 됐습니다.

## 핵심 변경
- `app/web.py` session serialization에 source-message-anchored optional `superseded_reject_signal`을 추가했습니다.
- helper는 same-anchor `content_verdict_recorded` / `content_reason_note_recorded`만 읽어 latest superseded reject 하나와 optional reject-note만 복원합니다.
- current `session_local_memory_signal.content_signal`은 그대로 두고, current verdict가 여전히 `rejected`이면 replay adjunct를 suppress 하도록 유지했습니다.
- ambiguous note association은 note를 붙이지 않고 omit 하도록 좁게 처리했습니다.
- focused regression은 current-state signal과 historical adjunct 분리, latest superseded reject note replay, ambiguous note omission을 고정했습니다.
- 문서는 replay helper가 future contract가 아니라 shipped narrow adjunct가 된 상태와 다음 open question이 save-axis `latest_approval_id` loss라는 점으로 갱신했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 150 tests in 1.744s`
  - `OK`
- `git diff --check`
- `rg -n "superseded_reject_signal|session_local_memory_signal|content_verdict_recorded|content_reason_note_recorded|content_reason_record|replay_source" storage/session_store.py app/web.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “superseded reject / reject-note가 current-state signal에서만 사라지고 replay helper가 없다”는 리스크는 이번 라운드에서 해소했습니다.
- helper는 same-anchor content-side audit만 보므로 save-axis `latest_approval_id` loss는 여전히 별도 open question으로 남습니다.
- helper는 task-log append order와 same-anchor match에 의존하므로, future에 broader history feed나 approval/save replay까지 같이 끌어오면 current verdict와 historical adjunct의 경계가 다시 흐려질 수 있습니다.
