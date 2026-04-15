# browser smoke root-doc pair markdown-container edge-case bundle verification

## 변경 파일

- `verify/4/15/2026-04-15-browser-smoke-root-doc-pair-markdown-container-edge-case-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 `tests/test_docs_sync.py` 의 lightweight markdown item matcher에 fenced code / block quote / block-level HTML 경계를 추가했다고 주장했으므로, 이번 verify round 에서는 그 helper 분기가 실제 코드에 들어갔는지, 현재 root docs truth 에 docs 수정이 정말 불필요한지, 그리고 기존 5개 unittest 가 여전히 green 인지만 좁게 재확인했습니다. 2026-04-15 same-family history 는 아직 1개 `/work` 와 신규 `/verify` round 뿐이라, truthful closure 뒤에는 같은 family 의 작은 current-risk reduction 한 슬라이스를 자동 선택할 수 있는 상태였습니다.

## 핵심 변경

- 최신 `/work` 의 핵심 claim 은 현재 코드와 대조했을 때 truthful 합니다. `tests/test_docs_sync.py` 에 `_FENCED_CODE_PATTERN`, `_BLOCK_QUOTE_PATTERN`, `_HTML_BLOCK_PATTERN`, fence state tracking, updated `_split_into_markdown_items(...)`, 그리고 container edge-case 설명을 반영한 `ClickReloadComposerPlainFollowUpRootDocPairTest` docstring 이 실제로 존재합니다.
- `python3 -m unittest -v tests.test_docs_sync` 를 다시 실행한 결과 5개 테스트가 모두 `ok` 였고 `Ran 5 tests in 0.020s`, `OK` 로 끝났습니다. 현재 root-doc pair uniqueness / inventory parity / stable acceptance reference shape 는 여전히 green 입니다.
- focused helper assertions 도 다시 통과했습니다. fenced code 는 heading/list marker 를 내부에서 opaque item 으로 유지했고, tilde fence 는 inner backtick 이 있어도 정상적으로 닫혔으며, block quote run 은 surrounding prose 와 분리되었습니다. block-level HTML 은 tag line 에서 새 boundary 를 여는 현재 heuristic 이 확인되었습니다.
- 현재 5개 root docs 에는 fenced code, block quote, block-level HTML 시작 marker 가 없어 docs body 수정이 필요하다는 증거는 보이지 않았습니다. 따라서 이번 `/work` 가 tests-only/helper-hardening round 로 머문 판단은 맞습니다.
- 다만 HTML 경계는 full HTML-block isolation 이 아니라 tag-line boundary opening 수준의 lightweight heuristic 입니다. 예를 들어 closing tag 뒤 prose 는 blank line 이 없으면 같은 item 으로 이어질 수 있습니다. 따라서 `/work` 의 HTML 관련 핵심 취지는 맞지만, "HTML block 전체를 독립 item 으로 격리했다"는 뜻으로 넓게 읽는 것은 현재 구현보다 강합니다.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과: 5 tests `ok`, `Ran 5 tests in 0.020s`, `OK`
- `python3 - <<'PY' ... ROOT_DOC_PATHS scan ... PY`
  - 결과: `No fenced-code, block-quote, or block-level HTML markers detected in the 5 root docs.`
- `python3 - <<'PY' ... _split_into_markdown_items focused assertions ... PY`
  - 결과: `Focused helper assertions passed for fenced code, tilde fences, block quotes, and HTML tag boundary opening.`
- Playwright, `make e2e-test`, 전체 unittest 는 다시 돌리지 않았습니다. 최신 `/work` 범위가 `tests/test_docs_sync.py` helper/docstring family 에만 머물렀고 browser/runtime/shared UI code 는 건드리지 않았기 때문입니다.
- exact `git diff --check -- tests ...` line 은 이번 verify round 에서 다시 돌리지 않았습니다. 현재 `tests/test_docs_sync.py` 와 최신 `/work` note 가 untracked 상태라 그 명령만으로는 새 helper branch 를 실질적으로 검수하기 어렵고, 위 focused assertions 가 더 직접적이었습니다.

## 남은 리스크

- `_split_into_markdown_items(...)` 는 여전히 intentionally lightweight heuristic 입니다. HTML closing tag 뒤 prose flush 같은 finer boundary 는 아직 dedicated unittest 없이 behavior-by-implementation 상태입니다.
- 방금 verify 에서 다시 실행한 helper assertions 는 persistent unittest method 로 저장된 상태가 아닙니다. 즉, fenced code / tilde fence / block quote / HTML tag boundary opening branch 는 다음 수정에서 regression 이 나도 현재 5개 root docs 가 같은 marker 를 쓰지 않으면 즉시 잡히지 않을 수 있습니다.
- repo dirty worktree 는 계속 남아 있습니다. 이번 verify round 는 latest `/work` family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, docs, 기타 test 변경은 건드리지 않았습니다.
