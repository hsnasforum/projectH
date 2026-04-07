# history-card latest-update mixed-source docs-next-steps family-closure truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 mixed-source summary가 source-path continuity만 적고 response-origin retention과 second-follow-up closure를 빠뜨림.

## 핵심 변경
- initial reload: + response-origin continuity + `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` retention
- follow-up: + response-origin continuity + drift prevention + second-follow-up closure

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
