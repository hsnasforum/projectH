# Docs PRODUCT_SPEC ARCHITECTURE original_response_snapshot response_origin nested field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`original_response_snapshot` 내부의 `response_origin`이 두 문서에서 이름만 나열되어 있었고, 실제 직렬화 코드가 message-level과 동일한 `response_origin` shape을 중첩하는 것이 기술되지 않았음.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- line 414 (snapshot keeps): `response_origin` — same shape as message-level `response_origin` 전체 필드 목록 추가
- line 479 (Original Response Snapshot 섹션): `response_origin` — same shape 참조 추가

### docs/ARCHITECTURE.md
- line 299: `original_response_snapshot.response_origin` — same shape 참조 및 전체 필드 목록 추가

## 검증

- `rg -n "response_origin" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`: 5곳 모두 shape 기술 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `original_response_snapshot`의 나머지 필드(`summary_chunks_snapshot`, `evidence_snapshot`)는 이름만 나열된 상태로 이번 슬라이스 범위 밖.
