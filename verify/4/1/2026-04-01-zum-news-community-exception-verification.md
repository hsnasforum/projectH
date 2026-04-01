# 2026-04-01 news.zum.com community exception verification

## 변경 파일
- `verify/4/1/2026-04-01-zum-news-community-exception-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-zum-news-community-exception.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-nate-news-community-exception-verification.md`를 기준으로 이번 라운드 truth만 다시 확인할 필요가 있었습니다.
- 직전 handoff는 `news.zum.com` 1건 구현을 지시했고, 이번 검수에서는 그 주장이 실제 코드/테스트와 맞는지와 same-family residual이 남는지까지만 좁게 확인했습니다.

## 핵심 변경
- Claude가 주장한 이번 라운드 코드 변경은 실제로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py` 4개 파일에만 존재했습니다.
- `core/source_policy.py`와 `core/agent_loop.py`의 news host 예외 목록에 `news.zum.com`이 추가돼 현재 `news.zum.com`은 `news`로 분류됩니다.
- `tests/test_source_policy.py`에는 `news.zum.com -> news` 회귀가, `tests/test_web_app.py`에는 `news.zum.com + mk + noisy community` latest_update badge contract 회귀가 실제로 존재했습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽 이번 라운드 추가 변경은 확인되지 않았고, 범위도 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건에 머물러 현재 `projectH` 방향을 벗어나지 않았습니다.
- 다만 이번 라운드로 주요 portal news host 복구는 닫혔어도, 현재 explicit portal/news host 판단이 여전히 substring 기반이라 `notnews.nate.com`, `notnews.zum.com`, `notnews.naver.com`, `notnews.daum.net` 같은 suffix-like 가짜 host가 `news`로 오인되는 current-risk는 남아 있습니다.
- 다음 Claude handoff는 이 broader classifier debt 전체가 아니라, 방금 닫은 same-family인 explicit portal news host 예외 5건만 exact-or-subdomain boundary로 좁히는 1개 slice로 고정했습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: `Ran 179 tests in 3.092s`, `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- `rg -n "news\\.zum\\.com|news\\.nate\\.com|v\\.daum\\.net|news\\.daum\\.net|news\\.naver\\.com" README.md docs tests/test_smoke.py`: 추가 hit 없음
- 수동 spot-check:
- `https://news.zum.com/articles/97600001 -> news`
- `https://news.nate.com/view/20260401n00123 -> news`
- `https://news.daum.net/v/20260401120000001 -> news`
- `https://v.daum.net/v/20260401120000001 -> news`
- `https://news.naver.com/main/read.naver?oid=001&aid=0000001 -> news`
- `https://cafe.daum.net/test/abc -> community`
- `https://blog.naver.com/test/123 -> community`
- `https://m.news.nate.com/view/20260401n00123 -> news`
- `https://m.news.zum.com/articles/97600001 -> news`
- `https://news.google.com/articles/CBMiYWh0dHBzOi8vZXhhbXBsZS5jb20vbmV3cy_SAQA -> general`
- residual false-positive spot-check:
- `https://notnews.nate.com/view/20260401n00123 -> news`
- `https://notnews.zum.com/articles/97600001 -> news`
- `https://notnews.naver.com/main/read.naver?oid=001&aid=0000001 -> news`
- `https://notnews.daum.net/v/20260401120000001 -> news`
- 브라우저 계약 변경은 아니라 `make e2e-test`는 이번 라운드에 재실행하지 않았습니다.

## 남은 리스크
- explicit portal news host 복구는 닫혔지만, 동일 family 안에서 host boundary false-positive current-risk가 남아 있습니다.
- 다음 smallest same-family slice는 `news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com` 5건만 substring이 아니라 exact-or-subdomain boundary로 판정하게 좁히는 것입니다.
- broader domain hint 전체(`yna`, `mk`, 기타 local news domain`)를 같은 라운드에 함께 정리하면 범위가 다시 넓어지므로 이번 handoff에서는 제외했습니다.
- whole-project audit 신호는 없어 `report/`는 만들지 않았습니다.
