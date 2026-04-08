# Docs PRODUCT_SPEC ARCHITECTURE permissions web_search_label value truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`permissions.web_search_label`의 실제 값 세트(`차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`)가 문서에 기술되지 않았음. `app/web.py:193-199`에서 고정된 라벨 값이 코드에 존재하나 docs에서 누락 상태였음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md
- `permissions` field-shape에 `web_search_label` 값 세트 추가

## 검증

- 두 문서 동일 라벨 값 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음.
