# 2026-03-31 docs/ACCEPTANCE_CRITERIA.md capability bullets metadata truth sync

## 목표
`docs/ACCEPTANCE_CRITERIA.md` 상단 capability bullets의 metadata 관련 항목을 현재 shipped metadata contract에 동기화.

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md`: 기존 2개 bullet(lines 21-22)을 1개 bullet로 통합 교체

## 변경 내용
- 기존 분리된 2개 bullet(source filename in quick-meta + source-type label)을 1개 bullet로 통합:
  1. `문서 요약` / `선택 결과 요약` source-type label이 quick-meta와 transcript meta 모두에 노출
  2. single-source일 때 basename-based `출처 <filename>`, multi-source일 때 count-based `출처 N개`
  3. general chat response에는 source-type label 없음
- wording은 `README.md`, `docs/PRODUCT_SPEC.md`와 동일하게 맞춤.

## 검증
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`: whitespace 오류 없음
- docs-only truth sync이므로 browser/unit 재실행 불필요

## 리스크
- 없음. 문서 동기화만 수행, 코드 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
