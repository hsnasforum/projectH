# docs: response payload control-field summary truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — `## Current Response Payload Contract` 섹션 신규 추가 (Current Message Fields 이후, Response Panels 이전)
- `docs/ARCHITECTURE.md` — `## Current Response Payload Contract` 섹션 신규 추가 (Current Request Flows 이후, Current Persistence Surfaces 이전), 전체 필드 테이블 포함
- `docs/ACCEPTANCE_CRITERIA.md` — `### Response Payload Contract` 하위 섹션 신규 추가 (Session And Trace Gates 내)

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `app/serializers.py:_serialize_response`가 직렬화하는 최상위 응답 페이로드 필드 전체 목록이 권위 문서에 아직 요약되지 않았음
- 셸(`app/static/app.js`)과 테스트(`tests/test_web_app.py`, `tests/test_smoke.py`)가 직접 의존하는 8개 제어 필드(`status`, `actions_taken`, `requires_approval`, `proposed_note_path`, `saved_note_path`, `web_search_record_path`, `follow_up_suggestions`, `search_results`)의 계약을 문서화하여 현재 출하 계약과 문서 간 진실 동기화 완료

## 핵심 변경
- PRODUCT_SPEC: 필드별 역할 설명 + 제어/아이덴티티/콘텐츠/메타데이터/보정 5개 그룹 분류
- ARCHITECTURE: 전체 필드 테이블(이름, 타입, 역할) + 제어 필드가 셸과 테스트에서 잠긴다는 명시
- ACCEPTANCE_CRITERIA: 페이로드 계약의 수용 기준 요약 + ARCHITECTURE/PRODUCT_SPEC 교차 참조
- 중첩 필드 형태(evidence, summary_chunks, claim_coverage, approval 등)는 기존 문서 섹션 참조로 대체하여 중복 방지

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md` — 3개 파일, 89줄 추가 확인
- `git diff --check` — 공백 오류 없음
- `rg` 교차 확인: 3개 문서 모두 8개 제어 필드 언급 확인 (ACCEPTANCE_CRITERIA 10건, PRODUCT_SPEC 19건, ARCHITECTURE 18건)
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- `applied_preferences` 필드는 현재 직렬화되지만 셸에서 아직 소비되지 않을 수 있음 — 추후 셸 소비 경로 확인 필요
- 중첩 필드 형태 자체의 진실 동기화는 이 슬라이스 범위 밖 (기존 섹션에 이미 문서화됨)
