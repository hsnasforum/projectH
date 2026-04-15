# browser smoke root-doc pair markdown-item match regression bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/11/2026-04-11-browser-smoke-root-doc-pair-markdown-item-match-regression-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 라운드(`work/4/11/2026-04-11-browser-smoke-root-doc-pair-paragraph-match-regression-bundle.md`)가 `ClickReloadComposerPlainFollowUpRootDocPairTest` 의 스캔 단위를 physical line 에서 paragraph block(blank line 으로 구분되는 연속 non-empty 라인 블록)으로 바꿔 line wrapping 에 대한 취약성을 닫았습니다. 그러나 paragraph block 은 markdown 문서에서는 여전히 너무 거칠었습니다. README 나 TASK_BACKLOG 같은 문서는 번호 리스트 안에서 블랭크 라인 없이 100개 이상의 항목이 하나의 큰 paragraph block 으로 묶이고, MILESTONES 나 ACCEPTANCE_CRITERIA 도 긴 bullet 리스트가 하나의 block 으로 묶입니다. 이 구조에서는:

1. entity-card 페어 바로 옆에 duplicate entity-card 페어가 같은 번호 리스트 또는 bullet 리스트에 추가되어도 paragraph block 기준으로는 "count == 1" 로 통과합니다. 직전 라운드의 uniqueness 가드가 실질적으로 약화된 상태였습니다.
2. heading 이 바로 뒤의 list 나 prose 와 같은 block 에 포함되어 페어 경계가 흐려질 수 있었습니다.

이 슬라이스는 또 다른 docs prose 라운드를 찍지 않고, 같은 regression 모듈(`tests/test_docs_sync.py`) 안에서 스캔 단위를 "paragraph block" 에서 "lightweight markdown item (numbered list item / bullet list item / heading / 독립 prose paragraph)" 로 한 단계 더 좁힙니다. 이렇게 하면 같은 리스트 안에 같은 페어가 두 번 등장해도 각 항목이 별개의 markdown item 으로 분리되어 uniqueness 가드가 제대로 작동합니다. 동시에 item 내부의 continuation line (들여쓰기나 wrapped 한 이어지는 줄) 은 같은 item 에 포함되어 line wrap 회피는 계속 유효합니다.

구현 / 브라우저 스모크 / 런타임 / 파이프라인 / docs 본문은 건드리지 않았습니다. 현재 5개 루트 docs 의 content 는 이미 새 markdown-item 계약을 만족하기 때문에 docs 수정도 필요하지 않았습니다.

## 핵심 변경

### `tests/test_docs_sync.py`

module-level helper 를 `_split_into_paragraph_blocks` 에서 `_split_into_markdown_items` 로 교체했습니다. `ClickReloadComposerPlainFollowUpRootDocPairTest` 의 helper layer 도 같이 바뀌었습니다. 기존 `BrowserSmokeInventoryDocsParityTest` 3개 테스트는 건드리지 않았습니다.

- 신규 module-level 상수:
  - `_MARKDOWN_ITEM_START_PATTERN = re.compile(r"^\s*(?:\d+\.|[-*+])\s")` — optional leading whitespace 뒤의 숫자 리스트 마커(`1.`) 또는 bullet 마커(`-`, `*`, `+`) 다음 공백.
  - `_MARKDOWN_HEADING_PATTERN = re.compile(r"^#+\s")` — `#` 한 개 이상 + 공백으로 시작하는 heading.

