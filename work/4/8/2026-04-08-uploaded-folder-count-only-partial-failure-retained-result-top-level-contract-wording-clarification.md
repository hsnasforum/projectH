# uploaded-folder count-only partial-failure retained-result top-level contract wording clarification

## 변경 파일

- `README.md` (line 67)
- `docs/ACCEPTANCE_CRITERIA.md` (line 35)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- top-level contract는 generic `still returning results from successfully read files`로만 적혀 있었음
- scenario-level docs와 smoke는 이미 search-only/search-plus-summary 양쪽에서 readable-file result preview retention (ordered label, full-path tooltip, match badge, snippet)을 직접 고정
- top-level contract를 same retained-result preview truth에 맞게 정렬

## 핵심 변경

- README:67: `still returning results` → `retaining readable-file result preview (search-only and search-plus-summary both preserve preview cards with ordered label, full-path tooltip, match badge, and snippet)`
- ACCEPTANCE:35: `still returning results` → `retaining readable-file result preview with ordered label, full-path tooltip, match badge, and snippet in both search-only and search-plus-summary paths`

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 없음. docs wording만 변경, runtime/smoke 무변경.
