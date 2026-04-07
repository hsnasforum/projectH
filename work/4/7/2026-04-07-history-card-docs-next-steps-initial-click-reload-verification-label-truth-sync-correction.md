# history-card docs-next-steps initial click-reload verification-label truth-sync correction

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 baseline history-card click-reload clause가 `설명형 다중 출처 합의`로 적혀 있었으나 root docs(README, MILESTONES, ACCEPTANCE_CRITERIA)는 모두 `설명형 단일 출처`를 current truth로 적고 있어 mismatch.

## 핵심 변경
- `설명형 다중 출처 합의` → `설명형 단일 출처` correction

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
