# 2026-03-31 README.md feature list metadata truth sync

## 목표
`README.md` 상단 feature list의 metadata bullet 1개를 현재 shipped metadata contract에 동기화.

## 변경 파일
- `README.md`: feature list metadata bullet 1개 교체

## 변경 내용
- 기존 bullet(source filename + source-type label 일반 설명)을 `docs/PRODUCT_SPEC.md`와 동일한 wording으로 교체:
  1. `문서 요약` / `선택 결과 요약` source-type label이 quick-meta와 transcript meta 모두에 노출
  2. single-source일 때 basename-based `출처 <filename>`, multi-source일 때 count-based `출처 N개`
  3. general chat response에는 source-type label 없음

## 검증
- `git diff --check -- README.md`: whitespace 오류 없음
- docs-only truth sync이므로 browser/unit 재실행 불필요

## 리스크
- 없음. 문서 동기화만 수행, 코드 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
