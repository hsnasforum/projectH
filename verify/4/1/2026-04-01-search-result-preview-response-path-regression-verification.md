# 2026-04-01 search result preview response-path regression verification

## 변경 파일
- `verify/4/1/2026-04-01-search-result-preview-response-path-regression-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/1/2026-04-01-search-result-preview-response-path-regression.md`의 round-local 변경 주장이 실제 코드와 맞는지 확인했습니다.
- same-day latest `/verify`인 `verify/4/1/2026-04-01-document-search-result-preview-docs-sync-verification.md`가 제안한 same-family current-risk reduction이 truthfully 닫혔는지 확인했습니다.
- 이번 변경에 필요한 최소 검증만 재실행하고, 다음 Claude handoff 상태를 현재 사실에 맞게 갱신했습니다.

## 핵심 변경
- 이번 라운드의 실제 product-file 변경은 `tests/test_web_app.py`에 추가된 2개 focused regression test로 확인했습니다.
- 추가된 테스트는 `search+summary` 흐름의 `needs_approval` 응답과 `saved` 응답에서 `search_results`가 유지되고 `path`, `matched_on`, `snippet` 구조를 갖는지 직접 잠급니다.
- `core/agent_loop.py`와 `app/web.py`는 이번 라운드에서 수정되지 않았고, latest `/work`의 "코드 보정 없이 테스트만 추가" 주장은 현재 작업트리 기준으로 맞았습니다.
- 범위는 shipped `document search result preview` contract의 same-family regression coverage 보강에 한정되어 있으며, current document-first MVP 방향에서 벗어나지 않았습니다.
- code change, docs sync, 4개 응답 경로 regression coverage까지 확인되어 `document search result preview` family는 이번 pair 기준 truthfully 닫혔습니다.
- whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_search_summary_save_request_includes_search_results tests.test_web_app.WebAppServiceTest.test_handle_chat_search_summary_approved_save_includes_search_results`: 통과
- `python3 -m unittest -v tests.test_web_app`: `Ran 185 tests`, `OK`
- `git diff --check -- core/agent_loop.py app/web.py tests/test_web_app.py`: 통과
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`를 재확인했고, read-only 파일 시각 대조로 이번 라운드의 touched product file이 `tests/test_web_app.py`뿐인지 확인했습니다.

## 남은 리스크
- 이번 family 안에서 자동으로 이어갈 더 작은 same-family slice는 보이지 않아 다음 구현 축은 operator 결정이 필요합니다.
- dirty worktree가 넓어 이후 round도 touched 파일과 round-local 근거를 계속 좁게 기록하는 편이 안전합니다.
