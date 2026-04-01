# 2026-04-01 corrected_text reflected in next summary docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `verify/4/1/2026-04-01-corrected-text-reflected-in-next-summary-verification.md` 기준으로, 코드 구현은 truthful하지만 docs에 교정 후 active_context.summary_hint 갱신 behavior가 미반영.
- same-family 안의 가장 작은 current-risk reduction인 docs truth sync 1건.

## 핵심 변경
- `README.md`: correction submit bullet에 active_context.summary_hint 갱신으로 후속 요약이 교정 텍스트 기반이 된다는 설명 추가
- `docs/PRODUCT_SPEC.md`: correction-submit contract에 active_context.summary_hint 갱신(240자 truncation)과 same-session follow-up basis 변경 명시
- `docs/ACCEPTANCE_CRITERIA.md`: correction submit acceptance에 active_context가 있을 때 summary_hint가 corrected_text 기반으로 갱신된다는 항목 추가
- reviewed-memory, candidate, approval contract wording 확장 없음

## 검증
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`: 통과
- docs-only round이므로 Python/browser 검증은 실행하지 않음

## 남은 리스크
- docs-only 변경이므로 기능적 리스크 없음
- corrected_text → next summary family는 코드 + docs sync까지 truthfully 닫힘
