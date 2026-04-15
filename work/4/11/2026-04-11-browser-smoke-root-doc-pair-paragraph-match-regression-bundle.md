# browser smoke root-doc pair paragraph-match regression bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/11/2026-04-11-browser-smoke-root-doc-pair-paragraph-match-regression-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 라운드(`work/4/11/2026-04-11-browser-smoke-root-doc-pair-uniqueness-regression-bundle.md`)가 `ClickReloadComposerPlainFollowUpRootDocPairTest` 의 match 단위를 "at least one" 에서 "exactly one per root doc" 으로 tighten 했습니다. 그 결과 copy/paste 나 merge drift 로 인한 duplicate pair entry 는 자동으로 걸립니다. 그러나 그 tighter 가드도 여전히 "각 페어가 physical 한 한 줄 안에서 모든 fragment 를 만족해야 한다" 는 line-format 가정을 깔고 있었습니다. 미래에 누군가 root doc 의 긴 한 줄 짜리 entry 를 가독성을 위해 두 줄 또는 세 줄의 soft-wrapped paragraph 로 재구성하면, 같은 내용인데도 fragment 가 여러 줄에 분산되어 line-level 매칭이 터지게 됩니다.

이 슬라이스는 또 다른 docs prose 라운드를 찍지 않고, 같은 regression 모듈(`tests/test_docs_sync.py`) 안에서 스캔 단위를 "physical line" 에서 "paragraph block (blank line 으로 구분되는 연속 non-empty 라인 블록)" 으로 바꿉니다. count parity / anchor shape / uniqueness / "exactly one per root doc" 은 유지되지만, fragment 가 같은 paragraph block 안에 있기만 하면 물리적 줄 바꿈이 여러 개여도 regression 이 여전히 green 을 냅니다. 구현 / 브라우저 스모크 / 런타임 / 파이프라인 / docs 본문은 건드리지 않았습니다. 현재 5개 루트 docs 의 content 가 이미 새 paragraph-level 계약을 만족하기 때문에 docs 수정도 필요하지 않았습니다.

## 핵심 변경

### `tests/test_docs_sync.py`

module-level helper 하나와 `ClickReloadComposerPlainFollowUpRootDocPairTest` helper 를 paragraph-block 기반으로 교체했습니다. 기존 `BrowserSmokeInventoryDocsParityTest` 와 `_extract_inventory_count`, `_extract_readme_max_smoke_scenario_number` 는 건드리지 않았습니다.

- 신규 module helper `_split_into_paragraph_blocks(text)`:
  - 반환 타입 `list[tuple[int, str]]`. 각 tuple 은 `(start_line_number, joined_block_text)` 이고, `start_line_number` 는 1-based 로 paragraph block 의 첫 물리 줄 번호, `joined_block_text` 는 block 내부의 여러 물리 줄을 `"\n"` 으로 join 한 문자열입니다.
  - 알고리즘은 단순하게 `text.splitlines()` 를 순회하면서 `strip() == ""` 인 블랭크 라인을 블록 경계로 처리합니다. 블랭크 라인이 없으면 연속한 non-empty 라인들이 모두 한 블록이 됩니다.
  - docstring 은 "joined block text preserves physical newlines so substring matching still sees the full block content, including wrapped continuation lines" 이라는 사실을 기록합니다. 이 덕분에 대소문자 무시 substring 매칭이 각 블록을 이어 붙인 전체 문자열에서 작동합니다.
  - hardcoded 라인 번호는 없고, 결과의 line number 는 오직 실패 시 사람이 drift 위치를 찾기 위한 힌트로만 사용됩니다.

- `ClickReloadComposerPlainFollowUpRootDocPairTest` 내부 helper 변경:
  - `_line_contains_all(line, fragments)` → `_block_contains_all(block_text, fragments)` (static method). 이름과 매개변수만 바뀌었고 대소문자 무시 all-fragment substring 매칭 로직은 동일합니다.
  - `_count_pair_matches(doc_path, *, fragments)` 는 내부에서 `text.splitlines()` 루프 대신 `_split_into_paragraph_blocks(text)` 를 사용합니다. 각 block 에 대해 `_block_contains_all(block_text, fragments)` 가 참이면 `(start_line, block_text)` 를 결과 목록에 append 합니다. 반환 타입은 그대로 `list[tuple[int, str]]` 이라 기존 caller 호환.
  - `_assert_pair_unique(doc_path, *, fragments, pair_label)` 는 len(matches) 가 정확히 1 이면 통과. 0 이면 missing 실패, 2 이상이면 duplicate 실패. 실패 메시지에서:
    - missing 메시지는 `"could not find a paragraph block covering the {pair_label} click-reload composer plain-follow-up pair. Expected exactly one paragraph block (contiguous non-empty lines) to contain all of: {list(fragments)}."` 로 바뀌어 스캔 단위가 paragraph block 임을 명시합니다.
    - duplicate 메시지는 `"found {len(matches)} paragraph blocks matching the {pair_label} click-reload composer plain-follow-up pair (block starting at line A, block starting at line B, ...), but expected exactly one. Remove the duplicate so copy/paste or merge drift does not leave two entries for the same pair in one root doc."` 로 바뀌어 각 matching block 의 시작 라인 번호를 노출합니다.
  - 두 테스트 메소드 `test_entity_card_pair_unique_in_all_root_docs` / `test_latest_update_pair_unique_in_all_root_docs` 는 그대로입니다. `subTest(doc=...)` 루프로 5개 루트 docs 를 순회하고 `_assert_pair_unique` 를 호출합니다.

