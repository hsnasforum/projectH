# 2026-04-01 explicit portal news host boundary fix verification

## 변경 파일
- `verify/4/1/2026-04-01-explicit-portal-news-host-boundary-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-explicit-portal-news-host-boundary-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-zum-news-community-exception-verification.md`를 기준으로 이번 라운드 truth만 다시 확인할 필요가 있었습니다.
- 직전 handoff는 explicit portal news host 5건의 substring false-positive를 exact-or-subdomain boundary로 좁히도록 지시했고, 이번 검수에서는 그 주장이 실제 코드/테스트와 맞는지와 same-family residual이 무엇인지까지만 좁게 확인했습니다.

## 핵심 변경
- Claude가 주장한 이번 라운드 코드 변경은 실제로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py` 4개 파일에만 존재했습니다.
- `core/source_policy.py`와 `core/agent_loop.py`에서 `news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`은 `news_host_hints` substring 목록에서 분리되어 `portal_news_hosts` exact-or-subdomain 경계로 처리됩니다.
- 그 결과 실제 host와 실제 하위 서브도메인인 `m.news.nate.com`, `m.news.zum.com`은 계속 `news`로 유지되고, `notnews.nate.com`, `notnews.zum.com`은 `general`로 내려갑니다.
- `tests/test_source_policy.py`에는 위 positive/negative 회귀가 실제로 추가돼 있었고, `tests/test_web_app.py`에는 `notnews.nate.com` fake portal-news host가 latest_update 기사 role로 승격되지 않는 focused regression이 들어가 있었습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽 이번 라운드 추가 변경은 확인되지 않았고, 범위도 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건에 머물러 현재 `projectH` 방향을 벗어나지 않았습니다.
- 다만 broader `news_host_hints`는 여전히 substring 기반이라 `foo-yna.co.kr`, `notmk.co.kr` 같은 dotted fake host가 `news`로 오인되는 current-risk는 남아 있습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: `Ran 180 tests in 3.397s`, `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- `rg -n "explicit-portal-news-host-boundary-fix|news\\.naver\\.com|v\\.daum\\.net|news\\.daum\\.net|news\\.nate\\.com|news\\.zum\\.com|notnews\\.nate\\.com|notnews\\.zum\\.com|m\\.news\\.nate\\.com|m\\.news\\.zum\\.com" README.md docs tests/test_smoke.py`: 추가 hit 없음
- 수동 spot-check:
- `https://news.naver.com/main/read.naver?oid=001&aid=0000001 -> news`
- `https://v.daum.net/v/20260401120000001 -> news`
- `https://news.daum.net/v/20260401120000001 -> news`
- `https://news.nate.com/view/20260401n00123 -> news`
- `https://news.zum.com/articles/97600001 -> news`
- `https://m.news.nate.com/view/20260401n00123 -> news`
- `https://m.news.zum.com/articles/97600001 -> news`
- `https://notnews.nate.com/view/1 -> general`
- `https://notnews.zum.com/articles/1 -> general`
- residual false-positive spot-check:
- `https://foo-yna.co.kr/article/20260401n00123 -> news`
- `https://notmk.co.kr/news/20260401n00123 -> news`
- `https://news.google.com/articles/CBMiYWh0dHBzOi8vZXhhbXBsZS5jb20vbmV3cy_SAQA -> general`
- 브라우저 계약 변경은 아니라 `make e2e-test`는 이번 라운드에 재실행하지 않았습니다.

## 남은 리스크
- explicit portal news host 경계 보정은 닫혔지만, dotted exact-domain `news_host_hints`의 substring false-positive current-risk가 남아 있습니다.
- 다음 smallest same-family slice는 dotted exact-domain hint만 exact-or-subdomain boundary로 좁히고, fragment-style hint(`chosun`, `joongang`, `donga`)는 그대로 두는 것입니다.
- broader classifier rewrite나 docs 변경으로 넓히면 범위가 다시 커지므로 이번 handoff에서는 제외했습니다.
- dirty worktree가 여전히 넓고, whole-project audit 신호는 없어 `report/`는 만들지 않았습니다.
