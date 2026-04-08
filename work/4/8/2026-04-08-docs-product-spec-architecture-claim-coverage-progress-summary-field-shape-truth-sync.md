# Docs PRODUCT_SPEC ARCHITECTURE claim_coverage_progress_summary field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`claim_coverage`와 `claim_coverage_progress_summary`가 문서에서 이름만 나열되어 있었고, 실제 구현에서 직렬화되는 슬롯-레벨 필드(`previous_status`, `previous_status_label`, `progress_state`, `progress_label`, `is_focus_slot`, `rendered_as` 등)의 shape이 기술되지 않아 메타데이터 contract가 under-documented 상태였음.

## 핵심 변경

### docs/PRODUCT_SPEC.md
- `claim_coverage`: 슬롯 객체의 기본 필드(`slot`, `status`, `status_label`, `value`, `support_count`, `candidate_count`, `source_role`, `rendered_as`)와 재조사 시 추가 필드(`previous_status`, `previous_status_label`, `progress_state`, `progress_label`, `is_focus_slot`) 기술
- `claim_coverage_progress_summary`: focus-slot 재조사 결과 요약 한국어 문장, 첫 조사 시 빈 문자열

### docs/ARCHITECTURE.md
- 동일 field-shape 기술 추가

## 검증

- `rg -n "claim_coverage_progress_summary|previous_status|progress_state|is_focus_slot" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`: 관련 필드 모두 문서화 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `rendered_as` 열거값(`fact_card` / `uncertain` / `not_rendered`)은 PRODUCT_SPEC에만 기술, ARCHITECTURE에는 열거값 미포함 (간결성 유지 의도).
