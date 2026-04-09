# docs: ARCHITECTURE web-investigation current-contract summary truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 3곳(line 11, 125-131, 1364): web investigation 요약 확장

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- ARCHITECTURE.md의 web investigation 관련 3개 섹션이 shipped surface를 압축하여 기술:
  - "web investigation remains a secondary mode" → disabled/approval/enabled per session 및 full surface 미반영
  - "response renders source roles and claim coverage state" → verification labels, answer-mode, claim-coverage panel detail 미반영
  - "claim coverage state and reinvestigation helpers" → status tags, actionable hints, focus-slot explanation 미반영
- 근거 앵커: `docs/PRODUCT_SPEC.md:153-155`, `docs/PRODUCT_SPEC.md:358-361`, `docs/NEXT_STEPS.md:18`

## 핵심 변경
- line 11: "secondary mode" → permission-gated (disabled/approval/enabled per session), history-card badges, entity-card / latest-update distinction, strong-badge downgrade, claim-coverage panel detail 포함
- line 125-131: web investigation flow 5-6단계 → 5-7단계로 확장, source-role trust labels, verification-strength, answer-mode, claim-coverage panel, entity-card distinction, history-card badges 반영
- line 1364: "claim coverage state and reinvestigation helpers" → claim-coverage panel + entity-card distinction + history-card badges로 3줄 분리

## 검증
- `git diff --stat` — 1 file changed, 7 insertions(+), 4 deletions(-)
- `rg` — history-card, entity-card/latest-update, claim-coverage panel, strong-badge downgrade, secondary mode 모두 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — ARCHITECTURE의 web-investigation current-contract summary 진실 동기화 완료
