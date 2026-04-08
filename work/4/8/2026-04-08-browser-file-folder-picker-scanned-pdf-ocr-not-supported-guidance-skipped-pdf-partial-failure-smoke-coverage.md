# browser file/folder picker scanned-PDF OCR-not-supported guidance + skipped-PDF partial-failure smoke coverage

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (fixture paths 추가, ensureLongFixture에 scanned PDF fixture 생성, 테스트 2개 추가)
- `README.md` (76-77번 smoke coverage bullet 추가)
- `docs/MILESTONES.md` (browser file/folder picker PDF smoke 2개 추가)
- `docs/TASK_BACKLOG.md` (82-83번 task 추가)
- `docs/ACCEPTANCE_CRITERIA.md` (browser file/folder picker PDF acceptance 2줄 추가)

## 사용 skill

- 없음

## 변경 이유

- shipped contract (README:66-67, ACCEPTANCE:33-35)는 PDF text-layer reading, scanned PDF OCR-not-supported guidance, skipped-scanned-PDF partial-failure notice를 이미 약속
- service/unit coverage (test_smoke.py:7518-7593, test_web_app.py:6056-6088)는 존재하지만 browser-level e2e smoke가 없었음
- 기존 browser file/folder picker helper를 재사용하여 두 가지 browser-visible PDF path를 Playwright smoke로 직접 고정

## 핵심 변경

- minimal valid PDF fixture (빈 페이지 1개, PyPDF2 parseable but empty text) 생성
- scanned-PDF file picker → OCR guidance 표시 smoke 1개 (`요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`)
- mixed folder (scanned PDF + readable txt) search-only → partial-failure notice smoke 1개 (`스캔본 또는 이미지형 PDF`, `건너뛰었습니다`)
- README/MILESTONES/TASK_BACKLOG/ACCEPTANCE에 coverage bullet truth-sync

## 검증

- `npx playwright test -g "scanned/image-only PDF"` → 1 passed (6.8s)
- `npx playwright test -g "count-only partial-failure notice"` → 1 passed (6.8s)
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- stub PDF의 `incorrect startxref pointer(3)` 경고는 PyPDF2 내부 로그일 뿐 기능에 영향 없음
- search-only mode에서 partial-failure notice는 hidden response-text body에 포함됨 — 별도 UI surface가 필요하면 추후 product decision
