# docs: ARCHITECTURE ACCEPTANCE_CRITERIA correction field test-lock truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 응답 페이로드 테스트 잠금 문구(line 167)에 보정/저장 필드 앵커 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 응답 페이로드 테스트 잠금 문구(line 121)에 동일 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 문구는 8개 제어 필드만 테스트로 잠긴다고 기술
- 실제로는 `original_response_snapshot`, `corrected_outcome`, `save_content_source`, `approval_reason_record`, `content_reason_record`도 서비스/스모크 테스트에서 잠금
  - `tests/test_web_app.py:6187-6192, 6247-6257, 6391-6398, 7112-7117, 490-498`
  - `tests/test_smoke.py:4648-4664`
- 테스트 커버리지 설명이 출하 현실과 불일치

## 핵심 변경
- 2개 문서의 테스트 잠금 문구에 보정/저장 필드 5개 앵커 명시 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 각 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 계약 family 테스트 잠금 진실 동기화 완료
