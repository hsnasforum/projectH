# browser file picker PDF text-layer readable success smoke coverage

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (readable PDF fixture path 추가, ensureLongFixture에 readable PDF fixture 생성, 테스트 1개 추가)
- `README.md` (78번 smoke coverage bullet 추가)
- `docs/MILESTONES.md` (browser file picker readable PDF success smoke 추가)
- `docs/TASK_BACKLOG.md` (84번 task 추가)
- `docs/ACCEPTANCE_CRITERIA.md` (browser file picker readable PDF acceptance 1줄 추가)

## 사용 skill

- 없음

## 변경 이유

- shipped contract (README:66, ACCEPTANCE:33)는 PDF text-layer reading을 이미 약속
- browser file picker의 positive path (readable PDF → 정상 요약)를 smoke로 고정하는 coverage가 없었음
- 기존 `browser-file-input` helper와 `ensureLongFixture()` 재사용

## 핵심 변경

- pypdf로 생성한 readable text-layer PDF fixture (base64 인라인, 686 bytes, "PDF text-layer test: local-first approval-based document assistant" 텍스트 포함)
- readable PDF file picker → 정상 요약 smoke 1개 (OCR 안내 미노출, context box/quick meta에 PDF 파일명 표시)
- README/MILESTONES/TASK_BACKLOG/ACCEPTANCE에 coverage bullet truth-sync

## 검증

- `npx playwright test -g "readable text-layer PDF"` → 1 passed (7.1s)
- `git diff --check` → clean

## 남은 리스크

- 없음. readable PDF positive path의 browser-level success를 직접 고정.
