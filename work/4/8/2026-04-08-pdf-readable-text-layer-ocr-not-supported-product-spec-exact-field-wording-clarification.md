# PDF readable text-layer + OCR-not-supported PRODUCT_SPEC exact-field wording clarification

## 변경 파일

- `docs/PRODUCT_SPEC.md` (lines 294-295)

## 사용 skill

- 없음 (docs wording clarification only)

## 변경 이유

- `PRODUCT_SPEC.md:294`는 `read through the local file-reading path`로만 적혀 있어 visible summary body, `문서 요약` label, filename truth 미반영
- `PRODUCT_SPEC.md:295`는 `explicit OCR-not-supported guidance`로만 적혀 있어 exact strings 미반영
- README:66, ACCEPTANCE:33-34, scenario-level docs, smoke는 이미 양쪽 exact-field truth를 직접 고정
- PRODUCT_SPEC를 same truth에 맞게 정렬

## 핵심 변경

- line 294: `read through the local file-reading path` → `read and produce a visible summary body with 문서 요약 label and PDF filename in context box/quick meta/transcript meta`
- line 295: `explicit OCR-not-supported guidance` → `visible OCR-not-supported guidance with exact strings 요약할 수 없습니다, OCR, 이미지형 PDF, 다음 단계:`

## 검증

- `git diff --check -- docs/PRODUCT_SPEC.md` → clean

## 남은 리스크

- 없음. PRODUCT_SPEC wording만 변경, runtime/smoke/README/ACCEPTANCE 무변경.
