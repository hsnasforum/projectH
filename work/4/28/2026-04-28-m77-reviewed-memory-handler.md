# 2026-04-28 M77 reviewed memory handler

## 변경 파일

- `app/handlers/aggregate.py`
- `app/handlers/reviewed_memory.py`
- `app/web.py`
- `work/4/28/2026-04-28-m77-reviewed-memory-handler.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록의 필수 항목, 실제 검증 결과, 남은 리스크를 맞추기 위해 사용했습니다.

## 변경 이유

- M77 handoff가 `AggregateHandlerMixin`에 남아 있던 reviewed-memory lifecycle 메서드를 별도 handler mixin으로 분리하도록 지정했습니다.
- 이번 라운드는 동작 변경이 아니라 handler 소유 경계를 나누는 구조 정리입니다.

## 핵심 변경

- `app/handlers/reviewed_memory.py`를 새로 만들고 `ReviewedMemoryHandlerMixin`에 `emit_aggregate_transition`, `apply_aggregate_transition`, `confirm_aggregate_transition_result`, `stop_apply_aggregate_transition`, `reverse_aggregate_transition`, `check_aggregate_conflict_visibility`를 옮겼습니다.
- `app/handlers/aggregate.py`에서는 위 6개 reviewed-memory lifecycle 메서드와 해당 import를 제거하고, docstring을 candidate confirmation/review 전용으로 갱신했습니다.
- `app/web.py`에서 `ReviewedMemoryHandlerMixin`을 import하고 `WebAppService` 상속 목록에 `CorrectionHandlerMixin` 뒤로 연결했습니다.
- 테스트 파일은 handoff 지시에 따라 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`: `c106453fa2bf1f9fe4f54fc4cf82c6404721c395cc3ad53a3fd59e206a9b1e8f` 일치 확인.
- `git switch -c feat/m77-axis1-reviewed-memory-handler`: 실패. `.git/refs/heads/...` lock 생성이 read-only file system으로 거부되었습니다.
- `python3 -m py_compile app/handlers/reviewed_memory.py app/handlers/aggregate.py app/web.py`: 통과.
- `python3 -m unittest tests.test_web_app 2>&1 | tail -3`: 실패. `Ran 322 tests in 45.747s`, `FAILED (errors=10)`.
- `python3 -m unittest tests.test_web_app > /tmp/m77_test_web_app.log 2>&1`: 실패 로그 확인. 10건 모두 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 경로의 `PermissionError: [Errno 1] Operation not permitted`로, 테스트 서버 소켓 생성이 sandbox에서 차단된 양상입니다.
- `python3 -m unittest tests.test_smoke 2>&1 | tail -3`: 통과. `Ran 150 tests in 1.569s`, `OK`.
- `git diff --check -- app/handlers/reviewed_memory.py app/handlers/aggregate.py app/web.py`: 통과.

## 남은 리스크

- 현재 작업은 브랜치 생성 실패 때문에 `feat/m76-doc-sync-m72-m75` 위의 dirty worktree에 남아 있습니다. commit, push, PR 생성은 handoff 규칙에 따라 수행하지 않았습니다.
- `tests.test_web_app` 전체는 이 sandbox에서 local HTTP server 소켓 생성이 막혀 완료하지 못했습니다. reviewed-memory handler dispatch 관련 테스트도 같은 소켓 생성 실패 묶음에 포함되어 있어, 소켓 허용 환경에서 재실행하면 회귀 여부를 더 직접 확인할 수 있습니다.
- dist 생성, E2E, broad unittest는 handoff 범위를 넘기지 않기 위해 실행하지 않았습니다.
