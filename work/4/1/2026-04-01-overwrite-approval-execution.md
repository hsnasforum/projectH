# 2026-04-01 overwrite approval execution

## 변경 파일
- `tools/write_note.py`
- `core/agent_loop.py`
- `app/templates/index.html`
- `tests/test_write_note.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 Approval UX 축으로 전환, `overwrite approval execution only` 단일 슬라이스 지시.
- 기존: overwrite가 감지되면 승인 버튼 비활성화 + "지원하지 않습니다" 메시지 → 사용자가 덮어쓰기 저장을 할 수 없음.
- `docs/TASK_BACKLOG.md`의 Not Implemented 항목이었던 core-loop gap.

## 핵심 변경
- `tools/write_note.py`:
  - `run()` 메서드에 `allow_overwrite: bool = False` 파라미터 추가
  - `allow_overwrite=True`이면 `FileExistsError` 대신 기존 파일 덮어쓰기 허용
- `core/agent_loop.py`:
  - `_execute_save_note_write`에 `allow_overwrite` 파라미터 추가, `write_note.run()`에 전달
  - `_execute_pending_approval`에서 `approval.overwrite`를 `allow_overwrite`로 전달
  - overwrite 실행 시 "기존 파일을 덮어쓰고 저장했습니다" 메시지 표시
  - `approval_granted` 로그에 `overwrite` 필드 추가
- `app/templates/index.html`:
  - overwrite일 때 승인 버튼 비활성화 제거 → 활성화
  - 경고 문구를 "지원하지 않습니다" → "기존 파일이 있습니다. 승인하면 덮어씁니다"로 변경
  - 두 곳(updateUI + showApprovalCard) 모두 수정
- `tests/test_write_note.py`:
  - `test_allows_overwrite_when_explicitly_approved`: allow_overwrite=True로 기존 파일 덮어쓰기 성공 확인
- `tests/test_web_app.py`:
  - `test_handle_chat_overwrite_approval_execution_replaces_existing_file`: reissue → overwrite 승인 → 기존 파일이 새 내용으로 교체되는 전체 흐름 확인

## 검증
- `python3 -m py_compile tools/write_note.py core/agent_loop.py`: 통과
- `python3 -m unittest -v tests.test_write_note tests.test_smoke tests.test_web_app`: 286 tests, OK (4.144s)
- `git diff --check -- tools/write_note.py core/agent_loop.py app/templates/index.html tests/test_write_note.py tests/test_web_app.py`: 통과

## 남은 리스크
- 기존 파일 내용은 덮어쓰기 시 복구 불가. approval-gated이므로 사용자 의도 없이 실행되지 않음.
- reissue 경로에서 overwrite 경고 문구("이미 파일이 있으므로 다른 저장 경로로 다시 요청해 주세요")는 남아있음. 이제 덮어쓰기가 가능하므로 이 문구도 경고 수준으로 완화할지는 후속 결정.
- docs sync(README, PRODUCT_SPEC, ACCEPTANCE_CRITERIA)는 이번 라운드에서 수행하지 않음.
