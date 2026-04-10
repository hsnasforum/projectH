# docs: ARCHITECTURE superseded historical signal anchor truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — Current message records의 grounded-brief 소스 메시지 섹션(line 223-224)에서 2개 시그널 필드에 앵커 조건 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `superseded_reject_signal`과 `historical_save_identity_signal`이 generic으로 남아 있었음
- 출하 동작:
  - `superseded_reject_signal`: 소스 메시지 앵커 + eligible `session_local_memory_signal` 경로 필요 (`app/serializers.py:147-151, 4703-4727`)
  - `historical_save_identity_signal`: 소스 메시지 앵커 + `session_local_memory_signal`의 `save_signal` 필요 (`app/serializers.py:153-158, 4729-4765`)
- PRODUCT_SPEC과 ACCEPTANCE_CRITERIA는 이미 grounded-brief 소스 메시지 전용으로 기술

## 핵심 변경
- `superseded_reject_signal`: `requires source-message anchor and eligible session_local_memory_signal path` 추가
- `historical_save_identity_signal`: `requires source-message anchor and session_local_memory_signal with save_signal` 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 2줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 모두 세션 메시지 메모리/후보 루트 조건 상세 진실 동기화 완료
