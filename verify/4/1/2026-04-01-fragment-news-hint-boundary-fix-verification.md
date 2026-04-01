## 변경 파일
- `verify/4/1/2026-04-01-fragment-news-hint-boundary-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-fragment-news-hint-boundary-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-dotted-news-host-boundary-fix-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- fragment-style news hint 3건(`chosun`, `joongang`, `donga`)의 substring 오인이 실제로 닫혔는지와, 이번 변경이 현재 `projectH`의 document-first MVP 범위를 벗어나지 않았는지 확인할 필요가 있었습니다.

## 핵심 변경
- Claude 주장대로 이번 라운드 구현 변경은 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py` 4개 파일로 좁혀져 있었습니다.
- `core/source_policy.py`와 `core/agent_loop.py`에서는 fragment-style hint가 제거되고 `chosun.com`, `joongang.co.kr`, `donga.com`이 explicit domain host boundary로 처리되고 있었습니다.
- `tests/test_source_policy.py`에는 `www.chosun.com`, `www.joongang.co.kr`, `www.donga.com` positive 회귀와 `mychosun.com`, `fakejoongang.example`, `notdonga.example` false-positive 차단 회귀가 실제로 존재했습니다.
- `tests/test_web_app.py`에는 `mychosun.com`이 `latest_update` 기사 role로 승격되지 않는 focused regression이 실제로 존재했습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽 이번 라운드 추가 변경은 확인되지 않았습니다.
- 범위는 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건으로 유지되어 현재 `projectH` 방향을 벗어나지 않았습니다.
- 다만 same-family current-risk는 `tools/web_search.py`의 `_looks_like_domain_specific_noise` 쪽에 별도로 남아 있습니다. 현재 이 필터는 `news_hosts` substring 매칭을 계속 사용해 `mychosun.com`, `foo-yna.co.kr`, `notmk.co.kr`, `news.example.com`, `news.google.com`에서도 기사 boilerplate를 뉴스 전용 잡음으로 처리합니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - `Ran 182 tests in 3.061s`
  - `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- `rg -n "fragment-news-hint-boundary-fix|mychosun\\.com|fakejoongang\\.example|notdonga\\.example|chosun\\.com|joongang\\.co\\.kr|donga\\.com" README.md docs tests/test_smoke.py`
  - 결과 없음
- 수동 spot-check
  - `https://www.chosun.com/politics/2026/04/01/ABC123/ -> news`
  - `https://mychosun.com/story/1 -> general`
  - `https://www.joongang.co.kr/article/12345678 -> news`
  - `https://fakejoongang.example/article/1 -> general`
  - `https://www.donga.com/news/article/all/20260401/123456789/1 -> news`
  - `https://notdonga.example/article/1 -> general`
  - `https://sportschosun.com/entertainment/2026/04/01/XYZ123/ -> news`
  - `https://news.tvchosun.com/site/data/html_dir/2026/04/01/2026040199999.html -> news`
  - `https://news.google.com/home?hl=ko&gl=KR&ceid=KR:ko -> general`
  - `https://blog.naver.com/example/123 -> community`
- `tools/web_search.py` residual-risk 확인
  - `mychosun.com -> True`
  - `www.chosun.com -> True`
  - `fakejoongang.example -> False`
  - `www.joongang.co.kr -> True`
  - `notdonga.example -> False`
  - `www.donga.com -> True`
  - `foo-yna.co.kr -> True`
  - `www.yna.co.kr -> True`
  - `notmk.co.kr -> True`
  - `www.mk.co.kr -> True`
  - `news.example.com -> True`
  - `news.google.com -> True`
- browser-visible contract 변경은 아니라 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `tools/web_search.py`의 뉴스 boilerplate/noise 필터는 아직 explicit news host를 substring으로 잡고 있어, source classification과 page-text refinement 사이의 host-boundary 정책이 어긋나 있습니다.
- 다음 단일 슬라이스는 `tools/web_search.py`의 `news_hosts`를 exact-or-subdomain boundary 규칙으로 좁히고, bare `news` token을 더 좁은 규칙으로 바꾸는 1건이 가장 작은 same-family current-risk reduction입니다.
- 이번 검수는 latest Claude round truth 확인과 다음 same-family slice 선정에 한정했습니다. whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
