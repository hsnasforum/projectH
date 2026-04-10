## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `PRODUCT_SPEC` wording clarification을 실제 current docs/current smoke truth에 맞게 반영했는지 확인해야 했습니다.
- 같은 PDF/uploaded-folder family에서 다음 Claude slice를 한 개로 고정하기 위해, latest spec sync가 닫힌 뒤 남은 source-of-truth gap도 함께 다시 확인해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-uploaded-folder-partial-failure-product-spec-exact-field-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_SPEC.md:296`은 `/work` 주장대로 uploaded-folder partial-failure contract에 readable-file result preview exact fields와 search-only/search-plus-summary path별 UI truth를 반영하고 있습니다.
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:67`, `docs/ACCEPTANCE_CRITERIA.md:35`
  - scenario-level docs: `README.md:189`, `README.md:191`, `docs/ACCEPTANCE_CRITERIA.md:1398`, `docs/ACCEPTANCE_CRITERIA.md:1400`
  - current smoke truth: `e2e/tests/web-smoke.spec.mjs:6584-6660`
- next slice는 같은 family의 남은 source-of-truth gap으로 `PDF readable text-layer + OCR-not-supported PRODUCT_SPEC exact-field wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:294-295`는 `text-layer PDFs are read through the local file-reading path`, `scanned/image-only PDFs return explicit OCR-not-supported guidance` 수준의 generic wording에 머물러 있습니다.
  - 반면 current shipped contract는 이미 `README.md:66`, `docs/ACCEPTANCE_CRITERIA.md:33-34`, `README.md:188`, `README.md:190`, `docs/ACCEPTANCE_CRITERIA.md:1397`, `docs/ACCEPTANCE_CRITERIA.md:1399`, `e2e/tests/web-smoke.spec.mjs:6566-6571`, `e2e/tests/web-smoke.spec.mjs:6665-6678`에 exact-field truth를 직접 고정하고 있습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '292,299p'`
- `nl -ba README.md | sed -n '66,67p'`
- `nl -ba README.md | sed -n '188,190p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '33,35p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1397,1399p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6566,6571p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6665,6678p'`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:294-295`의 PDF 설명은 아직 readable text-layer success exact fields와 scanned/image-only OCR guidance exact fields를 fully 따라오지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` untracked notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
