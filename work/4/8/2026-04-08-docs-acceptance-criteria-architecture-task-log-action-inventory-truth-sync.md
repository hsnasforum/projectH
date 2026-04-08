# Docs ACCEPTANCE_CRITERIA ARCHITECTURE task-log action inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

task-log action 목록이 shipped 코드와 불일치. ARCHITECTURE는 일부 action 누락(`request_cancelled`, `correction_submitted`, `content_reason_note_recorded`, `candidate_review_recorded`), ACCEPTANCE_CRITERIA는 generic 카테고리 문장만 사용하고 `candidate_confirmation_recorded` 외 구체적 action 미나열.

## 핵심 변경

### docs/ARCHITECTURE.md
- task-log action 목록에 `request_cancelled`, `correction_submitted`, `content_reason_note_recorded`, `candidate_review_recorded` 추가
- 기존 action 순서 정리 (request → approval → write → feedback → correction → verdict → candidate)

### docs/ACCEPTANCE_CRITERIA.md
- generic 카테고리 문장을 구체적 shipped action 15개 목록으로 교체

## 검증

- 두 문서 모두 동일 15개 action 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 코드에는 내부 처리용 action(`agent_response`, `read_file`, `summarize_file`, `web_search_retried` 등)도 있으나, 이번 목록은 user-facing contract 수준의 핵심 action만 포함. 내부 action은 별도 문서화 범위.
