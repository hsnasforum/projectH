# Docs PRODUCT_SPEC ARCHITECTURE pending_approvals permissions field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`pending_approvals`와 `permissions`가 두 문서에서 이름만 나열되어 있었고, 실제 직렬화 코드가 반환하는 field shape이 기술되지 않았음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md
- `pending_approvals`: serialized approval 객체 리스트, Approval 섹션 참조로 기술
- `permissions`: `{web_search, web_search_label}`, `web_search`는 `enabled` / `disabled` / `ask` 열거값

## 검증

- 두 문서 동일 shape 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 세션 스키마의 주요 필드가 모두 field-shape 기술 완료됨 (`response_origin`, `active_context`, `claim_coverage`, `web_search_history`, `evidence`, `summary_chunks`, `pending_approvals`, `permissions`).
