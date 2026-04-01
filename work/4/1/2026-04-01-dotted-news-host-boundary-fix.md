# 2026-04-01 dotted news host boundary fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, broader dotted news_host_hints의 substring 매칭을 exact-or-subdomain boundary로 좁히도록 지시.
- 기존 substring 매칭 `hint in hostname`으로 `foo-yna.co.kr`, `notmk.co.kr` 같은 suffix-like 가짜 host가 `news`로 오인되는 concrete current-risk.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`에서 news hints를 두 그룹으로 분리:
  - `news_fragment_hints` (`chosun`, `joongang`, `donga`): substring 매칭 유지
  - `news_domain_hosts` (나머지 dotted domain 전체 + portal news host 5건): `hostname == host or hostname.endswith(f".{host}")` exact-or-subdomain 매칭
- positive 유지: `www.yna.co.kr`, `m.yna.co.kr`, `www.mk.co.kr`, `m.mk.co.kr`, `news.sbs.co.kr`, `sportschosun.com` 등
- false-positive 차단: `foo-yna.co.kr`, `notmk.co.kr` → general
- fragment hints (`chosun`, `joongang`, `donga`)는 이번 라운드에 건드리지 않음
- `tests/test_source_policy.py`에 `m.yna.co.kr -> news`, `m.mk.co.kr -> news`, `foo-yna.co.kr -> general`, `notmk.co.kr -> general` assertion 추가
- `tests/test_web_app.py`에 `foo-yna.co.kr` fake dotted news host regression 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 181 tests, OK (3.085s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- fragment hints (`chosun`, `joongang`, `donga`)는 여전히 substring 매칭. 이번 라운드 범위 밖이며 별도 슬라이스로 다룰 수 있음.
- dirty worktree가 여전히 넓음.
