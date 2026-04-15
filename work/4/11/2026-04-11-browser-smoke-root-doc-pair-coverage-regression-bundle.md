# browser smoke root-doc pair coverage regression bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/11/2026-04-11-browser-smoke-root-doc-pair-coverage-regression-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 라운드(`work/4/11/2026-04-11-browser-smoke-inventory-docs-parity-regression-bundle.md`)가 browser smoke inventory 의 count parity 와 `docs/NEXT_STEPS.md -> docs/ACCEPTANCE_CRITERIA.md:<line>` 하드코딩 앵커 금지를 `tests/test_docs_sync.py` 의 3개 테스트로 자동 가드했습니다. 그러나 같은 docs-parity 가족 안에 좁은 남은 current-risk 가 하나 더 있었습니다. 같은 날 새로 landed 된 click-reload composer plain-follow-up 페어(entity-card / latest-update)는 5개 루트 docs 에 모두 한 번씩 추가되었지만, 현재 regression 은 해당 페어 wording 자체를 assert 하지 않기 때문에 미래에 누군가 한두 개 루트 doc 에서만 그 페어를 조용히 삭제하거나 rename 해도 `tests.test_docs_sync` 는 그대로 green 이 나옵니다.

이 슬라이스는 또 다른 docs prose 라운드를 찍지 않고, 같은 regression 모듈(`tests/test_docs_sync.py`) 에 신규 `ClickReloadComposerPlainFollowUpRootDocPairTest` 테스트 클래스를 하나 추가해 해당 페어가 5개 루트 docs 에 모두 남아 있어야 한다는 계약을 자동으로 묶습니다. 구현 / 브라우저 스모크 / 런타임 / 파이프라인 / 기존 docs 본문은 건드리지 않았습니다. regression 은 이미 green 이라 docs 수정도 필요하지 않았습니다.

## 핵심 변경

### `tests/test_docs_sync.py`

기존 `BrowserSmokeInventoryDocsParityTest` 아래 새 테스트 클래스를 추가했습니다. 파일 상단 상수도 같이 확장했습니다.

- 상수 확장:
  - `MILESTONES_PATH`, `TASK_BACKLOG_PATH` 를 추가.
  - `ROOT_DOC_PATHS: tuple[Path, ...] = (README_PATH, ACCEPTANCE_PATH, MILESTONES_PATH, NEXT_STEPS_PATH, TASK_BACKLOG_PATH)` — 페어 regression 이 순회할 루트 docs 5개.
- 신규 클래스 `ClickReloadComposerPlainFollowUpRootDocPairTest`:
  - docstring 은 "새 브라우저 페어가 한 루트 doc 에서 조용히 빠져도 다른 루트 doc 에는 남아 있어 detection 되지 않을 수 있다"는 동기를 기록합니다.
  - 클래스 상수 `ENTITY_FRAGMENTS`, `LATEST_UPDATE_FRAGMENTS` 는 각각 최소한의 stable 한 fragment 집합을 정의합니다:
    - entity-card: `history-card entity-card`, `plain follow-up`, `load_web_search_record_id`, `#claim-coverage-box`, `visible`
    - latest-update: `history-card latest-update`, `plain follow-up`, `load_web_search_record_id`, `#claim-coverage-box`, `hidden`
    - visible/hidden 구분은 handoff 가 권장한 "visible/hidden claim-coverage distinction only where needed to keep the two scenarios separate" 를 따른 것이며, 두 페어가 섞여 같은 한 라인에서도 올바르게 매칭되도록 유지합니다.
  - `_line_contains_all(line, fragments)` 는 대소문자 무시 substring 매칭을 수행합니다. `docs/TASK_BACKLOG.md` 의 127/128 번 항목은 `History-card` (대문자 H) 로 시작하고, 다른 4개 루트 doc 은 `history-card` (소문자 h) 로 시작하기 때문입니다. 대소문자 무시는 안정적인 fragment 매칭 범위에서 문구 casing 편차를 흡수합니다.
  - `_assert_pair_present(doc_path, *, fragments, pair_label)` 는 파일 텍스트를 줄 단위로 스캔해 한 줄이라도 fragment 집합 전체를 포함하면 통과하고, 없으면 `{relative_path}: could not find a single line covering the {pair_label} click-reload composer plain-follow-up pair. Expected one line to contain all of: [...]. Keep the click-reload composer plain-follow-up pair in every required root doc (README.md, docs/ACCEPTANCE_CRITERIA.md, docs/MILESTONES.md, docs/NEXT_STEPS.md, docs/TASK_BACKLOG.md).` 메시지로 실패합니다. 실패 메시지가 "어느 doc" 에서 "어느 페어" 가 빠졌는지, 그리고 "어디에 반드시 남아 있어야 하는지" 를 한 번에 드러냅니다.
  - `test_entity_card_pair_present_in_all_root_docs` 와 `test_latest_update_pair_present_in_all_root_docs` 는 각각 `ROOT_DOC_PATHS` 를 `subTest` 로 순회하며 페어 존재를 확인합니다. `subTest` 를 사용한 덕분에 한 번 실행에서 여러 루트 doc 의 drift 를 동시에 드러낼 수 있고, 실패 시에도 다른 doc 의 검사를 멈추지 않습니다.

