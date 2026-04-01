# 2026-03-31 non-object JSON request body 400 regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, non-object JSON request body의 400 응답을 직접 고정하는 regression 1건을 지시.
- `_read_json_body()`의 `isinstance(payload, dict)` guard는 이미 `WebApiError(400)`을 반환하지만 direct regression이 없었음.
- malformed request-body family의 네 번째이자 마지막 branch (malformed UTF-8 → malformed JSON syntax → empty body → non-object JSON).

## 핵심 변경
- `test_handler_returns_400_for_non_object_json_request_body` 추가 (`tests/test_web_app.py`)
  - `LocalOnlyHTTPServer`를 올려 `b'["not", "an", "object"]'`를 `/api/chat`에 POST
  - 검증: 응답 status 400, `ok: false`, error message에 "객체 형태" 포함
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 110 tests, OK (1.760s)
- `git diff --check -- app/web.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app handler test만 추가)

## 남은 리스크
- `_read_json_body()`의 모든 branch가 이제 direct regression으로 보호됨. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
