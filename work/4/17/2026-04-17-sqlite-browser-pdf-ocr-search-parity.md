# sqlite-browser-pdf-ocr-search-parity

## 변경 파일

- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `using-superpowers`

## 변경 이유

이전 `/work`에서 sqlite browser gate가 recurrence aggregate 5 + save/correction/verdict 4 + core document productivity loop 4건까지 총 13건으로 확장됐습니다. 최신 `/verify`는 같은 document-ingestion family의 남은 current-risk가 PDF/OCR document workflow 네 건(`scanned/image-only PDF OCR 미지원 안내`, 혼합 폴더 `count-only partial-failure notice`, 혼합 폴더 `검색+요약 partial-failure notice + readable preview`, `readable text-layer PDF 정상 요약`)이라고 판단했습니다. 이 네 시나리오는 JSON-default Playwright path에서 이미 shipped된 사용자 가시 계약이고, sqlite backend에서도 동일하게 동작한다는 증거가 그동안 없었습니다. 이번 라운드는 기존 `web-smoke.spec.mjs` 네 시나리오를 `playwright.sqlite.config.mjs`로 재실행해서 실측 parity gate를 확보하고 sqlite browser gate inventory 문서를 17건 기준으로 맞춥니다. 제품 계약·OCR 정책·저장 semantics는 손대지 않습니다.

## 핵심 변경

1. **sqlite browser gate 실측 통과 확인** (기존 시나리오 재사용, 코드·설정 변경 없음):
   - `브라우저 파일 선택으로 scanned/image-only PDF를 선택하면 OCR 미지원 안내가 표시됩니다` — sqlite backend에서도 OCR-not-supported guidance(`요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`)가 동일하게 노출됨을 확인.
   - `브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색하면 count-only partial-failure notice가 표시됩니다` — 혼합 폴더 search-only의 count-only partial-failure notice + readable preview + selected-path copy가 sqlite backend에서 동일하게 동작함을 확인.
   - `브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색+요약하면 partial-failure notice와 함께 readable file preview가 유지됩니다` — 혼합 폴더 search-plus-summary의 partial-failure notice + readable preview 유지 계약이 sqlite backend에서도 유지됨을 확인.
   - `브라우저 파일 선택으로 readable text-layer PDF를 선택하면 정상 요약이 됩니다` — readable text-layer PDF가 OCR guidance 미노출로 정상 요약 본문과 `문서 요약` metadata를 노출함을 sqlite backend에서 확인.

2. **docs sync**: sqlite browser gate inventory 문서 4개에 PDF/OCR document workflow 4건을 추가해 총 17건으로 맞춤.
   - `README.md` `SQLite Browser Smoke (opt-in backend parity gate)` 섹션의 시나리오 목록을 17건으로 확장.
   - `docs/ACCEPTANCE_CRITERIA.md` sqlite browser smoke bullet에 PDF/OCR document workflow 4건 추가.
   - `docs/MILESTONES.md` SQLite browser smoke baseline milestone 문구에 PDF/OCR document workflow 4건 포함으로 확장.
   - `docs/TASK_BACKLOG.md` `Partial / Opt-In` SQLite backend 항목의 browser-level parity gate 설명을 같은 17건으로 확장.

3. **제품/서비스/설정 무변경**: `e2e/playwright.sqlite.config.mjs`, `e2e/tests/web-smoke.spec.mjs`, app/serializer/store/frontend 모두 손대지 않음. sqlite 전용 PDF/OCR 플로우 없음.

## 검증

```
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 파일 선택으로 scanned/image-only PDF를 선택하면 OCR 미지원 안내가 표시됩니다" --reporter=line  # 1 passed (4.0s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색하면 count-only partial-failure notice가 표시됩니다" --reporter=line  # 1 passed (4.8s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 폴더 선택으로 scanned PDF + readable file이 섞인 폴더를 검색+요약하면 partial-failure notice와 함께 readable file preview가 유지됩니다" --reporter=line  # 1 passed (4.1s)
cd e2e && npx playwright test -c playwright.sqlite.config.mjs -g "브라우저 파일 선택으로 readable text-layer PDF를 선택하면 정상 요약이 됩니다" --reporter=line  # 1 passed (4.3s)
git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md  # clean
```

- `make e2e-test`, full sqlite browser suite, Python unit suite는 이번 라운드에 실행하지 않았습니다. 이번 `/work`는 opt-in sqlite browser gate inventory 4건을 실측으로 확정한 Playwright-only smoke tightening bundle이었고, 최신 handoff가 요구한 focused rerun 4건을 모두 확인했습니다. 기존 13건 sqlite browser gate는 이전 라운드에서 회귀 없음이 확인됐고 이번 슬라이스는 설정·코드·테스트 본문 어디에도 변경을 만들지 않았으므로 full sqlite browser suite는 이번 범위 대비 과한 검증이었습니다.
- Playwright 출력에 `[WebServer] incorrect startxref pointer(3)` 경고가 scanned PDF fixture 기반 세 시나리오에서 반복적으로 나타났습니다. 이 경고는 base64 scanned-PDF fixture의 xref 포인터 경고이며 JSON-default smoke와 동일하게 서버·프론트엔드가 정상적으로 스캔본으로 분류하도록 되어 있으므로 이번 슬라이스 범위에서 별도 조치가 필요하지 않습니다.

## 남은 리스크

- sqlite browser gate는 이번 라운드로 recurrence aggregate 5건 + document-loop save/correction/verdict 4건 + core document productivity loop 4건 + PDF/OCR document workflow 4건까지 총 17건으로 확장됐습니다. 권한 게이트, history-card reload, 웹 조사 계열은 이번 슬라이스 scope 밖이라 아직 sqlite backend로 확인되지 않았습니다.
- OCR 미지원 정책은 이번 라운드에서도 shipped 계약 그대로이며, sqlite 경로에서도 안내 문구만 확인했습니다. OCR 지원 확장은 여전히 제품 scope 밖입니다.
- `LOCAL_AI_NOTES_DIR`을 repo 기본값으로 공유하는 sqlite config 정책은 지난 라운드 그대로이며, sqlite/JSON smoke config를 병렬 실행하는 파이프라인이 생기면 격리 전략을 다시 봐야 합니다.
- scanned PDF fixture가 뿌리는 `incorrect startxref pointer` 경고는 오래된 fixture 포맷에서 유래하며, 테스트가 계속 pass하는 한 production PDF 처리 경로의 이슈는 아닙니다. 필요 시 fixture 재생성으로 조용히 덮을 수 있으나 이번 슬라이스 범위는 아닙니다.
