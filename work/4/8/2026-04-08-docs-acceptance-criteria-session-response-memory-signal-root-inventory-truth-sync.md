# Docs ACCEPTANCE_CRITERIA session response memory-signal root inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

response metadata inventory에서 shipped message-level memory-signal root 필드(`session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, `session_local_candidate`, `candidate_review_record`)가 누락. PRODUCT_SPEC/ARCHITECTURE와 `app/serializers.py:132-210`은 이미 기술/직렬화.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
- response metadata inventory에 memory-signal roots 2라인 추가:
  - `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal` — optional per-message memory-signal roots
  - `session_local_candidate`, `candidate_review_record` — optional per-message candidate roots

## 검증

- inventory 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- response metadata inventory가 PRODUCT_SPEC/ARCHITECTURE의 message-level 필드 목록과 parity 달성.
