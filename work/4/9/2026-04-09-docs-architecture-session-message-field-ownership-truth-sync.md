# docs: ARCHITECTURE session message field ownership truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — Current message records 서브섹션(line 196-229)을 소유권 기반 3개 그룹으로 재구조화

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 기존 문서는 모든 optional 필드를 단일 플랫 목록으로 기술
- 실제 출하 동작은 메시지 유형별로 소유권이 다름:
  - `response_origin`: 존재 시에만 기록, 부재 시 키 생략 (null 아님)
  - `original_response_snapshot`, `corrected_text`, `corrected_outcome`, `content_reason_record`: 원본 grounded-brief 소스 메시지 전용
  - `save_content_source`, `source_message_id`: 소스 메시지 + 저장/승인 트레이스 메시지 양쪽
  - `approval_reason_record`: 거절/재발행 승인 트레이스 메시지 전용
- `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 이미 소유권 기반으로 정확하게 기술

## 핵심 변경
- 플랫 목록 → 3개 그룹 분리:
  1. 일반 응답 메타데이터 (모든 응답 메시지)
  2. grounded-brief 소스 메시지 전용 필드
  3. 승인 트레이스 메시지 전용 필드
- `response_origin` omission 시맨틱 명시
- `original_response_snapshot`에 중첩 `response_origin` nullable 주석 추가
- `save_content_source`/`source_message_id` 양쪽 소유 교차 참조

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 13줄 추가 / 9줄 제거 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 3개 권위 문서 모두 세션 메시지 필드 소유권 진실 동기화 완료
