# PRODUCT_SPEC Stored Evidence, Logs, And Feedback wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 114-119, Stored Evidence, Logs, And Feedback section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 6줄 모두 generic wording이었음
- README:56-64/68, ACCEPTANCE:81-99, PRODUCT_SPEC:224-277는 이미 session fields, response metadata surfaces, task log events, web-search history badges를 직접 고정
- Stored Evidence summary를 same truth에 맞게 정렬

## 핵심 변경

- session JSON: `active_context` follow-up context, `permissions` web-search state 명시
- response metadata: evidence/source trust labels, summary chunks applied-range, response origin badges, claim coverage status tags, feedback label+reason, grounded-brief trace fields 명시
- task log: `additive` 수식어, `response_feedback_recorded` event 명시
- web-search history: answer-mode/verification/source-role badges 명시

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
