# PDF top-level readable text-layer transcript-meta contract wording clarification

## 변경 파일

- `README.md` (line 66)
- `docs/ACCEPTANCE_CRITERIA.md` (line 33)
- `docs/MILESTONES.md` (line 98)
- `docs/TASK_BACKLOG.md` (line 22)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4곳 모두 top-level readable text-layer PDF contract에서 `context box/quick meta`만 적고 `transcript meta`를 반영하지 않았음
- scenario-level docs와 smoke는 이미 quick meta + transcript meta 양쪽에서 PDF filename + `문서 요약` label을 직접 고정
- top-level contract를 same truth에 맞게 정렬

## 핵심 변경

- README:66: `context box/quick meta` → `context box/quick meta/transcript meta`
- ACCEPTANCE:33: `context box/quick meta` → `context box/quick meta/transcript meta`
- MILESTONES:98: `context box/quick meta` → `context box/quick meta/transcript meta`
- TASK_BACKLOG:22: `문서 요약 label` → `문서 요약 label in quick meta + transcript meta`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
