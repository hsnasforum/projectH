# Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA session permissions field-shape summary truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/PRODUCT_SPEC.md:114`의 요약에서 `permissions`를 `including web-search permission state`로 기술, `docs/ACCEPTANCE_CRITERIA.md:88`에서는 이름만 나열. 이미 같은 문서의 상세 섹션에 `{web_search, web_search_label}` shape이 기술되어 있어 요약 계층과 불일치.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- line 114: `permissions (including web-search permission state)` → `permissions ({web_search, web_search_label})`

### docs/ACCEPTANCE_CRITERIA.md
- line 88: `permissions` → `permissions — {web_search, web_search_label}`

## 검증

- 두 문서 요약 계층과 상세 계층 간 parity 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음. permissions 문서화가 authoritative docs 전체에서 일관됨.
