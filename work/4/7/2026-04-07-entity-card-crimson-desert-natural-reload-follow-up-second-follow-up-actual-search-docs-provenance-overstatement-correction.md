# entity-card crimson-desert natural-reload follow-up/second-follow-up actual-search docs provenance overstatement correction

날짜: 2026-04-07

## 변경 파일
- `README.md`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only overstatement correction)

## 변경 이유
- actual-search continuity anchors (`e2e/tests/web-smoke.spec.mjs:4870/5045`, `tests/test_web_app.py:16443/16582`)는 `namu.wiki`, `ko.wikipedia.org` two-source continuity만 직접 잠급니다.
- `blog.example.com` provenance continuity는 noisy-exclusion family anchors (`e2e/tests/web-smoke.spec.mjs:5107/5186`, `tests/test_web_app.py:17275/17332`)에서만 직접 잠겨 있습니다.
- 이전 라운드에서 actual-search general continuity docs에 `blog.example.com` provenance를 넣었으나, 이는 actual-search anchors가 잠그는 truth보다 강한 overstatement였습니다.

## 핵심 변경
- 5개 파일의 actual-search general continuity lines에서 `blog.example.com` provenance 제거
- noisy-exclusion family lines의 `blog.example.com` provenance wording은 그대로 유지
- scenario count 75 유지

## 검증
- `git diff --check`: clean
- actual-search anchors truth (two-source)와 docs wording 일치 확인

## 남은 리스크
- 없음 (docs-only correction, noisy-exclusion family에서 `blog.example.com` provenance는 여전히 잠김)
