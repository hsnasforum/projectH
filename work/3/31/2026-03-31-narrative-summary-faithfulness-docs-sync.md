# 2026-03-31 narrative summary faithfulness docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 local-document summary prompt에 strict source-anchored faithfulness 규칙을 추가하고 `docs/ACCEPTANCE_CRITERIA.md`에 반영했으나, `README.md`와 `docs/PRODUCT_SPEC.md`가 아직 "narrative-friendly guidance" 수준으로만 적혀 있어 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (2개 파일)
- `README.md`: local document summary 설명에 "with a strict source-anchored faithfulness rule (no fabricated events, no term substitution, no conclusions beyond what the text shows)" 추가
- `docs/PRODUCT_SPEC.md`: narrative/fiction summary guidance 항목에 동일 faithfulness rule 명시

### 변경하지 않은 것
- 코드 변경 없음
- 테스트 변경 없음
- `docs/ACCEPTANCE_CRITERIA.md`: 이전 라운드에서 이미 반영 완료

## 검증
- `git diff --check` (변경 파일) — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
