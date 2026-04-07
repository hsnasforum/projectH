# history-card noisy-single-source initial-click-reload milestones-acceptance-task-backlog provenance truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/MILESTONES.md:52`, `docs/ACCEPTANCE_CRITERIA.md:1343`, `docs/TASK_BACKLOG.md:41`의 history-card entity-card `다시 불러오기` noisy single-source claim exclusion 초기 click-reload 항목이 `blog.example.com` provenance만 적고 있어, current truth (`README.md:134`, `docs/NEXT_STEPS.md:16`, `tests/test_web_app.py` service assertions)에서 확인되는 `namu.wiki`, `ko.wikipedia.org` provenance가 빠져 있었습니다.

## 핵심 변경
- 3개 파일 모두 context box/source_paths provenance를 `blog.example.com`만에서 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com`으로 확장
- 기존 `설명형 다중 출처 합의`, `백과 기반`, negative assertions, agreement-backed fact card retention wording 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`: clean
- README.md:134, NEXT_STEPS.md:16과의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, follow-up/second-follow-up chain lines 및 다른 family wording 변경 없음)
