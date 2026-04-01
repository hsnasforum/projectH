# 2026-04-01 news substring false-positive fix

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, bare `"news"` substring hint의 false-positive를 줄이도록 지시.
- `unknownlocalnews.kr` 같은 arbitrary hostname이 `news`로 오인되는 concrete current-risk.
- 기존 explicit news-domain coverage는 유지하면서 false-positive만 제거하는 가장 작은 수정.

## 핵심 변경
- `classify_source_type`와 `_classify_web_source_kind`에서 bare `"news"` / `"news."` substring hint를 hints 튜플에서 제거
- 대신 `hostname.startswith("news.")` 조건으로 `news.` 서브도메인(예: `news.example.com`, `news.sbs.co.kr`)만 매칭
- `unknownlocalnews.kr`처럼 도메인 본문에 `news`가 포함된 미등록 host는 더 이상 news로 오인되지 않음
- 기존 explicit domains (`newsis.com`, `news1.kr`, `nocutnews.co.kr`, `etnews.com` 등)은 모두 별도 entry로 커버돼 변경 없이 유지

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 173 tests, OK (2.953s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- 수동 확인:
  - `classify_source_type('https://www.unknownlocalnews.kr/article/1') == 'general'` ✓
  - `classify_source_type('https://news.example.com/article') == 'news'` ✓
  - `classify_source_type('https://www.newsis.com/view/NISX20260401_0001') == 'news'` ✓

## 남은 리스크
- `hostname.startswith("news.")` 패턴으로 `news.` 서브도메인은 여전히 일괄 news로 분류됨. 이는 대부분 실제 뉴스 서브도메인이므로 현재 수준에서는 허용 가능.
- dirty worktree가 여전히 넓음.
