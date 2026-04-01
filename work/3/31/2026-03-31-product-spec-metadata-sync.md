# 2026-03-31 docs/PRODUCT_SPEC.md Response Panels metadata truth sync

## 목표
`docs/PRODUCT_SPEC.md`의 `## Response Panels And UI Metadata` > `### Implemented` 구간에서 UI metadata contract 설명을 현재 shipped truth에 동기화.

## 변경 파일
- `docs/PRODUCT_SPEC.md`: metadata bullet 1개 교체

## 변경 내용
- 기존 bullet(source filename + source-type label 일반 설명)을 다음 세 가지 contract를 명확히 드러내는 wording으로 교체:
  1. `문서 요약` / `선택 결과 요약` source-type label이 quick-meta와 transcript meta 모두에 노출
  2. single-source일 때 basename-based `출처 <filename>`, multi-source일 때 count-based `출처 N개`
  3. general chat response에는 source-type label 없음
- wording은 이미 truth-sync된 README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG 및 실제 구현(index.html)을 기준으로 맞춤.

## 검증
- `git diff --check -- docs/PRODUCT_SPEC.md`: whitespace 오류 없음
- docs-only truth sync이므로 browser/unit 재실행 불필요

## 리스크
- 없음. 문서 동기화만 수행, 코드 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
