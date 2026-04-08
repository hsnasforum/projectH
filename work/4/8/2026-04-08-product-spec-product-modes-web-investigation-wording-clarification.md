# PRODUCT_SPEC Product Modes Web Investigation wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 151-155, Product Modes > Web Investigation section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 4줄 모두 generic wording이었음
- README:68-69, ACCEPTANCE:37/53, PRODUCT_SPEC:307-313/281-288는 이미 permission states, history badges, answer-mode distinction, claim coverage, document-first guardrail을 직접 고정
- Product Modes summary를 same truth에 맞게 정렬

## 핵심 변경

- permission: enabled/disabled/ask per session 명시
- local JSON: in-session reload + history-card badges 명시
- entity-card/latest-update: separate verification labels, source-role, claim coverage panel, strong-badge downgrade 명시
- secondary mode: document-first guardrail 명시

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
