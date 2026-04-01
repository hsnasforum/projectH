## 변경 파일
- `verify/4/1/2026-04-01-news-subdomain-false-positive-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-news-subdomain-false-positive-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-news-substring-false-positive-fix-verification.md`를 기준으로, 이번 라운드가 주장한 `news.` subdomain false-positive fix가 실제 코드/테스트와 맞는지 좁게 재검증할 필요가 있었습니다.

## 핵심 변경
- Claude `/work` 주장대로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`의 4개 파일에 same-family source-classification 변경이 집중돼 있음을 확인했습니다.
- `classify_source_type`와 `_classify_web_source_kind`에서 `hostname.startswith("news.")` catch-all이 실제로 제거돼 있음을 확인했습니다.
- `tests/test_source_policy.py`에는 `news.example.com -> general`, `news.sbs.co.kr -> news`, `news.kbs.co.kr -> news` assertion이 실제로 존재했습니다.
- `tests/test_web_app.py`에는 `test_handle_chat_latest_update_news_subdomain_not_promoted_to_article_role`가 실제로 존재했고, `news.example.com`이 latest_update에서 `기사 교차 확인`으로 승격되지 않음을 잠그고 있었습니다.
- `tests/test_web_app.py`의 기존 mixed-source fixture 3곳은 현재 `www.yna.co.kr`를 사용하고 있어, closeout의 `news.example.com` 교체 주장과 현재 파일 상태가 일치했습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 계열에는 이번 라운드용 추가 변경이 없었고, round-local 문서 무변경 주장도 맞았습니다.
- 이번 변경 범위는 secondary web investigation의 `latest_update` source-classification same-family false-positive current-risk reduction 1건에 머물러 현재 document-first MVP 방향을 벗어나지 않았습니다.
- 새 검수 결과를 기준으로 `.pipeline/codex_feedback.md`는 `news.naver.com` community misclassification을 줄이는 exact next slice로 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - `Ran 174 tests in 3.033s`
  - `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- 수동 spot-check
  - `classify_source_type("https://news.example.com/article/1") == "general"`
  - `classify_source_type("https://news.naver.com/main/read.naver?oid=001&aid=0000001") == "community"`
  - `classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N1001") == "news"`
  - `classify_source_type("https://news.kbs.co.kr/news/pc/view/view.do?ncd=8000001") == "news"`
  - `classify_source_type("https://www.unknownlocalnews.kr/article/1") == "general"`
- 문서/비범위 파일 spot-check
  - `rg -n "news-subdomain-false-positive-fix|news\\.example\\.com|news\\.naver\\.com" README.md docs tests/test_smoke.py`
  - `README.md`, `docs/`, `tests/test_smoke.py`에는 이번 라운드용 추가 변경 없음
- 미실행 검증
  - 브라우저 계약 변경이 아니라서 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `news.example.com` false-positive는 닫혔지만, `news.naver.com`은 현재 `community`로 분류돼 common Korean news portal article가 noisy community처럼 과도하게 낮게 취급될 여지가 남아 있습니다.
- 따라서 다음 same-family current-risk reduction은 generic `news.` catch-all을 다시 여는 것이 아니라, `news.naver.com`을 좁게 다뤄 latest_update에서 기사형 source-role로 복구하는 한 칸이 맞습니다.
- 이번 note는 latest Claude round truth 검수와 다음 단일 슬라이스 지정까지만 다룹니다. whole-project audit이 필요한 징후는 확인되지 않아 `report/`는 만들지 않았습니다.
