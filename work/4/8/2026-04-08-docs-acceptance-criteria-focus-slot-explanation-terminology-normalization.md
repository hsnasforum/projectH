# Docs ACCEPTANCE_CRITERIA focus-slot explanation terminology normalization

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:41`이 `remains single-source`를 사용하고 있었으나, 같은 파일 line 1337과 다른 모든 문서는 이미 `still single-source`로 정규화되어 있어 용어 불일치가 있었음.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- line 41: `remains single-source` → `is still single-source`

## 검증

- `rg -n "remains single-source" docs/ACCEPTANCE_CRITERIA.md`: 0건 확인
- 3개 핵심 문서(ACCEPTANCE_CRITERIA, PRODUCT_SPEC, README) 전체 4-state 용어 일관성 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- focus-slot explanation 용어 정규화는 전체 문서 계층에서 완료됨.
