# docs: response_origin nullable truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 응답 페이로드 메타데이터 필드 섹션에서 `response_origin` 설명에 `or null when absent` 추가
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블에서 `response_origin` 타입을 `object` → `object | null`로 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 세션/트레이스 게이트 per-message 필드에서 `response_origin` 설명에 `or null when absent` 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:80`에서 `AgentResponse.response_origin`은 `dict[str, Any] | None`으로 정의
- `app/serializers.py:333-345`는 origin 부재 시 `None` 반환
- 에러 경로(`core/agent_loop.py:391-395`, `399-403`, `8775-8794`)에서 `response_origin` 없이 `AgentResponse` 반환
- 셸(`app/static/app.js:3153, 3170, 3196`)도 이미 nullable로 소비
- 문서만 object 전용으로 기술하여 진실 불일치 존재

## 핵심 변경
- 3개 문서 모두에서 `response_origin`을 nullable로 표기하고, 에러 경로에서 `null`이 될 수 있음을 명시

## 검증
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `response_origin` nullability 진실 동기화 완료
