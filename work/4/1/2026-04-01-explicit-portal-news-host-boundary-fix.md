# 2026-04-01 explicit portal news host boundary fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, portal news host 5건의 substring 매칭을 exact-or-subdomain boundary로 좁히도록 지시.
- 기존 substring 매칭 `hint in hostname`으로 `notnews.nate.com`, `notnews.zum.com` 같은 suffix-like 가짜 host가 `news`로 오인되는 concrete current-risk.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`에서 portal news host 5건(`news.naver.com`, `v.daum.net`, `news.daum.net`, `news.nate.com`, `news.zum.com`)을 news_host_hints substring 튜플에서 분리
- 별도 `portal_news_hosts` 튜플로 옮기고 `hostname == host or hostname.endswith(f".{host}")` exact-or-subdomain 매칭 적용
- positive 유지: `news.naver.com`, `m.news.nate.com`, `m.news.zum.com` 등 실제 host/서브도메인은 계속 news
- false-positive 차단: `notnews.nate.com`, `notnews.zum.com` 등 suffix-like 가짜 host는 general
- broader news_host_hints (`yna`, `mk`, `chosun` 등)는 변경하지 않음
- `tests/test_source_policy.py`에 `m.news.nate.com -> news`, `m.news.zum.com -> news`, `notnews.nate.com -> general`, `notnews.zum.com -> general` assertion 추가
- `tests/test_web_app.py`에 `notnews.nate.com` fake portal-news host regression 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 180 tests, OK (3.063s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- broader news_host_hints의 substring 매칭은 여전히 유지됨. 이들 중 일부도 boundary 매칭으로 좁힐 수 있으나 이번 라운드 범위 밖.
- dirty worktree가 여전히 넓음.