- 신규 `_split_into_markdown_items(text) -> list[tuple[int, str]]`:
  - 각 item 은 `(start_line_number, joined_item_text)` 로 반환되고, `start_line_number` 는 1-based 로 item 의 첫 물리 줄.
  - item boundary 는 다음 중 하나를 만날 때 열립니다:
    - 숫자 리스트 마커가 줄 시작에 등장(`_MARKDOWN_ITEM_START_PATTERN` 매칭)
    - bullet 리스트 마커가 줄 시작에 등장
    - heading 이 등장(`_MARKDOWN_HEADING_PATTERN` 매칭) — heading 은 자체로 한 item 이 되고 뒤따르는 list/prose 를 흡수하지 않음
    - blank 라인 뒤의 non-empty 라인(마커 없음) — 새 prose paragraph
  - blank 라인은 현재 item 을 flush 해서 닫습니다.
  - 마커가 없는 continuation 라인(들여쓰기나 wrapped 라인)은 현재 item 에 append 되어 wrapped 한 content 도 같은 item 에 포함됩니다.
  - docstring 은 "This matcher is intentionally lightweight and stable-fragment based; it does not aim to be a faithful CommonMark parser." 라고 명시했습니다. 무거운 markdown parser 의존성을 추가하지 않는다는 handoff 제약을 지킵니다.
  - helper 는 내부 `_flush()` closure 로 current item 을 items 목록에 commit 하고 current_start / current_lines 를 초기화합니다.

- `ClickReloadComposerPlainFollowUpRootDocPairTest` 변경:
  - helper rename: `_block_contains_all` → `_item_contains_all` (static method). 대소문자 무시 all-fragment substring 매칭 로직은 동일.
  - `_count_pair_matches(doc_path, *, fragments)` 는 내부에서 `_split_into_markdown_items(text)` 를 사용하고, 각 item 에 대해 `_item_contains_all(item_text, fragments)` 가 참이면 `(start_line, item_text)` 를 결과에 append.
  - `_assert_pair_unique` 의 실패 메시지가 "paragraph block" 에서 "markdown item" 으로 바뀌었고, missing/duplicate 분기 모두 명확합니다:
    - missing: `"could not find a markdown item covering the {pair_label} click-reload composer plain-follow-up pair. Expected exactly one markdown item (numbered list item, bullet list item, heading, or standalone prose paragraph) to contain all of: {list(fragments)}."`
    - duplicate: `"found {N} markdown items matching the {pair_label} click-reload composer plain-follow-up pair (item starting at line A, item starting at line B, ...), but expected exactly one. Remove the duplicate so copy/paste or merge drift does not leave two entries for the same pair in one root doc."`
  - 두 테스트 메소드(`test_entity_card_pair_unique_in_all_root_docs`, `test_latest_update_pair_unique_in_all_root_docs`) 는 그대로. `subTest(doc=...)` 루프로 5개 루트 docs 를 순회합니다.
  - class docstring 업데이트: "The scan unit is a lightweight markdown item (numbered list item, bullet list item, heading, or standalone prose paragraph), not a raw blank-line paragraph block, so adjacent list items keep separate pair boundaries and duplicates inside one over-broad block cannot hide as a single blank-line paragraph match. Wrapped continuation lines inside the same item are still covered." 라는 문장을 추가해 왜 paragraph block 대신 markdown item 을 쓰는지, 그리고 wrapped continuation 은 여전히 같은 item 안에 묶인다는 점을 같이 기록했습니다.

### 현재 루트 docs 가 markdown-item 가드를 만족하는 이유(참고)

