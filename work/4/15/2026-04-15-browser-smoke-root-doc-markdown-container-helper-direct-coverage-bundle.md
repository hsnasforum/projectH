# browser smoke root-doc markdown-container helper direct-coverage bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/15/2026-04-15-browser-smoke-root-doc-markdown-container-helper-direct-coverage-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 라운드(`work/4/15/2026-04-15-browser-smoke-root-doc-pair-markdown-container-edge-case-bundle.md`)에서 `_split_into_markdown_items` 에 fenced code / block quote / HTML tag boundary 분기를 추가했으나, 현재 5개 루트 docs 에 해당 구조가 없어 기존 5개 pair-uniqueness / inventory-parity 테스트만으로는 이 분기들의 regression 을 잡을 수 없었습니다. verify round(`verify/4/15/...`)에서 ad-hoc assertion 으로 분기가 truthful 함은 확인했지만, persistent unittest 로 저장되지 않아 다음 수정 시 regression 이 조용히 통과할 수 있다는 리스크가 남아 있었습니다.

이 슬라이스는 그 ad-hoc assertion 들을 `MarkdownItemSplitterDirectTest` class 의 8개 persistent unittest method 로 전환하여 helper 분기를 직접 보호합니다.

## 핵심 변경

### `tests/test_docs_sync.py`

신규 test class `MarkdownItemSplitterDirectTest` 를 추가했습니다. 기존 두 class(`BrowserSmokeInventoryDocsParityTest`, `ClickReloadComposerPlainFollowUpRootDocPairTest`)는 무변경입니다.

#### Fenced code block 분기 (4개 테스트)

- `test_fenced_code_block_is_one_opaque_item`: backtick fence 내부의 heading / bullet / numbered marker 가 별개 item 으로 분리되지 않고 하나의 opaque item 에 포함됨을 검증.
- `test_tilde_fence_with_inner_backticks`: tilde fence(`~~~`) 내부에 backtick(`\`\`\``)이 있어도 fence 가 정상 close 됨을 검증.
- `test_longer_fence_not_closed_by_shorter`: 4-backtick fence 가 3-backtick 줄로는 닫히지 않고 4-backtick 으로만 닫힘을 검증 (CommonMark 규칙).
- `test_unclosed_fence_becomes_single_item`: 닫히지 않은 fence 가 파일 끝에서 하나의 item 으로 flush 됨을 검증.

#### Block quote 분기 (2개 테스트)

- `test_block_quote_splits_from_surrounding_prose`: `>` 줄이 앞뒤 prose 와 blank line 없이 이어져도 별개 item 으로 분리됨을 검증.
- `test_consecutive_block_quote_lines_stay_together`: 연속 `>` 줄이 같은 item 에 유지됨을 검증.

#### HTML block tag 분기 (2개 테스트)

- `test_html_block_tag_opens_new_boundary`: `<div>` 가 두 list item 사이에 boundary 를 열어 별개 item 으로 분리함을 검증.
- `test_html_closing_tag_opens_boundary`: `</details>` 같은 closing tag 도 boundary 를 여는 것을 검증.

### Docstring / comment wording

verify round 에서 "HTML 설명이 실제 heuristic 보다 넓게 읽힐 수 있다"는 관찰이 있었으나, 현재 docstring("a block-level HTML tag starts a line — prevents two distinct pair mentions from collapsing into one over-broad item")은 tag-line boundary opening 수준을 정확히 기술하고 있어 수정이 필요하지 않았습니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — 새 테스트가 synthetic doc 만 사용하므로 root docs 수정 불필요.
- `e2e/tests/web-smoke.spec.mjs`, `app/`, `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, agent/skill 설정 — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `BrowserSmokeInventoryDocsParityTest` 3개 테스트: `ok`
    - `ClickReloadComposerPlainFollowUpRootDocPairTest` 2개 테스트: `ok`
    - `MarkdownItemSplitterDirectTest` 8개 테스트: `ok`
    - `Ran 13 tests in 0.026s`, `OK`.
- Playwright / `make e2e-test` / 전체 unittest 재실행은 돌리지 않았습니다. 이번 슬라이스는 `tests/test_docs_sync.py` 에 synthetic-doc 기반 direct 테스트만 추가했고, browser / runtime / shared UI 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- `_split_into_markdown_items` 는 여전히 intentionally lightweight heuristic 입니다. HTML closing tag 뒤 prose flush, nested block quote 안의 list marker, indented code block 같은 finer edge case 는 아직 다루지 않으며, 현재 루트 docs 에서도 필요하지 않습니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등에 dirty 상태가 있습니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 에 direct-coverage 테스트 추가와 이 closeout 노트만 작성했습니다.
