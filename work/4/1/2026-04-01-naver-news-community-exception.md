# 2026-04-01 news.naver.com community exception fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `news.naver.com`이 community로 내려가는 문제를 좁게 보정하도록 지시.
- `news.naver.com`은 실제 포털 뉴스 host인데 `naver.com` community 판정에 걸려 기사형 source-role을 잃는 concrete current-risk.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`의 news_host_hints에 `"news.naver.com"` 추가
- news_host_hints 체크가 community_hosts보다 먼저 실행되므로 `news.naver.com`은 news로 분류
- `blog.naver.com`, 일반 `*.naver.com`은 변경 없이 community 유지
- `tests/test_source_policy.py`에 `news.naver.com -> news`, `blog.naver.com -> community` assertion 추가
- `tests/test_web_app.py`에 `news.naver.com + mk + noisy community` badge contract 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 175 tests, OK (3.014s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- `news.naver.com` 1건만 예외 처리. `news.daum.net` 같은 다른 포털 뉴스 서브도메인은 별도 처리 필요할 수 있음.
- dirty worktree가 여전히 넓음.
