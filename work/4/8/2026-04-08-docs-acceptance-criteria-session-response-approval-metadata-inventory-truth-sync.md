# Docs ACCEPTANCE_CRITERIA session response approval metadata inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

response metadata inventory에서 response-level `approval` payload가 누락. `app/serializers.py:50`과 `app/serializers.py:300-315`는 이미 `approval`을 직렬화하고 있고, PRODUCT_SPEC/ARCHITECTURE도 이미 기술.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- response metadata inventory에 `approval` — serialized approval object (Approval 섹션 참조) 추가

## 검증

- `approval` entry 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- response metadata inventory가 PRODUCT_SPEC/ARCHITECTURE와 대략적 parity 달성.
