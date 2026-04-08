# Docs ACCEPTANCE_CRITERIA session permissions enum-and-label value-set truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:88`이 `permissions` shape만 기술하고 구체적 열거값을 누락. `docs/PRODUCT_SPEC.md:219`과 `docs/ARCHITECTURE.md:143`은 이미 열거값까지 기술되어 있어 authoritative docs 간 상세 수준 불일치.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- line 88: `{web_search, web_search_label}` 뒤에 `web_search` 열거값(`disabled` / `approval` / `enabled`)과 `web_search_label` 값(`차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`) 추가

## 검증

- 3개 authoritative 문서(PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA) 동일 permissions 기술 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음. permissions 열거값 문서화가 authoritative docs 전체에서 완전 parity 달성.
