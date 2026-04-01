# 2026-04-01 news. subdomain false-positive fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, generic `hostname.startswith("news.")` catch-all의 false-positive를 줄이도록 지시.
- `news.example.com` 같은 arbitrary `news.` 서브도메인이 `news`로 오인되는 concrete current-risk.
- `news.sbs.co.kr`는 `sbs.co.kr` explicit hint로 이미 커버되므로, `startswith("news.")` catch-all을 완전히 제거해도 기존 coverage 유지.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`에서 `hostname.startswith("news.")` catch-all 제거
- 기존 explicit domains (`newsis.com`, `news1.kr`, `sbs.co.kr`, `etnews.com` 등)은 별도 hint로 계속 `news`
- `news.sbs.co.kr` → `sbs.co.kr` hint로 매칭 → `news` 유지
- `news.example.com` → 더 이상 매칭되지 않음 → `general`
- 기존 mixed-source 테스트 3건의 `news.example.com` URL을 `www.yna.co.kr` (실제 등록 news domain)으로 교체
- `tests/test_source_policy.py`에 `news.example.com -> general`, `news.sbs.co.kr -> news` assertion 추가
- `tests/test_web_app.py`에 `news.example.com` false-positive badge contract 1건 추가

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 174 tests, OK (2.899s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- `news.` 서브도메인 catch-all 완전 제거. 미등록 실제 뉴스 사이트가 `news.` 서브도메인만 쓰는 경우 `general`로 분류될 수 있으나, explicit hint 추가로 대응 가능.
- dirty worktree가 여전히 넓음.
