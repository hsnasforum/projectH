# Docs PRODUCT_SPEC ARCHITECTURE web_search_history field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`web_search_history`가 두 문서에서 이름만 나열되어 있었고, 실제 직렬화 코드(`app/serializers.py:261-298`)가 반환하는 레코드 구조(`record_id`, `query`, `answer_mode`, `verification_label`, `source_roles`, `claim_coverage_summary`, `pages_preview` 등)가 기술되지 않아 메타데이터 contract가 under-documented 상태였음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md
- `web_search_history`: 최근 검색 기록 요약 리스트(최대 8건)의 필드 shape 기술
  - 기본 필드: `record_id`, `query`, `created_at`, `result_count`, `page_count`, `record_path`, `summary_head`
  - 분류 필드: `answer_mode` (`entity_card` / `latest_update` / `general`), `verification_label`, `source_roles`
  - 집계 필드: `claim_coverage_summary` (`strong` / `weak` / `missing` counts)
  - 미리보기: `pages_preview` (`title`, `url`, `excerpt`, `text_preview`, `char_count`)

## 검증

- `rg -n "web_search_history|pages_preview|claim_coverage_summary" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`: 두 문서 동일 field-shape 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `web_search_history` field-shape 문서화 PRODUCT_SPEC/ARCHITECTURE 간 완전 parity 달성.
