# 2026-04-01 document search result preview

## 변경 파일
- `core/agent_loop.py`
- `app/web.py`
- `app/templates/index.html`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 web investigation family를 닫고 document-first MVP core loop 축으로 전환 지시.
- 검색 결과가 plain text `<pre>`로만 표시되어 사용자 체감 gap이 큰 상태.
- 가장 작은 user-visible quality improvement로 검색 결과 미리보기 카드 1건만 다룸 (관련성 랭킹은 이번 라운드에서 열지 않음).

## 핵심 변경
- `AgentResponse`에 `search_results: list[dict[str, str]]` 필드 추가 (structured search result 전달용)
- `agent_loop.py`: search_only 경로 + 검색+요약 경로 3곳(승인요청/저장완료/요약만) 총 4곳에서 `search_results`를 `[{"path", "matched_on", "snippet"}]` 형태로 response에 포함
- `web.py` `_serialize_response`: `search_results`를 JSON으로 직렬화하여 프런트엔드에 전달
- `index.html`:
  - `search_results` 배열이 있으면 `<pre>` body 아래에 미리보기 패널(`.search-preview-panel`) 렌더링
  - 각 결과를 카드 형태로: 파일명(+전체경로 tooltip), 일치 방식 배지(`파일명 일치`/`내용 일치`), snippet 발췌
  - CSS: `.search-preview-panel`, `.search-preview-item`, `.search-preview-name`, `.search-preview-match`, `.search-preview-snippet` 스타일 추가
- `tests/test_web_app.py`: 기존 검색 테스트 2건에 `search_results` 필드 존재/구조/값 assertion 추가

## 검증
- `python3 -m py_compile core/agent_loop.py app/web.py`: 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`: 277 tests, OK (4.096s)

## 남은 리스크
- 문구/UI 카드 추가이므로 기능적 리스크 낮음
- 기존 `<pre>` text body와 미리보기 카드가 동시에 표시됨 (정보 중복). 추후 search_only일 때 `<pre>` 대신 카드만 표시하는 UX 개선 가능
- 검색 관련성 랭킹은 이번 라운드 범위 밖
- browser smoke는 이번 변경이 브라우저 계약을 바꾸지 않으므로 생략
