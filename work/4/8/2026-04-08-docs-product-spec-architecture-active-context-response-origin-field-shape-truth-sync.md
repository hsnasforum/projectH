# Docs PRODUCT_SPEC ARCHITECTURE active_context response_origin field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`active_context`와 `response_origin`이 두 문서에서 이름만 나열되어 있었고, 실제 직렬화 코드(`app/serializers.py:318-345`)가 반환하는 필드 shape이 기술되지 않아 세션/메시지 메타데이터 contract가 under-documented 상태였음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md
- `active_context`: `{kind, label, source_paths, summary_hint, suggested_prompts, record_path, claim_coverage_progress_summary}` shape 기술
- `response_origin`: `{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}` shape 기술

## 검증

- `rg -n "active_context.*kind|response_origin.*provider" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md`: 두 문서 동일 shape 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- PRODUCT_SPEC의 approval/snapshot 섹션에서 `response_origin`을 재참조하는 곳(line 414, 479)은 이번 슬라이스에서 inline annotation 미추가. 주요 shape은 message-level에서 이미 기술됨.
