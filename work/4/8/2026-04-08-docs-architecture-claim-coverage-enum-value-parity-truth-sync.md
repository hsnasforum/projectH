# Docs ARCHITECTURE claim_coverage enum-value parity truth sync

## 변경 파일

- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ARCHITECTURE.md:170`의 `claim_coverage` field-shape 기술에서 `rendered_as`와 `progress_state`의 열거값이 누락되어 있었음. `docs/PRODUCT_SPEC.md:256`은 이미 `rendered_as` (`fact_card` / `uncertain` / `not_rendered`)와 `progress_state` (`improved` / `regressed` / `unchanged`)를 명시하고 있어 두 문서 간 parity gap이 있었음.

## 핵심 변경

### docs/ARCHITECTURE.md
- line 170: `rendered_as`에 `(fact_card / uncertain / not_rendered)`, `progress_state`에 `(improved / regressed / unchanged)` 열거값 추가

## 검증

- `rg -n "fact_card|not_rendered" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`: 두 문서 동일 field-shape 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- claim_coverage field-shape 문서화는 PRODUCT_SPEC과 ARCHITECTURE 간 완전 parity 달성.
