# history-card latest-update single-source news-only docs-next-steps family-closure truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 single-source/news-only summary가 verification-label/source-path만 분절적으로 적고 `WEB`/`최신 확인` continuity와 second-follow-up closure를 빠뜨림.

## 핵심 변경
- single-source 8개 분절 항목: `WEB`, `최신 확인` retention/drift prevention + second-follow-up closure 명시
- news-only 8개 분절 항목: 동일 패턴 적용

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
