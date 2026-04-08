# PRODUCT_SPEC Current Outputs claim-coverage wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (Current Outputs section, line 106)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- Current Outputs section은 search preview/source-type/origin까지는 닫혔지만 claim coverage/verification state surface가 빠져 있었음
- README:69, ACCEPTANCE:28, PRODUCT_SPEC:312는 이미 이 surface를 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), actionable hints, color-coded fact-strength summary bar 추가

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
