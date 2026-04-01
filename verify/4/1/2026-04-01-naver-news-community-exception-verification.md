## 변경 파일
- `verify/4/1/2026-04-01-naver-news-community-exception-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-naver-news-community-exception.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-news-subdomain-false-positive-fix-verification.md`를 기준으로, 이번 라운드가 주장한 `news.naver.com` community 예외 보정이 실제 코드/테스트와 맞는지 좁게 재검증할 필요가 있었습니다.

## 핵심 변경
- Claude `/work` 주장대로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`의 4개 파일에만 same-family source-classification 변경이 집중돼 있음을 확인했습니다.
- `core/source_policy.py`와 `core/agent_loop.py`의 news host hint에 실제로 `news.naver.com`이 추가돼 있어, generic `naver.com` community 판정보다 먼저 `news`로 분류되도록 보정돼 있었습니다.
- `tests/test_source_policy.py`에는 `news.naver.com -> news`와 `blog.naver.com -> community` assertion이 실제로 존재해, 포털 뉴스 host만 좁게 복구하고 일반 Naver community 경로는 유지하는 회귀가 들어가 있었습니다.
- `tests/test_web_app.py`에는 `test_handle_chat_latest_update_naver_news_mk_noisy_community_badge_contract`가 실제로 존재했고, `news.naver.com + mk + noisy community` fixture에서 `verification_label = 기사 교차 확인`과 non-generic article-role 반영을 잠그고 있었습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 계열에는 이번 라운드용 추가 변경이 없었고, round-local 문서 무변경 주장도 맞았습니다.
- 이번 변경 범위는 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건에 머물러 현재 document-first MVP 방향을 벗어나지 않았습니다.
- manual spot-check에서는 `v.daum.net`와 `news.daum.net`가 여전히 `community`로 분류돼 다음 same-family current-risk가 남아 있음을 확인했고, 그중 더 작은 exact next slice로 `v.daum.net` 1건을 handoff에 고정했습니다.

## 검증
- `rg -n "news\\.naver\\.com|blog\\.naver\\.com|naver\\.com|news_subdomain|기사 교차 확인" core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - `news.naver.com` hint, `blog.naver.com` 유지 assertion, latest_update badge contract 위치 확인
- `rg -n "news\\.naver\\.com|blog\\.naver\\.com|naver news|community exception|naver-news-community-exception" README.md docs tests/test_smoke.py work/4/1/2026-04-01-naver-news-community-exception.md`
  - `README.md`, `docs/`, `tests/test_smoke.py`에는 이번 라운드용 추가 변경 없음
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - `Ran 175 tests in 3.155s`
  - `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- 수동 spot-check
  - `classify_source_type("https://news.naver.com/main/read.naver?oid=001&aid=0000001") == "news"`
  - `classify_source_type("https://blog.naver.com/example/1") == "community"`
  - `classify_source_type("https://news.example.com/article/1") == "general"`
  - `classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N1001") == "news"`
  - `classify_source_type("https://v.daum.net/v/20260401120000001") == "community"`
  - `classify_source_type("https://news.daum.net/v/20260401120000001") == "community"`
- 미실행 검증
  - 브라우저 계약 변경이 아니라서 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `news.naver.com` current-risk는 닫혔지만, common Daum portal article host인 `v.daum.net`는 아직 `daum.net` community 판정에 걸려 latest_update에서 기사형 source-role을 잃을 수 있습니다.
- `news.daum.net`도 현재 `community`로 보였지만, 이번 handoff는 smallest same-family slice 원칙에 따라 `v.daum.net` 1건만 고정합니다.
- 이번 note는 latest Claude round truth 검수와 다음 단일 슬라이스 지정까지만 다룹니다. whole-project audit이 필요한 징후는 확인되지 않아 `report/`는 만들지 않았습니다.
