# 2026-04-01 fragment news hint boundary fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, fragment-style hint 3건(`chosun`, `joongang`, `donga`)의 substring 매칭을 explicit domain boundary로 교체하도록 지시.
- 기존 substring 매칭으로 `mychosun.com`, `fakejoongang.example` 같은 가짜 host가 `news`로 오인되는 concrete current-risk.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`에서 `news_fragment_hints` 튜플과 substring 매칭 완전 제거
- `news_domain_hosts`에 `chosun.com`, `joongang.co.kr`, `donga.com` 3건 추가 (exact-or-subdomain 매칭)
- `sportschosun.com`, `tvchosun.com`은 기존 `news_domain_hosts`에 이미 존재하므로 positive 유지
- positive 유지: `www.chosun.com`, `www.joongang.co.kr`, `www.donga.com`, `sportschosun.com`, `news.tvchosun.com`
- false-positive 차단: `mychosun.com`, `fakejoongang.example`, `notdonga.example` → general
- `tests/test_source_policy.py`에 positive 3건 + false-positive 3건 assertion 추가
- `tests/test_web_app.py`에 `mychosun.com` fake fragment host regression 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 182 tests, OK (3.113s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- 이제 모든 news host hints가 exact-or-subdomain boundary 매칭으로 통일됨. substring false-positive family는 완전히 닫힘.
- dirty worktree가 여전히 넓음.
