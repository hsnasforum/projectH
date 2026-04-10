# docs: original_response_snapshot response_origin nullable truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 3곳: 응답 페이로드 보정 필드(line 318), 스냅샷 상세 필드(line 459), 두 번째 스냅샷 상세 필드(line 524)에서 `response_origin`에 `or null when absent` 추가
- `docs/ARCHITECTURE.md` — 1곳: 스냅샷 상세 필드(line 368)에서 동일 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳: per-message `original_response_snapshot` 설명(line 103)에 `nested response_origin may be null when absent` 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:220`에서 스냅샷 `response_origin`을 `dict(...)` 또는 `None`으로 저장
- `app/serializers.py:358`에서 동일한 nullable 헬퍼로 직렬화
- `tests/test_smoke.py:2725`에서 `response.original_response_snapshot["response_origin"] is None` 명시적 잠금
- 문서는 object-only 형태로 기술하여 진실 불일치 존재

## 핵심 변경
- 5개 위치에서 `original_response_snapshot.response_origin`이 `null`일 수 있음을 명시
- 세션 메시지의 optional `response_origin` 문구(PRODUCT_SPEC:257, ARCHITECTURE:205)는 이미 정확하므로 미변경

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `original_response_snapshot.response_origin` nullability 진실 동기화 완료