### 루트 doc 현재 계약이 만족하는 위치(참고)

- `README.md:251` (entity-card 124번 항목) 과 `README.md:252` (latest-update 125번 항목)
- `docs/ACCEPTANCE_CRITERIA.md:1473` 과 `docs/ACCEPTANCE_CRITERIA.md:1474`
- `docs/MILESTONES.md:147` 과 `docs/MILESTONES.md:148`
- `docs/NEXT_STEPS.md:23` (긴 inline inventory 한 줄에 `history-card entity-card / latest-update ... plain follow-up ... load_web_search_record_id ... #claim-coverage-box visible ... #claim-coverage-box hidden` 이 모두 포함되어 두 fragment set 을 동시에 만족)
- `docs/TASK_BACKLOG.md:141` 과 `docs/TASK_BACKLOG.md:142`

이 라인 위치들은 테스트에 하드코딩하지 않았고, `_line_contains_all` substring 매칭만 사용합니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — 새 regression 이 이미 green 이기 때문에 이번 라운드는 docs 본문을 전혀 수정하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/*`, `core/*`, `tests/*` (test_docs_sync.py 제외), `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `storage/*`, `.pipeline/*`, agent/skill 설정 — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `test_entity_card_pair_present_in_all_root_docs ... ok`
    - `test_latest_update_pair_present_in_all_root_docs ... ok`
    - `Ran 5 tests in 0.014s`, `OK`.
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` → whitespace 경고 없음.
- handoff 지시에 따라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 돌리지 않았습니다. 이번 슬라이스는 신규 test case 두 개만 추가하고, docs 본문과 browser / runtime 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- 새 regression 은 "한 줄 안에 모든 fragment 가 다 들어 있어야 한다" 는 형태로 동작합니다. 이는 현재 5개 루트 doc 의 문구 스타일(numbered item, bullet, inline inventory 한 문장) 을 관찰한 결과 한 줄 단위로 모이는 걸 확인했기 때문입니다. 미래에 특정 doc 이 페어 설명을 두 줄 이상으로 쪼개면 `_line_contains_all` 이 false negative 로 실패할 수 있습니다. 그 경우에는 두 옵션이 가능합니다 — 해당 doc 의 문구를 다시 한 줄로 합치거나, 테스트의 스캔 단위를 "paragraph (연속 non-empty line 블록)" 레벨로 넓히는 것. 이번 슬라이스는 현재 계약에 맞춘 가장 단순한 구현을 유지했습니다.
- 매칭은 대소문자 무시입니다. 향후 `HISTORY-CARD ENTITY-CARD` 같은 전혀 다른 스타일 변경까지도 흡수합니다. 반면 `entity card` (하이픈 없음) 혹은 `entity-card history-card` (순서 역전) 같은 변형은 여전히 실패합니다. 이는 "stable fragment" 라는 handoff 문구에 맞춘 의도적 경직성입니다.
- regression 은 entity-card 에 `visible`, latest-update 에 `hidden` 이라는 단어가 같은 줄에 등장한다는 사실에 의존합니다. 이는 현재 shipped wording 이 `#claim-coverage-box visible` / `#claim-coverage-box hidden` 형태를 따르기 때문에 안전합니다. 미래에 예를 들어 `#claim-coverage-box` 를 제거하거나 visible/hidden 대신 다른 용어(`표시/숨김`)를 쓰면 테스트가 업데이트 필요를 드러냅니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` 등 dirty 상태입니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 확장과 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke root-doc pair coverage regression guard 범위 밖은 건드리지 말라" 제약을 유지했습니다.
