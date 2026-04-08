# uploaded-folder partial-failure PRODUCT_SPEC exact-field wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (line 296)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `PRODUCT_SPEC.md:296`는 generic `still returning results from successfully read files`로만 적혀 있었음
- README:67, ACCEPTANCE:35, scenario-level docs, smoke는 이미 search-only path의 selected path/copy + hidden body + transcript hidden과 search-plus-summary path의 retained preview + dual-preview truth를 직접 고정
- PRODUCT_SPEC를 same exact-field truth에 맞게 정렬

## 핵심 변경

- generic `still returning results` → `retaining readable-file result preview with ordered label, full-path tooltip, match badge, and snippet` + search-only path의 `selected path/copy, hidden response body, transcript preview, transcript body hidden` + search-plus-summary path의 `visible summary body alongside preview cards in both response detail and transcript`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
