# 2026-04-01 web search portal news noise host fix

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, portal news host 5건을 `_looks_like_domain_specific_noise`의 news boilerplate 필터에 추가하도록 지시.
- `core/source_policy.py`가 이미 news contract로 취급하는 `news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`이 page-text refinement에서는 boilerplate 제거 대상이 아니어서 정책이 어긋나는 concrete current-risk.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에 5건 추가: `news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`
- 기존 exact-or-subdomain boundary 매칭 유지 → `m.news.nate.com`, `m.news.zum.com` 등 서브도메인도 자동 포함
- `news.google.com`, `blog.naver.com`, `cafe.daum.net`은 뉴스 boilerplate 필터에 걸리지 않음
- `tests/test_web_search_tool.py`에 `test_fetch_page_portal_news_host_boilerplate_boundary` 추가 (positive 5건 + negative 3건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 10 tests, OK (0.015s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과

## 남은 리스크
- portal news host boilerplate 정책과 source classification 정책이 이제 정합됨.
- dirty worktree가 여전히 넓음.
