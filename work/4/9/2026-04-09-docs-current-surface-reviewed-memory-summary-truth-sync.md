# docs: README AGENTS CLAUDE PROJECT_CUSTOM_INSTRUCTIONS NEXT_STEPS ACCEPTANCE_CRITERIA current-surface reviewed-memory summary truth sync

## 변경 파일
- `README.md` — 1곳(line 48): Current Product Slice 헤더에 reviewed-memory surface 언급 추가
- `AGENTS.md` — 1줄 추가(line 48): review queue + aggregate apply trigger + active-effect path
- `CLAUDE.md` — 1줄 추가(line 27): review queue + aggregate apply trigger + active-effect path
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1줄 추가(line 25): review queue + aggregate apply trigger + active-effect path
- `docs/NEXT_STEPS.md` — 1줄 추가(line 18): review queue + aggregate apply trigger + active-effect path
- `docs/ACCEPTANCE_CRITERIA.md` — 1줄 추가(line 25): review queue + aggregate apply trigger + active-effect path

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 6개 파일의 top-level current-product / current-result 요약에 shipped reviewed-memory surface 누락:
  - review queue (`검토 후보`)
  - aggregate apply trigger (`검토 메모 적용 후보`)
  - reviewed-memory active-effect path (apply / stop-apply / reversal / conflict-visibility)
- README 상세 목록(line 72-73)에는 이미 있지만 top-level 헤더에서 누락
- 근거 앵커: `docs/PRODUCT_SPEC.md:58`/`60`/`1520`/`1539`, `docs/ARCHITECTURE.md:29`/`79`/`80`

## 핵심 변경
- 6개 파일 각각에 1줄씩 reviewed-memory surface 요약 추가
- broader structured correction memory, durable preference memory 주장 없음
- 기존 스타일/간결성 유지

## 검증
- `git diff --stat` — 6 files changed, 6 insertions(+), 1 deletion(-)
- `rg '검토 후보|검토 메모 적용 후보|reviewed-memory'` — 모든 대상 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 current-surface reviewed-memory summary 동기화 완료
