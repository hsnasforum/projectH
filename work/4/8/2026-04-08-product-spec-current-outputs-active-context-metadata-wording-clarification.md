# PRODUCT_SPEC Current Outputs active-context metadata wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (line 99, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `active context metadata`는 generic wording이었음
- PRODUCT_SPEC:46/220/434, README:59, ACCEPTANCE:88-91/189는 이미 `active_context` session field, follow-up answer surface, correction-submit `summary_hint` update를 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- `active context metadata` → `active context metadata (active_context session field for follow-up answers, updated by correction-submit summary_hint)`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
