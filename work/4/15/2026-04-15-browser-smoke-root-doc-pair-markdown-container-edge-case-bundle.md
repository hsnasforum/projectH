# browser smoke root-doc pair markdown-container edge-case bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/15/2026-04-15-browser-smoke-root-doc-pair-markdown-container-edge-case-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 라운드들이 스캔 단위를 physical line → paragraph block → markdown item 으로 순차 개선해 왔으나, `_split_into_markdown_items`에 여전히 세 가지 markdown container 수준의 edge case가 남아 있었습니다:

1. fenced code block (` ``` ` / `~~~`) 내부의 heading / list marker / bullet 이 별개 item 으로 파싱되어 false match 를 만들 수 있음
2. block quote (`> `) 가 앞뒤 prose 와 blank line 없이 이어질 때 하나의 item 으로 병합되어 pair boundary 가 흐려질 수 있음
3. block-level HTML 태그가 두 개의 서로 다른 pair mention 을 하나의 over-broad item 으로 합칠 수 있음

operator stop (`CONTROL_SEQ: 130`)이 "또 다른 narrower same-family micro-slice 대신, 남은 markdown container edge case 를 한 번에 닫는 broader bounded bundle 을 승인한다"고 명시했기 때문에 이 세 edge case 를 하나의 라운드에서 함께 닫았습니다.

## 핵심 변경

### `tests/test_docs_sync.py`

module-level helper `_split_into_markdown_items` 에 세 가지 container 인식을 추가했습니다:

1. **Fenced code block**: `_FENCED_CODE_PATTERN = re.compile(r"^(\`{3,}|~{3,})")` 으로 opening/closing fence 를 추적합니다. fence 내부의 모든 줄은 하나의 opaque item 에 속하며, heading / list marker / bullet regex 에 걸리지 않습니다. closing fence 는 opening fence 와 같은 문자로 같거나 더 긴 반복이어야 닫힙니다 (CommonMark 규칙). 닫히지 않은 fence 는 파일 끝에서 하나의 item 으로 flush 됩니다.

2. **Block quote**: `_BLOCK_QUOTE_PATTERN = re.compile(r"^>\s?")` 으로 block-quote 줄을 인식합니다. 연속된 block-quote 줄은 같은 item 에 유지되지만, non-quote content 뒤에 block-quote 가 오면 새 item 을 엽니다. 반대로 block-quote run 뒤에 non-quote 줄이 오면 기존 item 을 flush 하여 prose 와 병합되지 않습니다.

3. **HTML block**: `_HTML_BLOCK_PATTERN` 으로 `<div>`, `<table>`, `<pre>`, `<details>` 등 block-level 태그 시작을 인식하고, 해당 줄에서 새 item boundary 를 엽니다. inline HTML 은 영향받지 않습니다.

class docstring 도 새 edge-case coverage 를 반영하도록 업데이트했습니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — 현재 5개 루트 docs 에 fenced code block, block quote, block-level HTML 이 없어 docs 수정이 필요하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`, `app/`, `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, agent/skill 설정 — 이번 슬라이스 범위 밖.
- `BrowserSmokeInventoryDocsParityTest` 3개 테스트 — 무변경.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `test_entity_card_pair_unique_in_all_root_docs ... ok`
    - `test_latest_update_pair_unique_in_all_root_docs ... ok`
    - `Ran 5 tests in 0.019s`, `OK`.
- `git diff --check -- tests README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` → whitespace 경고 없음.
- 별도 inline edge-case 검증 (임시 스크립트, 삭제 완료):
  - fenced code block 내부의 heading / bullet / numbered item 이 별개 item 으로 분리되지 않고 하나의 opaque item 에 포함됨을 확인.
  - block quote run 이 앞뒤 prose 와 병합되지 않고 독립 item 으로 분리됨을 확인.
  - HTML block tag 가 item boundary 를 여는 것을 확인.
  - tilde fence (`~~~`) 와 중첩 backtick fence (` ```` ` 안의 ` ``` `) 가 올바르게 처리됨을 확인.
- Playwright / `make e2e-test` / 전체 unittest 재실행은 실행하지 않았습니다. 이번 슬라이스는 `tests/test_docs_sync.py` helper 만 수정했고 browser / runtime 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- `_split_into_markdown_items` 는 여전히 의도적으로 가벼운 heuristic 입니다. 실제 CommonMark 파서를 도입하지 않는다는 handoff 제약을 유지했습니다. 현재 5개 루트 docs 에 fenced code block / block quote / HTML block 이 없으므로 새 regex 가 실제 pair matching 에 영향을 주지 않지만, 미래에 이런 구조가 추가되면 heuristic 이 올바르게 보호합니다.
- HTML block 인식은 block-level 태그 목록 기반이며, 커스텀 HTML 컴포넌트나 비표준 태그는 인식하지 않습니다. 현재 루트 docs 에는 해당 없습니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등에 dirty 상태가 있습니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 의 helper hardening 과 이 closeout 노트만 추가했습니다.
