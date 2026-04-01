# 2026-04-01 news.zum.com community exception fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `news.zum.com`을 news로 복구하도록 지시.
- `news.zum.com`은 실제 포털 뉴스 host인데 현재 `general`로 분류돼 기사형 source-role을 잃는 concrete current-risk.
- 이전 라운드에서 `news.nate.com`이 닫혔고, `news.zum.com`이 같은 family의 마지막 explicit residual.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`의 news_host_hints에 `"news.zum.com"` 추가
- news_host_hints 체크가 community_hosts/general fallback보다 먼저 실행되므로 `news.zum.com`은 news로 분류
- `tests/test_source_policy.py`에 `news.zum.com -> news` assertion 추가
- `tests/test_web_app.py`에 `news.zum.com + mk + noisy community` badge contract 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 179 tests, OK (3.124s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- 주요 포털 뉴스 서브도메인(`news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`)은 모두 보정 완료.
- dirty worktree가 여전히 넓음.
