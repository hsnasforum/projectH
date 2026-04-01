# 2026-04-01 news.nate.com community exception fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 `news.nate.com` 1건을 다음 same-family current-risk reduction으로 확정.
- `news.nate.com`은 실제 포털 뉴스 host인데 현재 `general`로 분류돼 기사형 source-role을 잃는 concrete current-risk.
- `news.zum.com`은 이번 라운드에 묶지 않고 다음 residual로 남김.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`의 news_host_hints에 `"news.nate.com"` 추가
- news_host_hints 체크가 community_hosts보다 먼저 실행되므로 `news.nate.com`은 news로 분류
- `tests/test_source_policy.py`에 `news.nate.com -> news` assertion 추가
- `tests/test_web_app.py`에 `news.nate.com + mk + noisy community` badge contract 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 178 tests, OK (3.123s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- `news.zum.com`이 다음 same-family residual로 남아 있음.
- dirty worktree가 여전히 넓음.
