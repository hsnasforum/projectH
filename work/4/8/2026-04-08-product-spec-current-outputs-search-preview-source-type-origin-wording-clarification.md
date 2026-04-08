# PRODUCT_SPEC Current Outputs search preview/source-type/origin wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 95-105, Current Outputs section)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- Current Outputs section은 generic `summary text`, `evidence items` 등만 적고 있어, current shipped response surfaces인 search result preview panel, summary source-type label, response origin badge를 반영하지 않았음
- README:47/51/53, ACCEPTANCE:26-27/36, PRODUCT_SPEC:135/279/281는 이미 이러한 surfaces를 직접 고정
- Current Outputs summary를 same truth에 맞게 정렬

## 핵심 변경

- structured search result preview panel (ordered label, full-path tooltip, match type badge, content snippet) 추가
- summary source-type label (`문서 요약`, `선택 결과 요약`) in quick meta and transcript meta 추가
- response origin badge (`WEB`, answer-mode badge, verification label, source-role trust badges) 추가

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
