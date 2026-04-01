# 2026-03-31 malformed JSON syntax 400 regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, malformed JSON syntax request body의 400 응답을 직접 고정하는 regression 1건을 지시.
- 이전 라운드에서 malformed UTF-8 branch는 regression으로 보호했으나, valid UTF-8이지만 JSON 문법이 깨진 branch는 직접 보호되지 않았음.
- `_read_json_body`의 `json.loads()` 경로는 이미 `WebApiError(400)`으로 변환하고 있어 production 변경 불필요 — test-only slice.

## 핵심 변경
- `test_handler_returns_400_for_malformed_json_syntax_request_body` 추가 (`tests/test_web_app.py`)
  - `LocalOnlyHTTPServer`를 올려 `b'{"session_id": "test", broken}'`를 `/api/chat`에 POST
  - 검증: 응답 status 400, `ok: false`, error message에 "JSON" 포함
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 108 tests, OK (1.782s)
- `git diff --check -- app/web.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (test_web_app handler test만 추가)

## 남은 리스크
- dirty worktree가 여전히 넓음.
