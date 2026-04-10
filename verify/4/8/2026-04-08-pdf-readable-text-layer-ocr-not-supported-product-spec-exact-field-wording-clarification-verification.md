## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `PRODUCT_SPEC` PDF wording clarification을 실제 current docs/current smoke truth에 맞게 반영했는지 확인해야 했습니다.
- 같은 `PRODUCT_SPEC` truth-sync family에서 다음 Claude slice를 한 개로 고정하기 위해, latest PDF sync가 닫힌 뒤 남은 source-of-truth gap도 함께 다시 확인해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-pdf-readable-text-layer-ocr-not-supported-product-spec-exact-field-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_SPEC.md:294-295`는 `/work` 주장대로 readable text-layer PDF success truth와 scanned/image-only PDF OCR guidance exact-field truth를 반영하고 있습니다.
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:66`, `docs/ACCEPTANCE_CRITERIA.md:33-34`
  - scenario-level docs: `README.md:188`, `README.md:190`, `docs/ACCEPTANCE_CRITERIA.md:1397`, `docs/ACCEPTANCE_CRITERIA.md:1399`
  - current smoke truth: `e2e/tests/web-smoke.spec.mjs:6566-6571`, `e2e/tests/web-smoke.spec.mjs:6665-6678`
- next slice는 같은 `PRODUCT_SPEC` truth-sync family의 남은 source-of-truth gap으로 `PRODUCT_SPEC Current Outputs search preview/source-type/origin wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:95-102`의 `Current Outputs` summary는 `summary text`, `evidence items`, `summary chunk metadata` 등 generic list만 적고 있어, current shipped response surfaces인 search result preview panel, summary source-type label, response origin badge를 top-level outputs summary에 반영하지 못합니다.
  - 반면 current shipped contract는 이미 `README.md:47`, `README.md:51`, `README.md:53`, `docs/ACCEPTANCE_CRITERIA.md:26-27`, `docs/ACCEPTANCE_CRITERIA.md:36`, `docs/PRODUCT_SPEC.md:135`, `docs/PRODUCT_SPEC.md:279`, `docs/PRODUCT_SPEC.md:281`에 직접 고정돼 있습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '95,102p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '294,296p'`
- `nl -ba README.md | sed -n '46,54p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '24,38p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6566,6571p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6665,6678p'`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:95-102`의 `Current Outputs` summary는 아직 current shipped response surfaces를 fully 요약하지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` untracked notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
