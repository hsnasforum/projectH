# entity-card crimson-desert natural-reload follow-up/second-follow-up provenance-continuity tightening

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
- crimson natural-reload follow-up/second-follow-up dedicated browser tests가 `namu.wiki`, `ko.wikipedia.org` context box continuity만 확인하고 `blog.example.com` provenance는 직접 잠그지 않고 있었습니다.
- generic noisy-single-source service/browser anchors는 이미 `blog.example.com` provenance를 확인하지만, crimson-specific dedicated scenarios에는 해당 assertion이 누락되어 있었습니다.

## 핵심 변경
- 2개 browser test에 `await expect(contextBox).toContainText("blog.example.com")` assertion 추가
- README.md: 2개 scenario 설명에 `context box에 `blog.example.com` provenance가 포함 유지` 추가
- NEXT_STEPS.md, MILESTONES.md, ACCEPTANCE_CRITERIA.md, TASK_BACKLOG.md: 동일 provenance wording 동기화
- scenario count 75 유지 (기존 scenario 강화, 새 scenario 아님)

## 검증
- `npx playwright test -g "entity-card 붉은사막 자연어 reload 후.*noisy"`: 2 passed
- `git diff --check`: clean

## 남은 리스크
- click-reload family에서의 동일 provenance-continuity tightening은 이번 범위 밖
