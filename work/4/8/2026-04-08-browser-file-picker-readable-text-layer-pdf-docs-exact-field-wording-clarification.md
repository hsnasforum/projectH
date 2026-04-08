# browser file picker readable text-layer PDF docs exact-field wording clarification

## 변경 파일

- `README.md` (line 190)
- `docs/MILESTONES.md` (line 102)
- `docs/TASK_BACKLOG.md` (line 97)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1399)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4곳 모두 `정상 요약 성공` / `OCR 안내 미노출` / filename 표시 수준으로만 적고 있었으나, actual smoke는 이미 visible summary body with extracted text, context box/quick meta filename, `문서 요약` label까지 직접 고정
- docs wording을 actual smoke coverage 범위에 맞게 truthful하게 정렬

## 핵심 변경

- 4곳 모두: generic `정상 요약` → OCR guidance 미노출 + visible summary body with extracted text(`local-first approval-based document assistant`) + context box/quick meta `readable-text-layer.pdf` + `문서 요약` label

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
