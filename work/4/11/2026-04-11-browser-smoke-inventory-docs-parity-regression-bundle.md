# browser smoke inventory docs parity regression bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/11/2026-04-11-browser-smoke-inventory-docs-parity-regression-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 라운드들에서 browser smoke inventory 관련 docs drift 문제가 같은 날 여러 번 반복되었습니다. 처음에는 시나리오 수를 `123 → 125` 로 올려야 했고, 그 다음에는 `docs/NEXT_STEPS.md:23` 이 `docs/ACCEPTANCE_CRITERIA.md:1351` 이라는 깨지기 쉬운 라인 앵커를 여전히 가리키고 있는 문제가 `/verify` 에서 뒤늦게 드러났습니다. 이 두 번의 docs-only 라운드를 돌려 현재 docs 가족은 true 하게 닫혀 있지만, 남은 current-risk 는 "다음 같은 종류의 drift 가 또 발생했을 때 CI 가 아닌 인간 리뷰어에게만 의존하는 상태" 입니다.

이 슬라이스는 또 하나의 docs 마이크로 라운드를 찍지 않고, 같은 가족의 current-risk 를 자동 가드로 줄이기 위해 새 regression 모듈 `tests/test_docs_sync.py` 하나를 추가합니다. 이 regression 은 browser smoke inventory 의 현재 루트-doc 계약을 세 가지 차원에서 lock 합니다:

1. `docs/ACCEPTANCE_CRITERIA.md` 의 `Playwright smoke covers <N> core browser scenarios` inventory count 와 `docs/NEXT_STEPS.md` 의 `Playwright smoke currently covers <N> core browser scenarios` count 가 반드시 일치.
2. `README.md` 의 `Current smoke scenarios:` 번호 목록이 같은 inventory count 에서 닫힘.
3. `docs/NEXT_STEPS.md` 가 `docs/ACCEPTANCE_CRITERIA.md:<line>` 형태의 하드코딩된 라인 앵커를 더 이상 사용하지 않음(직전 `/work` 가 이걸 stable 한 section anchor 로 이미 바꿨고, 이 가드가 재발을 막습니다).

구현/브라우저 스모크/런타임/파이프라인 코드는 건드리지 않았고, 기존 docs 본문도 수정하지 않았습니다.

## 핵심 변경

### `tests/test_docs_sync.py` (신규)

작은 단일 모듈로 추가했습니다. 헤비 마크다운 파서 없이 안정적인 정규식 3개와 간단한 라인 스캔을 사용합니다. 하드코딩된 라인 번호는 사용하지 않으며, 레포 경로는 `__file__.resolve().parent.parent` 로 잡았습니다.

주요 요소:

- `REPO_ROOT`, `README_PATH`, `ACCEPTANCE_PATH`, `NEXT_STEPS_PATH` — 세 루트 docs 경로 상수.
- `_read_text(path)` — utf-8 텍스트 읽기.
- `_extract_inventory_count(text, pattern, *, source)` — 정규식 하나를 받아 `<N> core browser scenarios` 캡쳐를 정수로 뽑고, 0건 혹은 2건 이상이면 정확한 `source` 이름과 함께 `AssertionError` 를 raise. 이 설계는 ACCEPTANCE_CRITERIA / NEXT_STEPS 양쪽에서 "Playwright smoke covers 125 core browser scenarios" 처럼 inventory 헤더가 정확히 한 번만 등장하는 현재 계약을 드러냅니다.
- `_extract_readme_max_smoke_scenario_number()` — README.md 를 읽고 `Current smoke scenarios:` 라인을 찾아, 그 다음 `##` 섹션 헤딩이 나올 때까지의 numbered 리스트 (`^(\d+)\.\s...`) 를 스캔해 최대 번호를 돌려줍니다. 섹션 경계 식별로 "다른 번호 리스트와 섞이지 않도록" 범위를 좁혔습니다.
- `BrowserSmokeInventoryDocsParityTest`:
  - `ACCEPTANCE_PATTERN = re.compile(r"Playwright smoke covers (\d+) core browser scenarios")`
  - `NEXT_STEPS_PATTERN = re.compile(r"Playwright smoke currently covers (\d+) core browser scenarios")`
  - `ACCEPTANCE_LINE_ANCHOR_PATTERN = re.compile(r"docs/ACCEPTANCE_CRITERIA\.md:\d+")`
  - `test_acceptance_and_next_steps_inventory_counts_match` — 두 count 가 같은지 확인. 실패 메시지는 "Update both together when the browser smoke inventory changes." 로 같이 올리라는 지시를 명시합니다.
  - `test_readme_numbered_smoke_list_closes_at_inventory_count` — README 번호 목록 최대값이 inventory count 와 같은지 확인.
  - `test_next_steps_does_not_hard_code_acceptance_line_anchor` — NEXT_STEPS.md 전체에서 `docs/ACCEPTANCE_CRITERIA.md:<line>` 패턴을 금지. 실패 메시지에 "Prefer a stable section anchor (for example, `### Current Gates` bullet under `## Test Gates` in `docs/ACCEPTANCE_CRITERIA.md`)" 라고 현재 정답 형태를 담았습니다.
