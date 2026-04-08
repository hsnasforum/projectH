# Docs PRODUCT_SPEC focus-slot explanation terminology normalization

## 변경 파일

- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음

## 변경 이유

`docs/PRODUCT_SPEC.md:291`이 focus-slot 상태를 `improved, regressed, stayed single-source, or remains unresolved`로 기술하고 있었으나, 같은 파일 내 line 106과 310은 이미 `reinforced / regressed / still single-source / still unresolved`로 정규화되어 파일 내 불일치가 있었음.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- line 291: `improved, regressed, stayed single-source, or remains unresolved` → `reinforced, regressed, is still single-source, or is still unresolved`

## 검증

- `rg -n "improved, regressed, stayed single-source" docs/PRODUCT_SPEC.md`: 0건 확인
- 3개 파일(PRODUCT_SPEC, ACCEPTANCE_CRITERIA, README) 전체 4-state 일관성 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- claim-coverage focus-slot 용어 정규화는 전체 문서 계층에서 완료됨.
