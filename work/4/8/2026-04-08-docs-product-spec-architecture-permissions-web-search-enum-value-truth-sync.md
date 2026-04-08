# Docs PRODUCT_SPEC ARCHITECTURE permissions web_search enum-value truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

이전 슬라이스에서 `permissions.web_search` 열거값을 `enabled` / `disabled` / `ask`로 기술했으나, 실제 shipped enum(`core/contracts.py:149-152`)은 `disabled` / `approval` / `enabled`임. `ask`는 존재하지 않는 값이었음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md
- `permissions.web_search` 열거값: `enabled` / `disabled` / `ask` → `disabled` / `approval` / `enabled`

## 검증

- 두 문서 동일 열거값 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음. `permissions.web_search` 열거값이 코드와 일치함.
