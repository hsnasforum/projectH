## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `PRODUCT_SPEC` wording clarification을 실제 current docs/current smoke truth에 맞게 반영했는지 확인해야 했습니다.
- 같은 document-search family에서 다음 Claude slice를 한 개로 고정하기 위해, latest spec sync가 닫힌 뒤 남은 source-of-truth gap도 함께 다시 확인해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-document-search-selected-copy-dual-preview-product-spec-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_SPEC.md:135`는 `/work` 주장대로 search-only `선택 경로 복사` button + `선택 경로를 복사했습니다` notice truth와 search-plus-summary dual-preview truth를 반영하고 있습니다.
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:47`, `docs/ACCEPTANCE_CRITERIA.md:36`
  - current smoke truth: `e2e/tests/web-smoke.spec.mjs:228-243`, `e2e/tests/web-smoke.spec.mjs:6599-6624`, `e2e/tests/web-smoke.spec.mjs:6643-6659`
- next slice는 같은 family의 남은 source-of-truth gap으로 `uploaded-folder partial-failure PRODUCT_SPEC exact-field wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:296`는 count-only partial-failure notice와 successful result retention만 generic하게 적고 있어, search-only path의 selected path/copy + hidden body + transcript hidden truth와 search-plus-summary path의 retained transcript preview exact-field truth를 직접 반영하지 못합니다.
  - 반면 current shipped contract는 이미 `README.md:67`, `docs/ACCEPTANCE_CRITERIA.md:35`, `README.md:189`, `README.md:191`, `docs/ACCEPTANCE_CRITERIA.md:1398`, `docs/ACCEPTANCE_CRITERIA.md:1400`에 직접 고정돼 있습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '133,137p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '292,299p'`
- `nl -ba README.md | sed -n '47,54p'`
- `nl -ba README.md | sed -n '188,191p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '33,36p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1397,1400p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6584,6660p'`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:296`의 uploaded-folder partial-failure 설명은 아직 current search-only/search-plus-summary exact-field truth를 fully 따라오지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` untracked notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
