# docs: NEXT_STEPS TASK_BACKLOG apply-boundary reopen wording truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — line 411-413: "next slice recommendation" / "prefer ... reopen" → "reviewed-memory apply boundary is now shipped"
- `docs/TASK_BACKLOG.md` — line 662: "before reopening enabled submit or emitted-record materialization" → "enabled submit and emitted-record materialization are now shipped"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- NEXT_STEPS가 apply boundary를 "next slice recommendation to reopen"으로 프레이밍
- TASK_BACKLOG가 "before reopening enabled submit"으로 프레이밍
- 동일 문서의 후속 행(NEXT_STEPS:418-420, TASK_BACKLOG:672-677, 717)에서 이미 shipped로 기술
- MILESTONES(line 320-340)도 이미 shipped로 기술

## 핵심 변경
- NEXT_STEPS: "next slice recommendation" → "reviewed-memory apply boundary is now shipped", "reopen only one exact reviewed-memory-apply boundary layer" → "lifecycle is now shipped above that emitted record"
- TASK_BACKLOG: "before reopening enabled submit or emitted-record materialization" → "enabled submit and emitted-record materialization are now shipped"

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 3줄 추가 / 4줄 제거 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서의 apply-boundary "reopen" 프레이밍 진실 동기화 완료
