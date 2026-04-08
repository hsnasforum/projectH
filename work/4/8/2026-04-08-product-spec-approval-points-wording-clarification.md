# PRODUCT_SPEC Approval Points wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 109-111, Approval Points section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- 3줄 모두 generic wording이었음
- README:48-49/68/199, ACCEPTANCE:20-22/37/67-70, PRODUCT_SPEC:183-200/307-313는 이미 approval object/overwrite warning, reissue approval, permission-gated web investigation을 직접 고정
- Approval Points summary를 same truth에 맞게 정렬

## 핵심 변경

- `note save approval` → approval object with request-time snapshot, requested save path, overwrite warning
- `save-path reissue approval` → new approval object issued when save path is changed after initial approval
- `web-search permission` → permission gate for permission-gated secondary-mode web investigation (enabled/disabled/ask per session)

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
