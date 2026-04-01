# 2026-03-31 uploaded search failure docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 이전 라운드에서 추가한 uploaded search partial-failure notice의 docs sync를 지시.
- 업로드 검색 경로에서 일부 파일 읽기 실패 시 count-only partial-failure notice가 existing notice surface에 붙는 현재 shipped behavior가 docs에 반영되지 않았음.

## 핵심 변경
- `README.md`: uploaded folder search partial-failure notice 항목 추가 (PDF OCR guidance 바로 아래)
- `docs/PRODUCT_SPEC.md`: PDF Rules > Implemented 섹션에 uploaded folder search partial-failure notice 항목 추가, OCR guidance와 별도 경로임을 명시
- `docs/ACCEPTANCE_CRITERIA.md`: OCR guidance 항목 바로 아래에 uploaded folder search partial-failure notice acceptance criterion 추가, OCR 경로와 분리됨을 명시
- code, test, Playwright, pipeline policy, reviewed-memory 변경 없음 — docs-only slice

## 검증
- 문구 대조: 3개 파일 모두에서 "partial-failure" / "count-only" / "읽지 못해 검색에서 제외" 확인
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`: 통과
- docs-only round이므로 코드 테스트는 실행하지 않음

## 남은 리스크
- dirty worktree가 여전히 넓음.
