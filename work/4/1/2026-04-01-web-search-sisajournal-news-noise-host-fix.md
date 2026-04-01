# 2026-04-01 web search sisajournal.com news noise host fix

## 변경 파일
- `tools/web_search.py`
- `tests/test_web_search_tool.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `sisajournal.com`을 `_looks_like_domain_specific_noise`의 news boilerplate 필터에 추가하도록 지시.
- `core/source_policy.py`가 이미 news contract로 취급하는 `sisajournal.com`이 page-text refinement에서는 boilerplate 제거 대상이 아니어서 정책이 어긋나는 concrete current-risk.

## 핵심 변경
- `_looks_like_domain_specific_noise`의 `news_hosts` 튜플에 `"sisajournal.com"` 추가
- 기존 exact-or-subdomain boundary 매칭 유지
- `tests/test_web_search_tool.py`에 `test_fetch_page_sisajournal_boilerplate_boundary` 추가 (positive 1건 + negative 3건)

## 검증
- `python3 -m unittest -v tests.test_web_search_tool`: 13 tests, OK (0.022s)
- `git diff --check -- tools/web_search.py tests/test_web_search_tool.py`: 통과

## 남은 리스크
- `core/source_policy.py`의 news_domain_hosts 80건 중 `tools/web_search.py` boilerplate 필터에 미등록인 host가 약 42건 남음. 1건씩 추가하는 것보다 operator가 broader sweep을 허용하면 한 번에 정리할 수 있음.
- dirty worktree가 여전히 넓음.
