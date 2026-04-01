# 2026-04-01 dotted news host boundary fix verification

## 변경 파일
- `verify/4/1/2026-04-01-dotted-news-host-boundary-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-dotted-news-host-boundary-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-explicit-portal-news-host-boundary-fix-verification.md`를 기준으로 이번 라운드 truth만 다시 확인할 필요가 있었습니다.
- 직전 handoff는 dotted exact-domain `news_host_hints`의 substring false-positive를 exact-or-subdomain boundary로 좁히도록 지시했고, 이번 검수에서는 그 주장이 실제 코드/테스트와 맞는지와 same-family residual이 무엇인지까지만 좁게 확인했습니다.

## 핵심 변경
- Claude가 주장한 이번 라운드 코드 변경은 실제로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py` 4개 파일에만 존재했습니다.
- `core/source_policy.py`와 `core/agent_loop.py`에서 기존 news hint가 `news_fragment_hints`와 `news_domain_hosts`로 분리되어, dotted domain들은 `hostname == host or hostname.endswith(f".{host}")` 경계로 처리되고 있습니다.
- 그 결과 `www.yna.co.kr`, `m.yna.co.kr`, `www.mk.co.kr`, `m.mk.co.kr`, `news.sbs.co.kr`, `sportschosun.com` 같은 실제 dotted news host는 계속 `news`로 유지되고, `foo-yna.co.kr`, `notmk.co.kr`는 `general`로 내려갑니다.
- `tests/test_source_policy.py`에는 위 positive/negative 회귀가 실제로 추가돼 있었고, `tests/test_web_app.py`에는 `foo-yna.co.kr` fake dotted news host가 latest_update 기사 role로 승격되지 않는 focused regression이 들어가 있었습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽 이번 라운드 추가 변경은 확인되지 않았고, 범위도 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건에 머물러 현재 `projectH` 방향을 벗어나지 않았습니다.
- 다만 fragment-style hint인 `chosun`, `joongang`, `donga`는 여전히 substring 기반이라 `mychosun.com`, `fakejoongang.example`, `notdonga.example` 같은 fake host가 `news`로 오인되는 current-risk는 남아 있습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: `Ran 181 tests in 3.020s`, `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- `rg -n "dotted-news-host-boundary-fix|foo-yna\\.co\\.kr|notmk\\.co\\.kr|m\\.yna\\.co\\.kr|m\\.mk\\.co\\.kr|news\\.sbs\\.co\\.kr|sportschosun\\.com" README.md docs tests/test_smoke.py`: 추가 hit 없음
- 수동 spot-check:
- `https://www.yna.co.kr/view/AKR20260401 -> news`
- `https://m.yna.co.kr/view/AKR20260401 -> news`
- `https://foo-yna.co.kr/article/1 -> general`
- `https://www.mk.co.kr/economy/2025 -> news`
- `https://m.mk.co.kr/economy/2025 -> news`
- `https://notmk.co.kr/article/1 -> general`
- `https://news.sbs.co.kr/news/endPage.do?news_id=N1001 -> news`
- `https://sportschosun.com/sports/2026/04/01/202604010100001230000001.htm -> news`
- residual fragment-hint spot-check:
- `https://www.chosun.com/politics/2026/04/01/ABC123/ -> news`
- `https://mychosun.com/story/1 -> news`
- `https://www.joongang.co.kr/article/12345678 -> news`
- `https://fakejoongang.example/article/1 -> news`
- `https://www.donga.com/news/article/all/20260401/123456789/1 -> news`
- `https://notdonga.example/article/1 -> news`
- 브라우저 계약 변경은 아니라 `make e2e-test`는 이번 라운드에 재실행하지 않았습니다.

## 남은 리스크
- dotted exact-domain hint 경계 보정은 닫혔지만, fragment-style hint(`chosun`, `joongang`, `donga`)의 substring false-positive current-risk가 남아 있습니다.
- 다음 smallest same-family slice는 이 3개 fragment hint만 explicit domain boundary로 바꾸고, 이미 explicit domain으로 남아 있는 `sportschosun.com`, `tvchosun.com` 같은 positive는 유지하는 것입니다.
- `tools/web_search.py`의 현재 `news_hosts`에도 `chosun.com`, `joongang.co.kr`, `donga.com`가 explicit host로 적혀 있어, 다음 slice의 intended domain 근거는 local repo 안에 있습니다.
- broader classifier rewrite나 docs 변경으로 넓히면 범위가 다시 커지므로 이번 handoff에서는 제외했습니다.
- dirty worktree가 여전히 넓고, whole-project audit 신호는 없어 `report/`는 만들지 않았습니다.
