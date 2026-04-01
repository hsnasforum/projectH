# 2026-04-01 web search news noise host boundary fix

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `tools/web_search.py`의 `_looks_like_domain_specific_noise` 안 news boilerplate host 매칭을 exact-or-subdomain boundary로 좁히도록 지시.
- 기존 substring 매칭 + bare `"news"` token으로 `mychosun.com`, `foo-yna.co.kr`, `notmk.co.kr`, `news.google.com` 같은 fake/generic host가 뉴스 boilerplate 필터에 걸리는 concrete current-risk.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에서 bare `"news"` 제거
- substring 매칭 `hint in hostname`을 `hostname == h or hostname.endswith(f".{h}")` exact-or-subdomain으로 교체
- positive 유지: `www.chosun.com`, `www.yna.co.kr`, `www.mk.co.kr` 등 실제 news host의 boilerplate 제거 동작 유지
- false-positive 차단: `mychosun.com`, `foo-yna.co.kr`, `notmk.co.kr`, `news.google.com`에서는 boilerplate 제거가 적용되지 않음
- `tests/test_web_search_tool.py`에 `test_fetch_page_news_noise_filter_exact_boundary` 추가 (positive 3건 + negative 4건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 9 tests, OK (0.007s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과

## 남은 리스크
- `tools/web_search.py`의 다른 noise 필터(blog, wiki, game portal 등)도 substring 매칭이 남아 있을 수 있으나 이번 라운드 범위 밖.
- dirty worktree가 여전히 넓음.
