# browser file picker scanned-image-only PDF docs exact-field wording clarification

## 변경 파일

- `README.md` (line 188)
- `docs/MILESTONES.md` (line 100)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `README.md:188`는 `OCR` 토큰이 빠져 있었고 `visible` 수식어가 없었음
- `MILESTONES.md:100`는 generic `OCR-not-supported guidance smoke`로만 적혀 있어 exact strings를 반영하지 않았음
- `TASK_BACKLOG.md:95`와 `ACCEPTANCE_CRITERIA.md:1397`는 이미 4개 exact strings를 모두 포함하고 있어 수정 불필요
- docs wording을 actual smoke coverage 범위에 맞게 truthful하게 정렬

## 핵심 변경

- `README.md:188`: `OCR 미지원 안내(요약할 수 없습니다, 이미지형 PDF, 다음 단계:)` → `visible OCR 미지원 안내(요약할 수 없습니다, OCR, 이미지형 PDF, 다음 단계:)`
- `MILESTONES.md:100`: generic smoke → `covering visible response guidance with exact strings 요약할 수 없습니다, OCR, 이미지형 PDF, 다음 단계:`

## 검증

- `git diff --check -- README.md docs/MILESTONES.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
