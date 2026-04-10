# docs: response status enum truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — `status` 필드 설명에서 `completed` 제거, `core/contracts.py:ResponseStatus` 정규 열거형(`answer`, `error`, `needs_approval`, `saved`) 명시
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블 `status` 행에서 `completed` 제거, 정규 열거형 + 소스 참조 명시
- `docs/ACCEPTANCE_CRITERIA.md` — 셸 제어 필드 요약에 `status` 열거형 값 + `core/contracts.py:ResponseStatus` 참조 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 응답 페이로드 계약을 문서화할 때 `status` 예시로 `completed`를 사용했으나, 정규 열거형(`core/contracts.py:16-20`)에는 `completed`가 존재하지 않음
- `core/agent_loop.py`와 테스트(`tests/test_web_app.py`, `tests/test_smoke.py`)는 오직 `answer`, `error`, `needs_approval`, `saved`만 사용
- 문서와 구현 간 진실 불일치 해소

## 핵심 변경
- 3개 문서 모두에서 `completed` 대신 정규 `ResponseStatus` 열거형 4개 값을 명시
- `core/contracts.py:ResponseStatus`를 단일 진실 소스로 참조 추가

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md` — 3개 파일, 각 1줄 변경 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 이 슬라이스는 응답 페이로드 `status` 필드 진실 동기화만 완료
