# 2026-03-31 empty request body 400 regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, empty request body의 400 응답을 직접 고정하는 regression 1건을 지시.
- `_read_json_body()`의 `content_length <= 0` guard는 이미 `WebApiError(400)`을 반환하지만 direct regression이 없었음.
- malformed request-body family의 세 번째이자 마지막 branch (malformed UTF-8 → malformed JSON syntax → empty body).

## 핵심 변경
- `test_handler_returns_400_for_empty_request_body` 추가 (`tests/test_web_app.py`)
  - `LocalOnlyHTTPServer`를 올려 `Content-Length: 0` + 빈 body를 `/api/chat`에 POST
  - 검증: 응답 status 400, `ok: false`, error message에 "요청 본문" 포함
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 109 tests, OK (1.791s)
- `git diff --check -- app/web.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app handler test만 추가)

## 남은 리스크
- `_read_json_body`의 non-object JSON branch(`isinstance(payload, dict)` 검사)도 direct regression 없음. 단, 이 branch는 request body parsing family보다 semantic validation에 가까워 별도 family로 볼 수 있음.
- dirty worktree가 여전히 넓음.
