# 2026-04-01 generic "news" substring false-positive reduction

## 변경 파일
- `tests/test_source_policy.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, `generic "news" substring false-positive reduction only` 단일 슬라이스를 지시.
- operator가 broader 42-host sweep을 accepted baseline으로 확정 후 false-positive guard를 current-risk reduction으로 고정.

## 핵심 변경
- `core/source_policy.py`와 `core/agent_loop.py`는 이전 라운드들에서 이미 bare `"news"` substring catch-all이 완전히 제거됨 — 추가 코드 변경 불필요
- `tests/test_source_policy.py`에 추가 false-positive edge case regression 2건 보강:
  - `fakenews.co.kr → general`
  - `mynewssite.com → general`
- 기존 guard 유지: `unknownlocalnews.kr → general`, `news.example.com → general`
- explicit news host positive 유지: `newsis.com`, `news.naver.com`, `news1.kr` 등 모두 `news`

## 검증
- `python3 -m unittest -v tests.test_source_policy`: 3 tests, OK (0.002s)
- `git diff --check -- core/source_policy.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- 수동 확인:
  - `classify_source_type('https://fakenews.co.kr/article/1') == 'general'` ✓
  - `classify_source_type('https://mynewssite.com/article/1') == 'general'` ✓
  - `classify_source_type('https://www.newsis.com/view/NISX20260401_0001') == 'news'` ✓

## 남은 리스크
- generic "news" substring false-positive family는 이제 코드 레벨에서 닫혔고, 테스트로 4건의 false-positive edge case가 잠김.
- 이후 새 news host 추가 시 news_domain_hosts에만 explicit 추가하면 false-positive 없이 커버됨.
- dirty worktree가 여전히 넓음.
