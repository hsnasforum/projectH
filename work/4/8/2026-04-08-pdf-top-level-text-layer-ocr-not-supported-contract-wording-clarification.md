# PDF top-level text-layer + OCR-not-supported contract wording clarification

## 변경 파일

- `README.md` (line 66)
- `docs/ACCEPTANCE_CRITERIA.md` (lines 33-34)
- `docs/MILESTONES.md` (lines 98-99)
- `docs/TASK_BACKLOG.md` (line 22)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- top-level contract는 generic `PDF text-layer support` / `OCR-not-supported guidance`로만 적혀 있었음
- scenario-level docs와 smoke는 이미 readable text-layer → visible summary body + `문서 요약` label + filename, scanned/image-only → visible guidance + exact strings까지 직접 고정
- top-level contract를 same truth 수준으로 정렬

## 핵심 변경

- README:66: generic one-liner → readable/scanned 양쪽 exact behavior 명시
- ACCEPTANCE:33-34: generic → readable → `문서 요약` label + filename, scanned → exact strings
- MILESTONES:98-99: generic → readable/scanned exact behavior 명시
- TASK_BACKLOG:22: generic → readable → `문서 요약` label, scanned → exact strings

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
