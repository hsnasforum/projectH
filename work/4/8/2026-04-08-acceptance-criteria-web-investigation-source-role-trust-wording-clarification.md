# ACCEPTANCE_CRITERIA Web Investigation source-role trust wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음 (문서 전용 슬라이스)

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:53-55`에 answer-mode 분리 배지, claim-coverage source-role trust labels, response origin detail compact trust labels가 `In Progress`로 남아 있었으나, 실제 구현 코드(`app/static/app.js:217-220`, `app/static/app.js:2241-2255`, `app/static/app.js:2367-2368`, `app/static/app.js:2893-2899`)와 Playwright smoke 테스트(`e2e/tests/web-smoke.spec.mjs:1031-1114`)에서 이미 출하 확인됨.

## 핵심 변경

1. **Implemented (line 37)**: 기존 web investigation history 불릿에 answer-mode 분리 문구 추가 (`설명 카드` / `최신 확인` 배지)
2. **Implemented (line 38, 신규)**: claim coverage slots의 source role with trust level 전용 라인 불릿 추가
3. **Implemented (line 39, 신규)**: response origin detail의 compact trust labels 불릿 추가
4. **In Progress (lines 53-55)**: 위 3개 항목 제거, 실제 미완료인 2개 항목만 유지 (agreement-backed facts 우선순위, reinvestigation 약한 슬롯 개선)

## 검증

- `git diff -- docs/ACCEPTANCE_CRITERIA.md`: 4줄 삭제, 3줄 추가 (In Progress → Implemented 이동)
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`: whitespace 에러 없음
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '24,28p;50,56p'`: Implemented/In Progress 경계 정렬 확인 완료
- 구현 코드 확인: `app/static/app.js:220` (compact trust), `app/static/app.js:2368` (dedicated line trust), `app/static/app.js:2897-2898` (history-card trust badges)

## 남은 리스크

- In Progress에 남은 2개 항목 (agreement-backed facts, reinvestigation weak slots)은 실제 미완료이므로 그대로 유지.
- 이 슬라이스는 문서 진실 정렬만 수행했으며, 런타임이나 테스트 변경 없음.
