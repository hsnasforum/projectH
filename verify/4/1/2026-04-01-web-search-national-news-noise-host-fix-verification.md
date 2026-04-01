## 변경 파일
- `verify/4/1/2026-04-01-web-search-national-news-noise-host-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-web-search-national-news-noise-host-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-web-search-portal-news-noise-host-fix-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 이번 라운드는 `tools/web_search.py`의 news boilerplate/noise 필터가 national-news host 11건까지 실제로 복구되었는지, 그리고 범위가 current `projectH`의 secondary web investigation hardening을 벗어나지 않았는지 확인하는 것이 핵심이었습니다.

## 핵심 변경
- Claude 주장대로 이번 라운드 구현 변경은 `tools/web_search.py`와 `tests/test_web_search_tool.py` 2개 파일에 집중되어 있었습니다.
- `tools/web_search.py`의 `_looks_like_domain_specific_noise` `news_hosts`에는 `hankyung.com`, `edaily.co.kr`, `etoday.co.kr`, `heraldcorp.com`, `zdnet.co.kr`, `dt.co.kr`, `seoul.co.kr`, `newdaily.co.kr`, `moneytoday.co.kr`, `segye.com`, `newsis.com`이 실제로 추가되어 있었습니다.
- `tests/test_web_search_tool.py`에는 `test_fetch_page_national_news_host_boilerplate_boundary`가 실제로 추가되어, positive 11건과 negative 3건(`news.google.com`, `blog.naver.com`, `cafe.daum.net`)을 함께 잠그고 있었습니다.
- `README.md`, `docs/*`, `tests/test_smoke.py`에는 이번 slug나 관련 host를 직접 언급하는 round-local 추가 변경이 보이지 않았습니다.
- 범위는 secondary web investigation의 page-text refinement same-family current-risk reduction 1건으로 유지되어 현재 `projectH` 방향을 벗어나지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`
  - `Ran 11 tests in 0.024s`
  - `OK`
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`
  - 통과
- `rg -n "web search national news noise host fix|hankyung\\.com|edaily\\.co\\.kr|etoday\\.co\\.kr|heraldcorp\\.com|zdnet\\.co\\.kr|dt\\.co\\.kr|seoul\\.co\\.kr|newdaily\\.co\\.kr|moneytoday\\.co\\.kr|segye\\.com|newsis\\.com|news\\.google\\.com|blog\\.naver\\.com|cafe\\.daum\\.net" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/TASK_BACKLOG.md tests/test_smoke.py`
  - 결과 없음
- 수동 spot-check: `_looks_like_domain_specific_noise(hostname=..., line="입력 2026.04.01 09:00 김철수 기자 무단전재 및 재배포 금지")`
  - `hankyung.com -> True`
  - `edaily.co.kr -> True`
  - `etoday.co.kr -> True`
  - `heraldcorp.com -> True`
  - `zdnet.co.kr -> True`
  - `dt.co.kr -> True`
  - `seoul.co.kr -> True`
  - `newdaily.co.kr -> True`
  - `moneytoday.co.kr -> True`
  - `segye.com -> True`
  - `newsis.com -> True`
  - `news.google.com -> False`
  - `blog.naver.com -> False`
  - `cafe.daum.net -> False`
- residual-risk 확인
  - `mbn.co.kr -> False`
  - `sbs.co.kr -> False`
  - `kbs.co.kr -> False`
  - `ytn.co.kr -> False`
  - `jtbc.co.kr -> False`
  - `ichannela.com -> False`
  - `tvchosun.com -> False`
- source-classification contract 확인
  - `core/source_policy.py`와 `tests/test_source_policy.py`에는 `mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`이 이미 news host/current contract로 남아 있음을 확인했습니다.
- browser-visible contract 변경은 아니라 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `tools/web_search.py`의 news boilerplate/noise 필터는 portal+national host mismatch는 닫혔지만, current source-classification contract에 이미 포함된 broadcast/newsroom host 7건(`mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`)은 아직 boilerplate 제거 대상으로 복구되지 않았습니다.
- 위 7건은 `core/source_policy.py`와 `tests/test_source_policy.py`에서 이미 news contract로 검증되고 있지만, `_looks_like_domain_specific_noise`에서는 현재 모두 `False`입니다.
- 다음 단일 슬라이스는 `tools/web_search.py`와 `tests/test_web_search_tool.py` 안에서 위 7건만 exact-or-subdomain boundary로 추가하고, `news.google.com`, `blog.naver.com`, `cafe.daum.net` 같은 non-news/community host는 계속 제외하는 1건이 가장 작은 same-family current-risk reduction입니다.
- 이번 검수는 latest Claude round truth 확인과 다음 same-family slice 선정에 한정했습니다. whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
