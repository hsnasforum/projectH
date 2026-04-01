## 변경 파일
- `verify/4/1/2026-04-01-web-search-broadcast-news-noise-host-fix-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-web-search-broadcast-news-noise-host-fix.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-web-search-national-news-noise-host-fix-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 이번 라운드는 `tools/web_search.py`의 news boilerplate/noise 필터에 broadcast/newsroom host 7건이 실제로 복구되었는지, 그리고 범위가 current `projectH`의 secondary web investigation page-text refinement를 벗어나지 않았는지 확인하는 것이 핵심이었습니다.

## 핵심 변경
- Claude 주장대로 이번 라운드 구현 변경은 `tools/web_search.py`와 `tests/test_web_search_tool.py` 2개 파일에 집중되어 있었습니다.
- `tools/web_search.py`의 `_looks_like_domain_specific_noise` `news_hosts`에는 `mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`이 실제로 추가되어 있었고, 기존 exact-or-subdomain boundary 매칭도 유지되어 있었습니다.
- `tests/test_web_search_tool.py`에는 `test_fetch_page_broadcast_news_host_boilerplate_boundary`가 실제로 추가되어, positive 7건과 negative 3건(`news.google.com`, `blog.naver.com`, `cafe.daum.net`)을 함께 잠그고 있었습니다.
- `README.md`, `docs/*`, `tests/test_smoke.py`에는 이번 slug나 관련 host를 직접 언급하는 round-local 추가 변경이 보이지 않았습니다.
- 범위는 secondary web investigation의 page-text refinement same-family current-risk reduction 1건으로 유지되어 현재 `projectH` 방향을 벗어나지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`
  - `Ran 12 tests in 0.021s`
  - `OK`
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`
  - 통과
- `rg -n "web search broadcast news noise host fix|mbn\\.co\\.kr|sbs\\.co\\.kr|kbs\\.co\\.kr|ytn\\.co\\.kr|jtbc\\.co\\.kr|ichannela\\.com|tvchosun\\.com|news\\.google\\.com|blog\\.naver\\.com|cafe\\.daum\\.net" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/TASK_BACKLOG.md tests/test_smoke.py`
  - 결과 없음
- 수동 spot-check: `_looks_like_domain_specific_noise(hostname=..., title="테스트 기사", line="입력 2026.04.01 09:00 김철수 기자 무단전재 및 재배포 금지")`
  - `mbn.co.kr -> True`
  - `news.sbs.co.kr -> True`
  - `news.kbs.co.kr -> True`
  - `www.ytn.co.kr -> True`
  - `news.jtbc.co.kr -> True`
  - `www.ichannela.com -> True`
  - `news.tvchosun.com -> True`
  - `news.google.com -> False`
  - `blog.naver.com -> False`
  - `cafe.daum.net -> False`
- source-classification contract 확인
  - `https://www.mbn.co.kr/news/economy/5000001 -> news`
  - `https://news.sbs.co.kr/news/endPage.do?news_id=N1001 -> news`
  - `https://news.kbs.co.kr/news/pc/view/view.do?ncd=8000001 -> news`
  - `https://www.ytn.co.kr/_ln/0102_202604010001 -> news`
  - `https://news.jtbc.co.kr/article/article.aspx?news_id=NB12100001 -> news`
  - `https://www.ichannela.com/news/main/news_detail.do?publishId=000000001 -> news`
  - `https://news.tvchosun.com/site/data/html_dir/2026/04/01/2026040100001.html -> news`
- residual scan 확인
  - `core/source_policy.py`의 `news_domain_hosts`는 80건, `tools/web_search.py`의 `news_hosts`는 37건이었습니다.
  - current source-classification contract 대비 web-search boilerplate 필터에 아직 미복구 host가 43건 남아 있음을 확인했습니다.
- browser-visible contract 변경은 아니라 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- broadcast/newsroom host 7건 mismatch는 닫혔지만, current source-classification contract 대비 `tools/web_search.py`의 news boilerplate/noise 필터에는 여전히 43개 host가 빠져 있습니다.
- 그중 첫 residual인 `sisajournal.com`은 `classify_source_type("https://www.sisajournal.com/news/articleView.html?idxno=123456") -> news`인데 `_looks_like_domain_specific_noise(hostname="www.sisajournal.com", title="테스트 기사", line="입력 2026.04.01 09:00 김철수 기자 무단전재 및 재배포 금지") -> False`라서 current contract와 page-text refinement가 아직 어긋납니다.
- 자동화를 deterministic하게 이어가기 위해 다음 단일 슬라이스는 current source-policy order 기준 첫 미복구 host인 `sisajournal.com` 1건으로 고정했습니다.
- 이번 검수는 latest Claude round truth 확인과 same-family next-slice 선정에 한정했습니다. whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
