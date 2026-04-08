# PRODUCT_SPEC Current Outputs evidence/source + summary-range wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 97-98, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `evidence items`와 `summary chunk metadata`는 generic wording이었음
- README:50/52, ACCEPTANCE:24-25, PRODUCT_SPEC:282/284는 이미 evidence/source panel with trust labels와 summary span/applied-range panel을 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- `evidence items` → `evidence/source panel with source-role trust labels`
- `summary chunk metadata` → `summary span/applied-range panel showing which chunks were used`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
