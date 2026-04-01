# 2026-03-31 malformed UTF-8 request 400 handling verification

## 변경 파일
- `verify/3/31/2026-03-31-malformed-utf8-request-400-handling-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-malformed-utf8-request-400-handling.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 `app/web.py`의 malformed UTF-8 request-body handling과 `tests/test_web_app.py` regression 1건만 추가했다고 적고 있으므로, 이번 검수에서는 그 코드/테스트 존재 여부, current MVP 범위 일탈 여부, 그리고 handler-level 변경에 필요한 최소 web-app 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 code/test 변경 주장은 현재 코드와 대체로 일치합니다.
- `app/web.py`의 `_read_json_body()`는 이제 `body.decode("utf-8")` 실패를 `WebApiError(400, "요청 본문이 올바른 UTF-8 형식이 아닙니다.")`로, `json.loads()` 실패를 `WebApiError(400, "JSON 요청 본문 형식이 올바르지 않습니다.")`로 좁게 정규화합니다. malformed UTF-8 body가 generic 500으로 빠지지 않도록 한 current-risk reduction입니다.
- `tests/test_web_app.py`에는 `test_handler_returns_400_for_malformed_utf8_request_body`가 실제로 추가되어 있고, `LocalOnlyHTTPServer`에 malformed UTF-8 body(`\x80\x81\x82\x83`)를 POST해 `400`, `ok: false`, `"UTF-8"` 포함 에러 메시지를 확인합니다.
- 범위도 current projectH의 document-first MVP 안에 있습니다. low-level request-validation hardening 1건이며, approval flow, reviewed-memory, entity-card quality, summary/search quality, broader web investigation UX 확장은 확인되지 않았습니다.
- docs 미변경 주장도 이번 round에서는 문제되지 않습니다. 현재 root docs는 raw malformed request-body validation contract를 별도 사용자-facing contract로 설명하지 않고 있고, 이번 변경은 browser-visible feature 추가보다 handler robustness 보정에 가깝습니다.
- 다만 automation truth는 닫히지 않았습니다. latest same-day `/verify`인 `verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md`는 `.pipeline/codex_feedback.md`를 `STATUS: needs_operator`로 남겼는데, 그 뒤 local canonical operator 승인 기록이나 새 Codex `/verify` 없이 `work/3/31/2026-03-31-uploaded-search-malformed-utf8-handoff.md`가 `.pipeline`을 `STATUS: implement`로 바꾸고, 그 다음 이번 implementation `/work`가 이어졌습니다. product truth는 맞아도 single-Codex pipeline truth는 이번 round에서 다시 흔들렸습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 107 tests`, `OK`)
- `git diff --check -- app/web.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-malformed-utf8-request-400-handling.md`
  - `verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md`
  - `work/3/31/2026-03-31-uploaded-search-malformed-utf8-handoff.md`
  - `app/web.py`
  - `tests/test_web_app.py`
  - `.pipeline/codex_feedback.md`
- 추가 확인
  - `rg -n "_read_json_body|UnicodeDecodeError|JSONDecodeError|malformed UTF-8|UTF-8 형식" app/web.py tests/test_web_app.py`
  - `rg -n "needs_operator|STATUS: implement|malformed UTF-8|operator|명시적으로 승인|uploaded search malformed utf8" .pipeline work verify`
  - `stat -c '%y %n' work/3/31/2026-03-31-uploaded-search-malformed-utf8-handoff.md work/3/31/2026-03-31-malformed-utf8-request-400-handling.md verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md .pipeline/codex_feedback.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `app/web.py` handler-level request-body validation hardening 1건이므로, `tests.test_web_app` 전체와 scoped `git diff --check`만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- product code/test truth는 맞지만, latest same-day `/verify` 이후 `needs_operator` 정지 상태를 local canonical operator 기록 없이 우회한 점 때문에 automation truth가 다시 흔들립니다.
- 외부 `except json.JSONDecodeError`는 현재 사실상 dead path에 가까워졌지만, 이번 slice 범위에서는 제거하지 않았습니다.
- dirty worktree가 여전히 넓어 다음 라운드도 unrelated 변경을 건드리지 않는 좁은 범위 통제가 필요합니다.
