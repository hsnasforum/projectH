# 2026-03-31 uploaded search malformed utf8 handoff

## 변경 파일
- `.pipeline/codex_feedback.md`
- `work/3/31/2026-03-31-uploaded-search-malformed-utf8-handoff.md`

## 사용 skill
- 없음

## 변경 이유
- latest `/work`인 `work/3/31/2026-03-31-uploaded-search-failure-docs-sync.md`와 latest `/verify`인 `verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md` 기준으로 uploaded-search partial-failure surface와 docs sync 라인은 current MVP 범위 안에서 닫혔습니다.
- 다음 단일 slice를 다시 operator가 지정해야 하는 상태였고, 현재 document workflow 안에서 가장 작은 current-risk reduction 후보를 정확히 좁혀 Claude handoff를 다시 `STATUS: implement`로 고정할 필요가 있었습니다.

## 핵심 변경
- `.pipeline/codex_feedback.md`를 `STATUS: needs_operator`에서 `STATUS: implement`로 갱신했습니다.
- 이번 라운드 단일 슬라이스를 `uploaded search malformed UTF-8 request handling only`로 고정했습니다.
- 실제 current-risk 위치가 `core/agent_loop.py` uploaded partial-failure surface가 아니라 `app/web.py`의 JSON request-body decode 경로라는 점을 반영해, handoff의 수정 범위를 `app/web.py` 중심으로 다시 좁혔습니다.
- 이번 handoff에서는 다음 사항을 명시했습니다:
  - malformed UTF-8 request body는 explicit `400` 계열 validation error로 정규화
  - partial-failure notice 성공 경로 유지
  - `content_base64` semantics, entity-card quality, summary/search quality, approval flow, reviewed-memory, broader web investigation UX 확장 금지

## 검증
- `sed -n '1,220p' .pipeline/codex_feedback.md`
- `sed -n '1,220p' work/3/31/2026-03-31-uploaded-search-failure-docs-sync.md`
- `sed -n '1,240p' verify/3/31/2026-03-31-uploaded-search-failure-docs-sync-verification.md`
- `sed -n '6648,6688p' app/web.py`
- `sed -n '1588,1610p' app/web.py`
- `rg -n "UnicodeDecodeError|malformed UTF-8|400|500|read_json_body|uploaded folder|search_uploaded_folder|uploaded file" app tests core`
- `git diff --check`

## 남은 리스크
- `malformed UTF-8` current-risk는 uploaded search path에 직접 체감되는 validation hardening 후보로 좁혔지만, 실제 구현 시 handler-level wording을 과하게 넓히지 않도록 주의가 필요합니다.
- dirty worktree가 여전히 넓어 다음 Claude 라운드도 unrelated 변경을 건드리지 않는 좁은 범위 통제가 필요합니다.