- `README.md` 의 `Current smoke scenarios:` 번호 리스트에서 124 번과 125 번 항목은 각각 자신의 numbered list item 으로 분리됩니다. 124 번은 `history-card entity-card` + `visible` + 나머지 fragment 를 모두 포함하고, 125 번은 `history-card latest-update` + `hidden` + 나머지 fragment 를 모두 포함합니다. 다른 번호 항목들은 `plain follow-up` + `load_web_search_record_id` + `#claim-coverage-box` 의 공통 조합을 갖지 않아 fragment set 에 걸리지 않습니다. 결과: 각 fragment set 당 exact-one item 매칭.
- `docs/ACCEPTANCE_CRITERIA.md` 의 `### Current Gates` 아래 inventory bullet 리스트에서 1473 / 1474 라인 두 bullet 이 각각 자신의 bullet item 으로 분리되고, 양쪽이 fragment set 을 한 번씩 만족합니다.
- `docs/MILESTONES.md` 의 `## Shipped` browser smoke bullet 묶음에서 147 / 148 라인 두 bullet 이 각각 자신의 bullet item 으로 분리되고, 양쪽이 fragment set 을 한 번씩 만족합니다.
- `docs/NEXT_STEPS.md:23` 의 긴 인라인 문장은 하나의 bullet item 안에 entity-card 와 latest-update 양쪽 페어를 한 번씩 표현합니다. item 내부에서 fragment 를 substring 매칭하므로 한 item 이 두 fragment set 을 각각 한 번씩 만족합니다. 다른 bullet 들은 이 fragment 조합을 갖지 않아 한 번의 매칭만 일어납니다.
- `docs/TASK_BACKLOG.md` 의 shipped 번호 리스트에서 127 번과 128 번 항목은 각각 자신의 numbered item 으로 분리됩니다. 대소문자 무시 매칭이 `History-card` 대문자 변형을 흡수합니다.

### 기존 테스트 class 는 무변경

- `BrowserSmokeInventoryDocsParityTest` 3개 테스트(count parity, README numbered list, `docs/ACCEPTANCE_CRITERIA.md:<line>` 하드코딩 금지)와 `_extract_inventory_count`, `_extract_readme_max_smoke_scenario_number` 는 그대로입니다. 이 테스트들은 파일별 count / anchor / numbered list 최대값만 보므로 markdown-item 스캔과 무관합니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — 새 regression 이 이미 green 이라 docs 본문 수정은 필요하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/*`, `core/*`, `tests/*` (test_docs_sync.py 제외), `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `storage/*`, `.pipeline/*`, agent/skill 설정 — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `test_entity_card_pair_unique_in_all_root_docs ... ok`
    - `test_latest_update_pair_unique_in_all_root_docs ... ok`
    - `Ran 5 tests in 0.041s`, `OK`.
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` → whitespace 경고 없음.
- handoff 지시에 따라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 돌리지 않았습니다. 이번 슬라이스는 `tests/test_docs_sync.py` helper layer 만 교체하고, docs 본문과 browser / runtime 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- `_split_into_markdown_items` 는 의도적으로 가벼운 heuristic 입니다. `^\s*(?:\d+\.|[-*+])\s` 와 `^#+\s` 두 regex 로만 item boundary 를 감지하며, fenced code block(` ``` `), block quote(`> `), HTML block, inline code 안의 마커 같은 진짜 CommonMark 구조는 파싱하지 않습니다. 현재 5개 루트 docs 에서는 이 단순화가 false positive 나 false negative 를 일으키지 않지만, 미래에 파일 구조가 크게 바뀌면 재검토가 필요할 수 있습니다. 다만 heavy markdown parser 도입은 handoff 가 명시적으로 금지한 방향입니다.
- markdown-item 분해는 blank 라인과 마커 시작 양쪽으로 boundary 를 열기 때문에, 연속한 두 bullet item 이 blank 라인 없이 이어져 있어도 각각 분리됩니다. 반면 한 bullet item 안에 여러 줄이 wrapped 되어 있으면 계속 같은 item 으로 묶입니다(마커가 없는 continuation 라인이 current item 에 append 되기 때문). 이 조합은 "wrapped 한 긴 문장" 과 "두 번째 페어" 를 구분하는 데 충분합니다.
- fragment set 은 계속 `visible` / `hidden` 에 의존합니다. 미래에 어느 doc 이 `#claim-coverage-box visible` 대신 `#claim-coverage-box: visible` 혹은 `#claim-coverage-box 표시` 같은 변형으로 바뀌면 markdown-item 단위에서도 substring 매칭이 깨집니다. 이는 의도적 경직성이며, 문구 변경 시 regression 이 업데이트 필요를 드러냅니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` 등 dirty 상태입니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 의 helper layer 교체와 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke root-doc pair markdown-item matcher 범위 밖은 건드리지 말라" 제약을 유지했습니다.
