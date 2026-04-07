# history-card entity-card dual-probe docs-next-steps family-closure truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 history-card dual-probe summary가 source-path continuity만 적고 response-origin retention과 second-follow-up closure를 빠뜨려 root/staged docs보다 약했습니다.

## 핵심 변경
- initial reload: source-path continuity → source-path + response-origin continuity + exact badge/label retention 명시
- follow-up: source-path continuity → source-path + response-origin continuity + drift prevention + second-follow-up closure 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
