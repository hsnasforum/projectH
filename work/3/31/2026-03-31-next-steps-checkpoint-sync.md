# 2026-03-31 docs/NEXT_STEPS.md Current Checkpoint truth sync

## 목표
`docs/NEXT_STEPS.md`의 `## Current Checkpoint` 구간에서 stale한 12-scenario 설명을 현재 shipped truth인 13-scenario metadata coverage 기준으로 동기화.

## 변경 파일
- `docs/NEXT_STEPS.md`: `## Current Checkpoint` 내 smoke coverage 설명 1곳 수정

## 변경 내용
- "12 browser scenarios" → "13 browser scenarios"
- 기존 설명 앞에 현재 shipped metadata coverage 설명 추가:
  - source-path summary + browser file picker: source filename + `문서 요약` in quick-meta/transcript meta
  - folder-search: `선택 결과 요약` + `출처 2개` in quick-meta/transcript meta
  - general chat: negative source-type label contract
- wording은 이미 truth-sync된 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 기준을 따름.

## 검증
- `git diff --check -- docs/NEXT_STEPS.md`: whitespace 오류 없음
- docs-only truth sync이므로 browser/unit 재실행 불필요

## 리스크
- 없음. 문서 동기화만 수행, 코드 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
