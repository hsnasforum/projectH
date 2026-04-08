# Docs PRODUCT_SPEC Current Permission Fields web_search_label parity truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음

## 변경 이유

`docs/PRODUCT_SPEC.md`의 `Current Permission Fields` 서브섹션이 `permissions.web_search`만 나열하고 `permissions.web_search_label`을 누락하고 있었음. 실제 직렬화 코드(`app/serializers.py:964-970`)는 항상 두 필드를 함께 반환함.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- `Current Permission Fields`에 `permissions.web_search_label` 추가: `차단 · 읽기 전용 검색` / `승인 필요 · 읽기 전용 검색` / `허용 · 읽기 전용 검색`

## 검증

- line 219 (top-level shape)과 line 237-245 (Current Permission Fields) 간 parity 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음. permission 필드 문서화 완료.
