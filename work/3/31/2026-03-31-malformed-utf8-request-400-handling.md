# 2026-03-31 malformed UTF-8 request 400 handling

## 변경 파일
- `app/web.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, malformed UTF-8 request body handling을 지시.
- 기존 `_read_json_body`에서 `body.decode("utf-8")`의 `UnicodeDecodeError`가 `WebApiError`로 변환되지 않아, malformed UTF-8 요청 시 generic 500(Internal Server Error)이 반환되었음.
- `json.JSONDecodeError`는 외부 catch(6633행)에서 잡히지만, `UnicodeDecodeError`는 잡히지 않아 `except Exception`(6637행)으로 빠져 500 응답.

## 핵심 변경

### production 변경 (`app/web.py`)
1. `_read_json_body`에서 `body.decode("utf-8")`와 `json.loads()`를 각각 별도 try-except로 감싸 `WebApiError(400)`으로 변환
   - `UnicodeDecodeError` / `ValueError` → `"요청 본문이 올바른 UTF-8 형식이 아닙니다."` (400)
   - `json.JSONDecodeError` / `ValueError` → `"JSON 요청 본문 형식이 올바르지 않습니다."` (400)
2. 기존 외부 `except json.JSONDecodeError`(6633행)는 `_read_json_body` 내부에서 먼저 잡히므로 사실상 도달하지 않지만, 방어적으로 유지

### 테스트 변경 (`tests/test_web_app.py`)
- `test_handler_returns_400_for_malformed_utf8_request_body` 추가
  - `LocalOnlyHTTPServer`를 짧게 올려 malformed UTF-8 body(`\x80\x81\x82\x83`)를 `/api/chat`에 POST
  - 검증: 응답 status 400, `ok: false`, error message에 "UTF-8" 포함

### 변경하지 않은 것
- UI, docs, approval flow, reviewed-memory, Playwright smoke 변경 없음
- `content_base64` validation semantics 확장 없음
- `core/agent_loop.py` uploaded partial-failure surface 재수정 없음
- entity-card ranking, summary/search quality 변경 없음

## 검증
- `python3 -m unittest -v tests.test_web_app`: 107 tests, OK (1.802s)
- `git diff --check -- app/web.py tests/test_web_app.py`: 통과
- `python3 -m unittest -v tests.test_smoke`: 실행하지 않음 (app/web.py handler 변경만이므로)

## 남은 리스크
- 외부 `except json.JSONDecodeError`(6633행)가 이제 사실상 dead code. 제거하면 더 깔끔하지만 방어적으로 유지함.
- dirty worktree가 여전히 넓음.
