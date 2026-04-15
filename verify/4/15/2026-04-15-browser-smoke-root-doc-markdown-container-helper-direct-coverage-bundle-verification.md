# browser smoke root-doc markdown-container helper direct-coverage bundle verification

## 변경 파일

- `verify/4/15/2026-04-15-browser-smoke-root-doc-markdown-container-helper-direct-coverage-bundle-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 `tests/test_docs_sync.py` 에 ad-hoc helper assertion 을 8개 persistent unittest 로 승격했다고 주장했으므로, 이번 verify round 에서는 그 direct test class 가 실제로 additive 하게 들어갔는지, 기존 root-doc parity / pair uniqueness guard 가 그대로 유지되는지, 그리고 최신 `/work` 의 검증 주장대로 `tests.test_docs_sync` 전체가 green 인지만 가장 좁게 다시 확인했습니다. 아울러 `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 의 현재 우선순위를 다시 보고, direct-coverage family 를 더 이어서 자동 `implement` 로 넘길지 판단했습니다.

## 핵심 변경

- 최신 `/work` 의 핵심 claim 은 현재 코드와 대조했을 때 truthful 합니다. `tests/test_docs_sync.py` 에 신규 `MarkdownItemSplitterDirectTest` class 가 실제로 존재하고, `test_fenced_code_block_is_one_opaque_item`, `test_tilde_fence_with_inner_backticks`, `test_longer_fence_not_closed_by_shorter`, `test_unclosed_fence_becomes_single_item`, `test_block_quote_splits_from_surrounding_prose`, `test_consecutive_block_quote_lines_stay_together`, `test_html_block_tag_opens_new_boundary`, `test_html_closing_tag_opens_boundary` 의 8개 direct test method 가 모두 들어가 있습니다.
- 기존 두 regression family 도 유지되고 있습니다. 현재 `tests/test_docs_sync.py` 는 `BrowserSmokeInventoryDocsParityTest` 3개, `ClickReloadComposerPlainFollowUpRootDocPairTest` 2개, `MarkdownItemSplitterDirectTest` 8개로 총 13개 테스트를 포함하며, direct coverage 가 additive 하게 붙은 형태입니다.
- `python3 -m unittest -v tests.test_docs_sync` 재실행 결과 13개 테스트가 모두 `ok` 였고 `Ran 13 tests in 0.035s`, `OK` 로 끝났습니다. `/work` 의 검증 섹션에 적힌 총 test count 와 green 상태가 현재 truth 와 일치합니다.
- scoped `git status --short ...` 확인 결과 이번 family 에서 직접 보이는 pending 파일은 `tests/test_docs_sync.py` 와 최신 `/work` note 뿐이었습니다. 즉, latest `/work` 가 말한 범위를 벗어나 `README.md`, `docs/`, `app/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` 쪽으로 퍼졌다는 증거는 현재 보이지 않았습니다.
- 다만 direct-coverage family 는 여기서 truthfully 닫혔고, 남은 same-family 후속은 `indented code block`, `nested block quote/list`, `HTML closing-tag + trailing prose` 같은 helper completeness 쪽에 더 가깝습니다. 반면 `docs/NEXT_STEPS.md:106`, `docs/MILESTONES.md:450`, `docs/TASK_BACKLOG.md:162` 의 현재 우선순위는 reviewed-memory guardrail family 를 가리키고 있어, 이번 verify scope만으로는 다음 exact implement slice 를 정직하게 하나로 좁히기 어려웠습니다. 그래서 next control 은 `STATUS: request_open` 으로 Gemini arbitration 을 여는 편이 맞다고 판단했습니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과: 13 tests `ok`, `Ran 13 tests in 0.035s`, `OK`
- `git status --short /home/xpdlqj/code/projectH/tests/test_docs_sync.py /home/xpdlqj/code/projectH/work/4/15/2026-04-15-browser-smoke-root-doc-markdown-container-helper-direct-coverage-bundle.md /home/xpdlqj/code/projectH/.pipeline/claude_handoff.md /home/xpdlqj/code/projectH/.pipeline/operator_request.md /home/xpdlqj/code/projectH/.pipeline/gemini_request.md`
  - 결과: `?? tests/test_docs_sync.py`, `?? work/4/15/2026-04-15-browser-smoke-root-doc-markdown-container-helper-direct-coverage-bundle.md`
- `rg -n "class MarkdownItemSplitterDirectTest|def test_" tests/test_docs_sync.py`
  - 결과: 신규 direct test class 1개와 direct test method 8개를 포함한 전체 test method 목록 확인
- `sed -n '106,180p' docs/NEXT_STEPS.md`
- `sed -n '450,490p' docs/MILESTONES.md`
- `sed -n '162,190p' docs/TASK_BACKLOG.md`
  - 결과: current priority text 는 reviewed-memory guardrail family 를 계속 우선순위로 두고 있으며, 이번 docs/test helper family 의 자동 연장은 문서상 next priority 와도 직접 맞물리지 않음을 재확인
- Playwright, `make e2e-test`, 전체 unittest, browser/runtime/service regression 은 다시 돌리지 않았습니다. 최신 `/work` 범위가 `tests/test_docs_sync.py` direct coverage 추가에 한정됐고 browser-visible contract 나 shared runtime code 는 건드리지 않았기 때문입니다.

## 남은 리스크

- `_split_into_markdown_items(...)` 의 remaining gaps 는 여전히 있습니다. 다만 direct-coverage family 이후 남은 항목은 현재 root docs 가 실제로 쓰지 않는 구조에 대한 matcher completeness 이므로, 그 자체만으로 다음 auto-implement slice 를 정당화하기는 어렵습니다.
- 현재 docs priority 는 reviewed-memory boundary guardrail family 쪽을 우선순위로 두고 있지만, 이번 verify round 는 그 family 구현 파일을 다시 읽거나 rerun 하지 않았으므로 여기서 바로 `.pipeline/claude_handoff.md` 를 새 exact slice 로 쓰면 과장 위험이 있습니다.
- repo dirty worktree 는 계속 남아 있습니다. 이번 verify round 는 latest `/work` family 와 next control 선택만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, docs, 기타 tests 변경은 건드리지 않았습니다.
