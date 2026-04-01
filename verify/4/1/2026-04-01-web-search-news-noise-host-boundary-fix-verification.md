## 변경 파일
- `verify/4/1/2026-04-01-web-search-news-noise-host-boundary-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-web-search-news-noise-host-boundary-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-fragment-news-hint-boundary-fix-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 이번 라운드는 `tools/web_search.py`의 news boilerplate/noise 필터가 exact-or-subdomain boundary로 실제 좁혀졌는지, 그리고 범위가 current `projectH`의 secondary web investigation hardening을 벗어나지 않았는지 확인하는 것이 핵심이었습니다.

## 핵심 변경
- Claude 주장대로 이번 라운드 구현 변경은 `tools/web_search.py`와 `tests/test_web_search_tool.py` 2개 파일에 집중되어 있었습니다.
- `tools/web_search.py`의 `_looks_like_domain_specific_noise`에서는 bare `"news"` token이 제거되었고, 기존 substring 기반 `hint in hostname`이 explicit domain host에 대한 exact-or-subdomain boundary 매칭으로 바뀌어 있었습니다.
- `tests/test_web_search_tool.py`에는 `test_fetch_page_news_noise_filter_exact_boundary`가 실제로 추가되어, positive 3건(`www.chosun.com`, `www.yna.co.kr`, `www.mk.co.kr`)과 negative 4건(`mychosun.com`, `foo-yna.co.kr`, `notmk.co.kr`, `news.google.com`)을 함께 잠그고 있었습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽에는 이번 slug나 관련 host를 직접 언급하는 round-local 추가 변경이 보이지 않았습니다.
- 현재 dirty worktree에 `README.md`, `docs/*`, `tests/test_smoke.py` 변경이 남아 있기는 하지만, 파일 mtime이 모두 `2026-03-31`로 이번 `/work` 시각(`2026-04-01 01:54`)보다 이전이어서 이번 round-local 변경으로 보이지는 않았습니다.
- 범위는 여전히 secondary web investigation의 page-text refinement same-family current-risk reduction 1건으로 유지되어 현재 `projectH` 방향을 벗어나지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`
  - `Ran 9 tests in 0.010s`
  - `OK`
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`
  - 통과
- `rg -n "web search news noise host boundary fix|mychosun\\.com|foo-yna\\.co\\.kr|notmk\\.co\\.kr|news\\.google\\.com" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/TASK_BACKLOG.md tests/test_smoke.py`
  - 결과 없음
- 수동 spot-check: `_looks_like_domain_specific_noise(hostname=..., line="입력 2026.04.01 09:00 김철수 기자 무단전재 및 재배포 금지")`
  - `www.chosun.com -> True`
  - `mychosun.com -> False`
  - `www.yna.co.kr -> True`
  - `foo-yna.co.kr -> False`
  - `www.mk.co.kr -> True`
  - `notmk.co.kr -> False`
  - `news.google.com -> False`
- residual-risk 확인
  - `news.naver.com -> False`
  - `news.daum.net -> False`
  - `v.daum.net -> False`
  - `news.nate.com -> False`
  - `news.zum.com -> False`
  - `m.news.nate.com -> False`
  - `m.news.zum.com -> False`
- source-classification 대비 확인
  - `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`에는 `news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`이 이미 news host/current contract로 남아 있음을 확인했습니다.
- browser-visible contract 변경은 아니라 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `tools/web_search.py`의 news boilerplate/noise 필터는 explicit domain boundary 보정은 닫혔지만, current source-classification contract에 이미 포함된 portal news host(`news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`)는 아직 뉴스 boilerplate 제거 대상으로 복구되지 않았습니다.
- 다음 단일 슬라이스는 `tools/web_search.py`와 `tests/test_web_search_tool.py` 안에서 위 explicit portal news host를 same-family exact-or-subdomain boundary 규칙으로 추가하고, `news.google.com`, `blog.naver.com`, `cafe.daum.net` 같은 generic/community host는 계속 제외하는 1건이 가장 작은 current-risk reduction입니다.
- 이번 검수는 latest Claude round truth 확인과 다음 same-family slice 선정에 한정했습니다. whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
