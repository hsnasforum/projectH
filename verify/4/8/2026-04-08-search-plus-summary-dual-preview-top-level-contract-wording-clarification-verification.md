## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only wording clarification을 실제 current docs/current smoke truth에 맞게 반영했는지 확인해야 했습니다.
- 같은 search UI contract family에서 다음 Claude slice를 한 개로 고정하기 위해, top-level docs가 닫힌 뒤 남은 source-of-truth gap도 함께 다시 확인해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-search-plus-summary-dual-preview-top-level-contract-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `README.md:47`과 `docs/ACCEPTANCE_CRITERIA.md:36`은 search-plus-summary path에서 visible summary body와 preview cards가 response detail + transcript 양쪽에 함께 유지된다는 top-level contract를 반영하고 있습니다.
- supporting smoke truth도 일치했습니다.
  - smoke-coverage docs: `README.md:115`, `docs/ACCEPTANCE_CRITERIA.md:1324`
  - browser smoke: `e2e/tests/web-smoke.spec.mjs:228-243`, `e2e/tests/web-smoke.spec.mjs:6643-6659`
- next slice는 같은 family의 남은 source-of-truth gap으로 `document-search selected-copy + dual-preview PRODUCT_SPEC wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:135`는 structured preview/search-only hidden body까지만 적고 있어 `selected-copy` notice truth와 search-plus-summary dual-preview truth가 빠져 있습니다.
  - 반면 current shipped contract는 이미 `README.md:47`, `docs/ACCEPTANCE_CRITERIA.md:36`에 직접 고정돼 있습니다.

## 검증
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba README.md | sed -n '47,51p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '27,36p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '132,141p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '214,236p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6636,6659p'`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md`의 document search section은 아직 latest top-level search contract를 fully 따라오지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` untracked notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
