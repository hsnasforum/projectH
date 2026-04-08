# Docs ACCEPTANCE_CRITERIA session response save-trace field inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:92-101`의 response metadata inventory에서 shipped save-trace 필드(`selected_source_paths`, `saved_note_path`, `note_preview`, `save_content_source`, `source_message_id`)가 누락. PRODUCT_SPEC과 ARCHITECTURE, 그리고 `app/serializers.py:38-61`은 이미 해당 필드를 기술/직렬화하고 있어 불일치.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- response metadata inventory에 `selected_source_paths`, `saved_note_path`, `note_preview`, `save_content_source`, `source_message_id` 라인 추가

## 검증

- `rg -n "selected_source_paths|saved_note_path" docs/ACCEPTANCE_CRITERIA.md`: inventory에 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- response metadata inventory가 PRODUCT_SPEC/ARCHITECTURE와 대략적 parity 달성. 더 세밀한 field-shape (예: `save_content_source` 열거값)은 기존 Approval 섹션에서 이미 기술됨.
