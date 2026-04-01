# 2026-04-01 web search broadcast news noise host fix

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, broadcast/newsroom host 7건을 `_looks_like_domain_specific_noise`의 news boilerplate 필터에 추가하도록 지시.
- `core/source_policy.py`가 이미 news contract로 취급하는 방송사 host들이 page-text refinement에서는 boilerplate 제거 대상이 아니어서 정책이 어긋나는 concrete current-risk.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에 7건 추가: `mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`
- 기존 exact-or-subdomain boundary 매칭 유지
- `news.google.com`, `blog.naver.com`, `cafe.daum.net`은 boilerplate 필터에 걸리지 않음
- `tests/test_web_search_tool.py`에 `test_fetch_page_broadcast_news_host_boilerplate_boundary` 추가 (positive 7건 + negative 3건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 12 tests, OK (0.031s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과

## 남은 리스크
- `core/source_policy.py`의 news_domain_hosts에는 지역신문, IT전문지 등 더 많은 host가 있으나 boilerplate 필터에는 아직 미등록. 필요시 다음 슬라이스로 추가 가능.
- dirty worktree가 여전히 넓음.
