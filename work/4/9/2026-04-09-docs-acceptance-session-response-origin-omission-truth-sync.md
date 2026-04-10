# docs: ACCEPTANCE_CRITERIA session response_origin omission truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — per-message 필드 목록(line 93)에서 `response_origin` 부재 시맨틱 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 세션 메시지에서 `response_origin` 부재 시 동작:
  - 최상위 응답 페이로드: `null` 반환
  - 세션 메시지: 키 자체를 생략 (omission)
- `core/agent_loop.py:7367-7368`은 `response_origin` 존재 시에만 메시지에 기록
- `app/serializers.py:91-100`과 `app/localization.py:146-177`도 누락 필드를 합성하지 않음
- 문서가 `or null when absent`로 기술하여 최상위 페이로드와 혼동 발생

## 핵심 변경
- `or null when absent (e.g. error responses)` → `when present; omitted from the session message when absent (unlike the top-level response payload, which returns null)`

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 세션 메시지 `response_origin` omission vs null 진실 동기화 완료
