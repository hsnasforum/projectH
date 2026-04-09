# docs: AGENTS CLAUDE PROJECT_CUSTOM_INSTRUCTIONS response-feedback grounded-brief surface truth sync

## 변경 파일
- `AGENTS.md` — 2줄 추가(line 42-43): response feedback capture + grounded-brief trace/correction surface
- `CLAUDE.md` — 2줄 추가(line 21-22): response feedback capture + grounded-brief trace/correction surface
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 2줄 추가(line 19-20): 응답 피드백 수집 + grounded-brief trace/correction surface

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3개 instruction docs의 current product slice 목록에 shipped surface 2종 누락:
  - response feedback capture
  - grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, artifact-linked reject/reissue reason traces
- 근거 앵커: `README.md:57-62`, `docs/PRODUCT_SPEC.md:48-64`

## 핵심 변경
- 3개 파일 모두 동일한 패턴으로 2줄 추가
- response feedback capture 단독 항목
- grounded-brief trace/correction surface를 한 줄로 요약
- structured correction memory나 durable preference memory 주장 없음
- 기존 스타일/간결성 유지 (PROJECT_CUSTOM_INSTRUCTIONS.md는 한국어 혼용)

## 검증
- `git diff --stat` — 3 files changed, 6 insertions(+)
- `rg` — response feedback capture, grounded-brief artifact trace 3개 파일 모두 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — instruction docs의 response-feedback + grounded-brief surface 동기화 완료
