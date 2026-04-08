# PRODUCT_SPEC Current Outputs approval preview + saved-note-path wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 100-101, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `approval preview`와 `saved summary note path when approved`는 generic wording이었음
- README:48-49/54/60, ACCEPTANCE:20-22/69/97, PRODUCT_SPEC:185-200/272/274/286는 이미 approval snapshot/requested path/overwrite warning과 saved_note_path/response detail linkage를 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- `approval preview` → `approval preview with request-time snapshot, requested save path, and overwrite warning when target already exists`
- `saved summary note path when approved` → `saved summary note path (saved_note_path) returned after approval, linked in response detail for user confirmation`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
