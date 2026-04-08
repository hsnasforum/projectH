# PRODUCT_SPEC Current Outputs response-feedback wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (line 102, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `response feedback records`는 generic wording이었음
- README:56, ACCEPTANCE:39/214, PRODUCT_SPEC:48/384는 이미 feedback label + optional reason과 `response_feedback_recorded` audit linkage를 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- `response feedback records` → `response feedback records with label + optional reason, linked via response_feedback_recorded audit event`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
