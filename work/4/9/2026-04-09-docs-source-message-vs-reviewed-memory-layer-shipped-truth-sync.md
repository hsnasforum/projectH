# docs: source-message trace vs reviewed-memory layer current-shipped wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 1059, 1062): "later reviewed-memory layer" / "future reviewed memory remains a later" → "shipped reviewed-memory layer" / "now shipped"
- `docs/ARCHITECTURE.md` — 2곳(line 798, 802): "later reviewed-memory layer" / "remains a later" → "shipped" / "now shipped"
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 585, 589): "later reviewed-memory layer" / "remains later" → "shipped" / "now shipped"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 소스 메시지 트레이스 vs reviewed-memory 레이어 요약이 전체 reviewed-memory 레이어를 "later"/"future"로 프레이밍
- 실제로 boundary/contract/apply/stop/reversal/conflict-visibility 모두 이미 출하됨
- promotion과 cross-session counting만 실제로 later

## 핵심 변경
- 6개 행에서 "later"/"future" → "shipped" + "(apply / stop-apply / reversal / conflict-visibility are shipped; promotion and cross-session counting remain later)"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 6줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 소스 메시지 트레이스 vs reviewed-memory 레이어 요약 shipped 문구 진실 동기화 완료
