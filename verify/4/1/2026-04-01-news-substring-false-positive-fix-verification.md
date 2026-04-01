## 변경 파일
- `verify/4/1/2026-04-01-news-substring-false-positive-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-news-substring-false-positive-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-broader-news-domain-sweep-verification.md`를 기준으로, 이번 라운드가 주장한 news-substring false-positive fix가 실제 코드/테스트와 맞는지 좁게 재검증할 필요가 있었습니다.

## 핵심 변경
- Claude `/work` 주장대로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`의 4개 파일에 same-family source-classification 변경이 집중돼 있음을 확인했습니다.
- `classify_source_type`와 `_classify_web_source_kind`에서 bare `"news"` 힌트는 제거되고, 대신 `hostname.startswith("news.")` 분기로 `news.` 서브도메인만 `news`로 처리하도록 바뀌어 있음을 확인했습니다.
- `tests/test_source_policy.py`에는 `unknownlocalnews.kr -> general`, `news.sbs.co.kr -> news`, `newsis.com -> news`, `news1.kr -> news`를 포함한 관련 assertion이 실제로 존재함을 확인했습니다.
- `tests/test_web_app.py`에는 `test_handle_chat_latest_update_unknown_news_host_not_promoted_to_article_role`가 실제로 존재했고, `unknownlocalnews.kr`이 latest_update에서 `기사 교차 확인`으로 승격되지 않음을 잠그고 있었습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 계열에는 이번 라운드용 추가 변경이 없었고, round-local 문서 무변경 주장도 맞았습니다.
- 이번 변경 범위는 secondary web investigation의 `latest_update` source-classification same-family false-positive current-risk reduction 1건에 머물러 현재 document-first MVP 방향을 벗어나지 않았습니다.
- 새 검수 결과를 기준으로 `.pipeline/codex_feedback.md`는 generic `news.` 서브도메인 false-positive를 한 칸 더 줄이는 exact next slice로 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - `Ran 173 tests in 2.955s`
  - `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- 수동 spot-check
  - `classify_source_type("https://www.unknownlocalnews.kr/article/1") == "general"`
  - `classify_source_type("https://news.example.com/article") == "news"`
  - `classify_source_type("https://news.naver.com/main/read.naver?oid=001&aid=0000001") == "news"`
  - `classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N1001") == "news"`
  - `classify_source_type("https://www.newsis.com/view/NISX20260401_0001") == "news"`
- 문서/비범위 파일 spot-check
  - `rg -n "unknownlocalnews|news-substring-false-positive-fix|unknownlocal\\.kr" README.md docs tests/test_smoke.py work/4/1/2026-04-01-news-substring-false-positive-fix.md tests/test_source_policy.py tests/test_web_app.py`
  - `README.md`, `docs/`, `tests/test_smoke.py`에는 이번 라운드용 추가 변경 없음
- 미실행 검증
  - 브라우저 계약 변경이 아니라서 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `unknownlocalnews.kr` false-positive는 닫혔지만, generic `hostname.startswith("news.")` catch-all 때문에 `news.example.com`과 `news.naver.com`은 여전히 `news`로 분류됩니다.
- 이는 same-family current-risk reduction이 한 칸 더 남아 있다는 뜻이며, 다음 라운드는 arbitrary `news.` 서브도메인을 기사로 승격하지 않도록 줄이되 explicit domain coverage(`news.sbs.co.kr`, `newsis.com`, `news1.kr`, `etnews.com`, `bloter.net`)는 유지하는 쪽이 맞습니다.
- 이번 note는 latest Claude round truth 검수와 다음 단일 슬라이스 지정까지만 다룹니다. whole-project audit이 필요한 징후는 확인되지 않아 `report/`는 만들지 않았습니다.
