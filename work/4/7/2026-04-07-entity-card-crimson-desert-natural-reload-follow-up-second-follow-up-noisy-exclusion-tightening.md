# entity-card crimson-desert natural-reload follow-up/second-follow-up noisy-exclusion tightening

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음

## 변경 이유
- crimson-desert natural-reload follow-up/second-follow-up에서 noisy 3-source record의 `출시일`, `2025`, `blog.example.com`이 본문/origin detail에 재노출되지 않는다는 current behavior가 browser test에서 잠겨 있지 않았습니다.
- service tests (`tests/test_web_app.py:17275`, `17332`)는 이미 3-source fixture로 noisy exclusion을 확인하지만, browser tests (`e2e/tests/web-smoke.spec.mjs`)는 2-source fixture만 사용하여 continuity만 확인하고 있었습니다.

## 핵심 변경
- 2개 새 browser scenario 추가:
  1. follow-up noisy single-source exclusion (negative `출시일`/`2025`/`blog.example.com` + continuity)
  2. second-follow-up noisy single-source exclusion (동일)
- scenario count 73 → 75
- README.md: 2개 scenario 추가, 56~75로 재번호
- NEXT_STEPS.md: 73→75, 2개 새 clause 추가
- MILESTONES.md: 2개 milestone entry 추가
- ACCEPTANCE_CRITERIA.md: 2개 criteria entry 추가
- TASK_BACKLOG.md: 2개 task entry 추가, 56~이후 재번호

## 검증
- `python3 -m unittest -v` noisy single-source natural-reload follow-up/second-follow-up service tests: pass
- `npx playwright test -g "entity-card 붉은사막 자연어 reload 후.*noisy"`: 2 passed
- `git diff --check`: clean

## 남은 리스크
- click-reload actual-search family에서의 동일 noisy-exclusion browser tightening은 이번 범위 밖 (service tests는 이미 커버)
