# browser file picker readable text-layer PDF docs exact-field wording clarification

## 변경 파일

- `README.md` (line 190)
- `docs/MILESTONES.md` (line 102)
- `docs/TASK_BACKLOG.md` (line 97)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1399)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4곳 모두 context box + quick meta만 적고 transcript meta truth를 반영하지 않았음
- current smoke는 quick meta와 transcript meta 모두에서 `readable-text-layer.pdf` + `문서 요약`를 직접 고정
- docs wording을 actual smoke coverage에 맞게 transcript meta truth를 추가

## 핵심 변경

- 4곳 모두: `context box + quick meta` → `context box + quick meta + transcript meta`로 확장, `문서 요약` label도 `quick meta + transcript meta` 양쪽 반영

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
