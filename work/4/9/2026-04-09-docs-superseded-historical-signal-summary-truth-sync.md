# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA superseded historical signal summary truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Current Message Fields 섹션(line 268-269)에서 `superseded_reject_signal`과 `historical_save_identity_signal`에 앵커 조건 추가
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 메모리 시그널 요약(line 106)에서 3개 시그널 각각에 개별 조건 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- ARCHITECTURE는 이미 앵커 조건을 정확히 기술
- PRODUCT_SPEC과 ACCEPTANCE_CRITERIA의 요약 행만 `grounded-brief source message only`로 남아 조건 상세 누락
- 출하 동작:
  - `superseded_reject_signal`: 소스 메시지 앵커 + eligible `session_local_memory_signal` 경로 필요
  - `historical_save_identity_signal`: 소스 메시지 앵커 + `session_local_memory_signal`의 `save_signal` 필요

## 핵심 변경
- PRODUCT_SPEC: 2개 시그널 인라인 주석에 앵커/경로 조건 추가
- ACCEPTANCE_CRITERIA: 그룹 요약에서 3개 시그널 각각 개별 조건 괄호 주석 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 모두 메모리 시그널 앵커 조건 상세 진실 동기화 완료