- class docstring 을 paragraph-level 계약과 그 동기를 설명하도록 업데이트했습니다. 특히 "The scan unit is a paragraph block (contiguous non-empty lines separated by blank lines) so wrapping a single-line pair entry into a two-line paragraph does not break the guard as long as the fragments still live inside the same contiguous block." 이라는 한 문장을 추가해 line-format fragility 를 구체적으로 명시했습니다.

### 현재 루트 docs 가 paragraph-level 가드를 만족하는 이유(참고)

- `README.md` 의 `Current smoke scenarios:` 이후 번호 목록(124 / 125 번 항목 포함)은 하나의 연속 non-empty 라인 블록으로, entity-card fragment set 과 latest-update fragment set 을 각각 정확히 한 번씩 만족합니다. 다른 번호 항목들은 `#claim-coverage-box` + `plain follow-up` + `load_web_search_record_id` 의 조합을 동시에 갖지 않기 때문에 fragment set 기준으로 추가 매칭이 발생하지 않습니다.
- `docs/ACCEPTANCE_CRITERIA.md` 의 `### Current Gates` 아래 inventory bullet 리스트(1473 / 1474 라인 포함)는 한 block 으로 취급되고, 두 fragment set 을 각각 정확히 한 번씩 만족합니다.
- `docs/MILESTONES.md` 의 `## Shipped` browser smoke bullet 묶음(147 / 148 라인 포함)은 하나의 block 으로 취급되고, 두 fragment set 을 각각 정확히 한 번씩 만족합니다.
- `docs/NEXT_STEPS.md:23` 이 있는 단일 bullet 묶음 블록은 한 긴 인라인 문장 안에 `history-card entity-card`, `history-card latest-update`, `plain follow-up`, `load_web_search_record_id`, `#claim-coverage-box visible`, `#claim-coverage-box hidden` 을 모두 포함해 두 fragment set 을 각각 정확히 한 번씩 만족합니다.
- `docs/TASK_BACKLOG.md` 의 shipped 번호 목록(127 / 128 번 항목 포함)은 한 block 으로 취급되고, 두 fragment set 을 각각 정확히 한 번씩 만족합니다. `History-card` 대문자 변형은 대소문자 무시 매칭이 흡수합니다.

### 기존 테스트 class 는 무변경

- `BrowserSmokeInventoryDocsParityTest` 3개 테스트(count parity, README numbered list, `docs/ACCEPTANCE_CRITERIA.md:<line>` 하드코딩 금지)는 건드리지 않았습니다. 이 테스트들은 파일별 count / anchor / numbered list 최대값만 본다는 점에서 paragraph 스캔과 무관합니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — paragraph-level regression 이 이미 green 이라 docs 본문 수정은 필요하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/*`, `core/*`, `tests/*` (test_docs_sync.py 제외), `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `storage/*`, `.pipeline/*`, agent/skill 설정 — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `test_entity_card_pair_unique_in_all_root_docs ... ok`
    - `test_latest_update_pair_unique_in_all_root_docs ... ok`
    - `Ran 5 tests in 0.014s`, `OK`.
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` → whitespace 경고 없음.
- handoff 지시에 따라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 돌리지 않았습니다. 이번 슬라이스는 `tests/test_docs_sync.py` helper layer 만 교체하고, docs 본문과 browser / runtime 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- paragraph block 의 uniqueness 는 "블록 단위" 이기 때문에, 한 root doc 안에서 같은 블록 안에 같은 fragment set 을 만족시키는 두 번째 entry 가 생기면 regression 은 여전히 `count == 1` 로 green 을 냅니다. 블록 내부 duplicate 탐지는 line-level uniqueness 가 담당하던 분기인데, 이번 paragraph-level 전환으로 이 분기는 약해졌습니다. 반면, 다른 블록에 duplicate 가 생기는 경우(예: 문서의 다른 섹션에 페어 wording 이 copy/paste 되어 블랭크 라인으로 구분되어 붙는 경우)는 여전히 잡힙니다. 블록 내부 duplicate 탐지가 중요해지면 별도 후속 슬라이스에서 blocks-plus-lines hybrid 검사 또는 블록 내부에서 fragment set 이 몇 번 등장하는지 세는 방식을 추가할 수 있습니다.
- paragraph-block 분해는 markdown 의 다른 경계(heading, fence, indentation 변화 등)를 이해하지 않고 오직 "blank line" 만을 경계로 사용합니다. 예를 들어 `##` heading 뒤에 바로 bullet 이 오는 경우 heading 과 bullet 이 같은 블록으로 묶입니다. 현재 5개 루트 docs 에서는 이 단순화가 false positive 를 일으키지 않지만, 미래에 파일 구조가 크게 바뀌면 재검토가 필요할 수 있습니다. 다만 markdown parser 도입은 handoff 가 권장한 "stable-fragment based" 와 "avoid heavy dependencies" 방향에서 벗어나므로 이번 슬라이스는 채택하지 않았습니다.
- regression 은 fragment 집합이 `visible` / `hidden` 을 포함한다는 사실에 의존합니다. 미래에 어느 doc 이 `#claim-coverage-box visible` 대신 `#claim-coverage-box: visible` 혹은 `#claim-coverage-box 표시` 같은 변형으로 바뀌면 paragraph-level 에서도 substring 매칭이 깨집니다. 이는 의도적 경직성이며, 문구 변경 시 regression 이 업데이트 필요를 드러냅니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` 등 dirty 상태입니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 의 helper layer 교체와 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke root-doc pair paragraph-match guard 범위 밖은 건드리지 말라" 제약을 유지했습니다.
