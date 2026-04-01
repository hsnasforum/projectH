# 2026-04-01 web search national news noise host fix

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, national-news host 11건을 `_looks_like_domain_specific_noise`의 news boilerplate 필터에 추가하도록 지시.
- `core/source_policy.py`가 이미 news contract로 취급하는 national-news host들이 page-text refinement에서는 boilerplate 제거 대상이 아니어서 정책이 어긋나는 concrete current-risk.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에 11건 추가: `hankyung.com`, `edaily.co.kr`, `etoday.co.kr`, `heraldcorp.com`, `zdnet.co.kr`, `dt.co.kr`, `seoul.co.kr`, `newdaily.co.kr`, `moneytoday.co.kr`, `segye.com`, `newsis.com`
- 기존 exact-or-subdomain boundary 매칭 유지
- `news.google.com`, `blog.naver.com`, `cafe.daum.net`은 boilerplate 필터에 걸리지 않음
- `tests/test_web_search_tool.py`에 `test_fetch_page_national_news_host_boilerplate_boundary` 추가 (positive 11건 + negative 3건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 11 tests, OK (0.019s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과

## 남은 리스크
- `core/source_policy.py`의 news_domain_hosts에는 지역신문 등 더 많은 host가 있으나, boilerplate 필터에는 아직 미등록. 필요시 다음 슬라이스로 추가 가능.
- dirty worktree가 여전히 넓음.
