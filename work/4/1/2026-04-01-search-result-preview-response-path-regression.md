# 2026-04-01 search result preview response-path regression coverage

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `verify/4/1/2026-04-01-document-search-result-preview-docs-sync-verification.md` 기준으로, `search_results`가 실리는 4개 응답 경로 중 search-only와 search+summary 2경로만 기존 regression이 있고, approval-request(needs_approval)와 approved-save(saved) 2경로는 아직 직접 잠기지 않았음.
- 이번 라운드는 같은 family 안의 가장 작은 current-risk reduction으로 해당 2경로 regression 테스트만 추가.

## 핵심 변경
- `test_handle_chat_search_summary_save_request_includes_search_results`: search+요약+저장승인요청(needs_approval) 응답에서 `search_results`가 존재하고 올바른 구조(`path`, `matched_on`, `snippet`)를 갖는지 확인
- `test_handle_chat_search_summary_approved_save_includes_search_results`: search+요약+승인저장(saved) 응답에서 `search_results`가 존재하고 올바른 구조를 갖는지 확인
- 코드 보정 없이 기존 구현이 이미 올바르게 동작하여 테스트만 추가

## 검증
- `python3 -m unittest -v tests.test_web_app`: 185 tests, OK (3.092s)
- `git diff --check -- core/agent_loop.py app/web.py tests/test_web_app.py`: 통과
- `core/agent_loop.py`, `app/web.py`는 이번 라운드에서 수정하지 않음
- browser smoke는 이번 변경이 브라우저 계약을 바꾸지 않으므로 실행하지 않음

## 남은 리스크
- 테스트 추가만이므로 기능적 리스크 없음
- dirty worktree가 여전히 넓음
- `document search result preview` family는 코드 구현 + docs sync + 4경로 regression coverage까지 truthfully 닫힘
