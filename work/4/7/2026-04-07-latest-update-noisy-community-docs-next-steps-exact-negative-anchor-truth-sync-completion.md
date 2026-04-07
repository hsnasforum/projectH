# latest-update noisy-community docs-next-steps exact negative-anchor truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 root summary가 latest-update noisy-community family에서 `brunch`를 explicit negative anchor로 적지 않아 later docs와 token-level truth-sync가 완료되지 않았습니다.

## 핵심 변경
1. noisy community exclusion wording에 `brunch` explicit negative anchor 추가 (`보조 커뮤니티` and `brunch` in origin detail, response body, and context box)

## 검증
- `brunch count: 1` 확인
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
- latest-update noisy-community family와 entity-card noisy single-source claim family 모두 root summary 포함 전체 경로에서 truth-sync 완료 상태입니다.
