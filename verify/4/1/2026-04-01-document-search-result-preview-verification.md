## 변경 파일
- `verify/4/1/2026-04-01-document-search-result-preview-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-document-search-result-preview.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-entity-card-weak-vs-missing-clarity-verification.md`를 기준으로, 이번 라운드 주장만 좁게 검수해야 했습니다.
- 이번 라운드는 secondary web investigation이 아니라 document-first MVP core loop 쪽으로 돌아와, 문서 검색 결과 응답에 사용자 체감용 미리보기 카드를 추가하는 user-visible quality slice 1건이었습니다.

## 핵심 변경
- Claude `/work`가 주장한 핵심 코드 변경은 현재 파일 상태에서 실제로 확인됐습니다.
- `core/agent_loop.py`
  - `AgentResponse`에 `search_results` 필드가 실제로 추가돼 있습니다.
  - `search_results=[...]`를 넣는 응답 경로도 `/work` 주장대로 4곳입니다.
    - search-only
    - 검색+승인요청
    - 검색+저장완료
    - 검색+요약 응답
- `app/web.py`
  - `_serialize_response`가 `response.search_results`를 `path`, `matched_on`, `snippet` 형태로 실제 직렬화합니다.
- `app/templates/index.html`
  - `message.search_results`가 있을 때 `.search-preview-panel` 아래에 카드형 미리보기 UI를 실제로 렌더링합니다.
  - 카드에는 파일명, `파일명 일치`/`내용 일치` 배지, snippet이 들어갑니다.
- `tests/test_web_app.py`
  - `/work`가 말한 기존 검색 테스트 2건이 실제로 `search_results` 구조를 검증하도록 보강돼 있습니다.
- 범위는 document search UX 개선 1건에 머물러 있고, ranking·search policy·web investigation로 다시 넓어지지 않아 현재 `projectH` 방향을 벗어나지 않았습니다.
- 다만 `/work` 주장이 완전히 truthful하진 않았습니다.
  - UI 동작이 실제로 바뀌었는데 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에는 새 검색 결과 미리보기 패널이 아직 반영돼 있지 않습니다.
  - `AGENTS.md`의 UI 동작 변경 시 doc sync 규칙과 충돌하므로, 이번 라운드 closeout은 docs 측면에서 불완전합니다.
  - `/work`의 `browser smoke는 이번 변경이 브라우저 계약을 바꾸지 않으므로 생략` 서술도 현재 기준으로는 맞지 않습니다. `index.html` 렌더링 계약이 직접 바뀌었기 때문입니다.

## 검증
- `python3 -m py_compile core/agent_loop.py app/web.py`
  - 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_search_uploaded_folder_returns_search_results tests.test_web_app.WebAppServiceTest.test_handle_chat_search_uploaded_folder_can_summarize_results`
  - `Ran 2 tests in 0.015s`
  - `OK`
- `git diff --check -- core/agent_loop.py app/web.py app/templates/index.html tests/test_web_app.py`
  - 통과
- `make e2e-test`
  - `16 passed (3.8m)`
- 코드/문서 truth 대조
  - `rg`로 `search_results` 4개 응답 경로 확인
  - `sed`로 `core/agent_loop.py`, `app/web.py`, `app/templates/index.html`, `tests/test_web_app.py`의 claimed 변경 본문 확인
  - `rg`로 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에 새 미리보기 패널 설명이 아직 없음을 확인

## 남은 리스크
- 코드 자체는 현재 상태에서 정상 동작하고, focused Python 검증과 browser smoke 모두 통과했습니다.
- 이번 family의 남은 가장 작은 current-risk reduction은 docs truth sync입니다.
  - 새 검색 결과 미리보기 패널이 현재 shipped UI에 존재하지만 root docs에는 아직 없습니다.
- browser smoke 자체는 통과했으므로, 다음 기본 슬라이스를 verification-only gap으로 넓히는 것보다 same-family docs sync를 먼저 닫는 편이 더 맞습니다.
- whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
