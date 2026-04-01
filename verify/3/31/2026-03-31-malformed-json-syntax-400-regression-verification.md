# 2026-03-31 malformed JSON syntax 400 regression verification

## 변경 파일
- `verify/3/31/2026-03-31-malformed-json-syntax-400-regression-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-malformed-json-syntax-400-regression.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-codex-auto-slice-tiebreak-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 malformed request-body family의 same-family current-risk follow-up으로 `tests/test_web_app.py` regression 1건만 추가했다고 적고 있으므로, 이번 검수에서는 그 테스트 존재 여부, production 코드 불변 여부, current MVP 범위 일탈 여부, 그리고 필요한 최소 web-app 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 test-only 변경 주장은 현재 코드와 일치합니다.
- `tests/test_web_app.py`에는 `test_handler_returns_400_for_malformed_json_syntax_request_body`가 실제로 추가되어 있고, `LocalOnlyHTTPServer`에 valid UTF-8 but malformed JSON syntax body(`b'{"session_id": "test", broken}'`)를 `/api/chat`으로 보내 `400`, `ok: false`, `"JSON"` 포함 에러 메시지를 검증합니다.
- `app/web.py`의 `_read_json_body()`는 직전 malformed UTF-8 라운드에서 이미 `json.loads()` 실패를 `WebApiError(400, "JSON 요청 본문 형식이 올바르지 않습니다.")`로 정규화하고 있으므로, 이번 round에서 production 코드 변경이 없다는 latest `/work` 주장도 맞습니다. 수정 시각도 `app/web.py`가 직전 implementation round 시점에 머물고 `tests/test_web_app.py`만 이번 round에서 더 새롭습니다.
- 범위는 current projectH의 document-first MVP 안에 있습니다. browser-visible feature 추가가 아니라 request-validation hardening family의 focused regression 1건이며, approval flow, reviewed-memory, entity-card quality, uploaded partial-failure surface, docs contract 확장은 확인되지 않았습니다.
- same-family current-risk-first tie-break 규칙과도 일치합니다. malformed request-body family는 malformed UTF-8 branch를 direct regression으로 닫은 뒤, 이번 round에서 malformed JSON syntax branch를 direct regression으로 닫았습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 108 tests`, `OK`)
- `git diff --check -- app/web.py tests/test_web_app.py`
  - 통과 (출력 없음)
- `git diff --check -- tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-malformed-json-syntax-400-regression.md`
  - `verify/3/31/2026-03-31-codex-auto-slice-tiebreak-verification.md`
  - `tests/test_web_app.py`
  - `app/web.py`
- 추가 확인
  - `rg -n "test_handler_returns_400_for_malformed_json_syntax_request_body|test_handler_returns_400_for_malformed_utf8_request_body|JSON 요청 본문 형식이 올바르지 않습니다" tests/test_web_app.py app/web.py`
  - `stat -c '%y %n' app/web.py tests/test_web_app.py work/3/31/2026-03-31-malformed-utf8-request-400-handling.md work/3/31/2026-03-31-malformed-json-syntax-400-regression.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests/test_web_app.py` handler regression 1건만 추가한 test-only slice였고, `app/web.py` runtime contract 자체는 직전 round와 동일했으므로 `tests.test_web_app` 전체와 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- malformed request-body family에서는 empty-body branch(`요청 본문이 필요합니다.`)와 non-object JSON branch(`JSON 본문은 객체 형태여야 합니다.`)가 여전히 direct regression으로는 닫혀 있지 않습니다.
- dirty worktree가 여전히 넓어 다음 라운드도 unrelated 변경을 건드리지 않는 좁은 범위 통제가 필요합니다.
