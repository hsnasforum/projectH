# PRODUCT_SPEC Current Outputs summary-text wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (line 96, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `summary text`는 generic wording이었음
- README:65-67, ACCEPTANCE:29-31/33/36, PRODUCT_SPEC:129-145/298-300는 이미 visible final Korean summary body, search-plus-summary visible body, source-anchored faithfulness rule을 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- `summary text` → `summary text (visible final Korean summary body for local file/uploaded document/readable PDF, visible summary body for selected search results in search-plus-summary path, source-anchored faithfulness rule)`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