- `if __name__ == "__main__": unittest.main()` — 단일 모듈 직접 실행도 허용.

docstring 은 "같은 날 여러 번 반복된 truth-sync 루프를 왜 이 regression 이 막는지" 한 문단으로 적었습니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 등 docs 본문 — 이번 라운드는 regression 이 이미 green 이라 docs 수정이 필요하지 않았습니다(직전 라운드에서 125 count, section anchor 교체가 이미 truthful 하게 닫혀 있습니다).
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/*`, `core/*`, `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `storage/*`, `.pipeline/*`, agent/skill 설정 — 이번 슬라이스 범위 밖.
- `tests/test_smoke.py` 기타 기존 test 모듈은 수정하지 않았습니다. handoff 가 권장한 대로 narrow 한 신규 모듈을 선택했습니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `Ran 3 tests in 0.003s`, `OK`.
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` → whitespace 경고 없음.
- handoff 지시에 따라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 돌리지 않았습니다. 이번 슬라이스는 신규 regression 한 모듈만 추가하고 docs 본문과 browser 계약은 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 regression 은 `<N> core browser scenarios` 라는 현재 shipped 문구에 결합되어 있습니다. 만약 미래에 inventory 헤더 문구 자체가 바뀌면(예: "browser smoke test suites" 로 rename), 세 테스트가 모두 "could not locate inventory header" 로 실패해 문구 변경 시점에 업데이트가 강제됩니다. 이는 의도적인 경직성이며, 문구 drift 를 실패로 드러내는 가드로 작동합니다.
- `_extract_readme_max_smoke_scenario_number()` 는 `Current smoke scenarios:` 마커 다음부터 다음 `## ` 섹션 헤더 전까지의 numbered 리스트 최대값을 추출합니다. 현재 README 구조(`## Playwright Smoke Coverage` 바로 뒤에 `Current smoke scenarios:` 가 있고 나중에 `## Safety Defaults` 가 오는 구조)가 바뀌면 역시 업데이트가 필요합니다.
- regression 은 `docs/ACCEPTANCE_CRITERIA.md:<line>` 라는 패턴만 NEXT_STEPS.md 에서 금지합니다. 다른 doc 에서 같은 스타일 라인 앵커가 생기는 경우까지 막지는 않습니다. 향후 동일 가족의 drift 가 다른 doc 에서 발견되면 범위를 넓혀 같은 테스트 파일에 추가하는 것이 합리적입니다. 이번 슬라이스는 handoff 가 지정한 좁은 범위만 닫았습니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` 등 dirty 상태입니다. 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 신규 파일과 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke inventory docs-parity guard 범위 밖은 건드리지 말라" 제약을 유지했습니다.
