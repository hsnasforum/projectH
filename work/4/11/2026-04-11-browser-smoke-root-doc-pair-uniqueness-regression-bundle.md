# browser smoke root-doc pair uniqueness regression bundle

## 변경 파일

- `tests/test_docs_sync.py`
- `work/4/11/2026-04-11-browser-smoke-root-doc-pair-uniqueness-regression-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`

## 변경 이유

직전 라운드(`work/4/11/2026-04-11-browser-smoke-root-doc-pair-coverage-regression-bundle.md`)가 `tests/test_docs_sync.py` 에 `ClickReloadComposerPlainFollowUpRootDocPairTest` 를 추가해 click-reload composer plain-follow-up 페어(entity-card / latest-update)가 5개 루트 docs 에 "한 번 이상" 남아 있음을 자동 가드했습니다. 그러나 그 가드는 "at least one" 만 확인할 뿐이어서 copy/paste 나 merge drift 로 한 루트 doc 안에 같은 페어가 "두 번" 등장하는 경우를 잡지 못합니다. 같은 날 같은 가족에서 반복된 docs drift 문제의 패턴을 고려할 때, 이 duplication 분기도 같은 regression 모듈에서 자동으로 닫는 것이 합리적입니다.

이 슬라이스는 또 다른 docs prose 라운드를 찍지 않고, 같은 테스트 모듈(`tests/test_docs_sync.py`) 안에서 기존 helper 를 "first-match return" 에서 "all-match count" 로 좁게 바꿔 각 루트 doc 이 entity-card / latest-update 페어마다 정확히 한 줄씩만 매칭되도록 tighten 합니다. 구현 / 브라우저 스모크 / 런타임 / 파이프라인 / docs 본문은 건드리지 않았습니다. 기존 5개 루트 docs 의 현재 내용이 이 tighter 계약을 이미 만족하기 때문에 docs 수정도 필요하지 않았습니다.

## 핵심 변경

### `tests/test_docs_sync.py`

`ClickReloadComposerPlainFollowUpRootDocPairTest` 내부의 helper 와 두 테스트 메소드 이름을 uniqueness 기반으로 교체했습니다. 상단 상수와 fragment set, `_line_contains_all` 은 그대로 유지했습니다.

- helper 변경:
  - 기존 `_assert_pair_present(doc_path, *, fragments, pair_label)` 를 제거하고, 같은 자리에 두 helper 로 쪼갰습니다:
    - `_count_pair_matches(doc_path, *, fragments)` 는 doc 을 줄 단위로 스캔하고 `(line_number, line)` 형태로 매칭 목록 전체를 돌려줍니다. 첫 매칭에서 조기 return 하지 않습니다.
    - `_assert_pair_unique(doc_path, *, fragments, pair_label)` 는 `_count_pair_matches` 결과 길이가 정확히 1 이면 통과, 0 이면 "could not find … expected exactly one line …" 실패 메시지, 2 이상이면 "found N lines matching … (line A, line B, …), but expected exactly one. Remove the duplicate so copy/paste or merge drift does not leave two entries for the same pair in one root doc." 로 실패합니다.
  - duplicate 실패 메시지에는 매칭 라인 번호 목록을 같이 노출해, 다음 라운드에서 어느 줄이 duplicate 인지 바로 보입니다.
- 테스트 메소드 이름 변경:
  - `test_entity_card_pair_present_in_all_root_docs` → `test_entity_card_pair_unique_in_all_root_docs`
  - `test_latest_update_pair_present_in_all_root_docs` → `test_latest_update_pair_unique_in_all_root_docs`
  - 두 테스트 모두 `subTest(doc=...)` 로 5개 루트 docs 를 같은 루프로 순회해, 한 실행에서 여러 doc 의 drift 를 같이 드러냅니다. 이번 변경은 각 subTest 의 assertion 을 "at least one" 에서 "exactly one" 으로 좁혔습니다.

신규 helper 덕분에 실패 메시지는 "얼마나 매칭됐는지" 와 "어느 줄에서 매칭됐는지" 를 동시에 알려 주고, missing 과 duplicate 양쪽 분기를 별도로 안내합니다.

### fragment set 과 casing 규칙

- `ENTITY_FRAGMENTS = ("history-card entity-card", "plain follow-up", "load_web_search_record_id", "#claim-coverage-box", "visible")`
- `LATEST_UPDATE_FRAGMENTS = ("history-card latest-update", "plain follow-up", "load_web_search_record_id", "#claim-coverage-box", "hidden")`
- 대소문자 무시 substring 매칭은 유지했습니다. `docs/TASK_BACKLOG.md` 의 `History-card` 대문자 시작 스타일을 계속 흡수합니다.
- `visible`/`hidden` 구분 덕분에 `docs/NEXT_STEPS.md:23` 의 긴 inline 라인 한 줄이 두 페어를 동시에 각각 한 번씩 매칭합니다(라인이 `#claim-coverage-box visible` 과 `#claim-coverage-box hidden` 을 모두 포함하므로 entity-card fragment set 기준으로도, latest-update fragment set 기준으로도 exactly one 매치가 됩니다).

### 기존 테스트 class 는 무변경

- `BrowserSmokeInventoryDocsParityTest` (count parity, README numbered list, `docs/ACCEPTANCE_CRITERIA.md:<line>` 하드코딩 금지) 3개 테스트는 건드리지 않았습니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` 본문 — tighter regression 이 이미 green 이라 docs 본문 수정은 필요하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/*`, `core/*`, `tests/*` (test_docs_sync.py 제외), `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `storage/*`, `.pipeline/*`, agent/skill 설정 — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_docs_sync`
  - 결과:
    - `test_acceptance_and_next_steps_inventory_counts_match ... ok`
    - `test_next_steps_does_not_hard_code_acceptance_line_anchor ... ok`
    - `test_readme_numbered_smoke_list_closes_at_inventory_count ... ok`
    - `test_entity_card_pair_unique_in_all_root_docs ... ok`
    - `test_latest_update_pair_unique_in_all_root_docs ... ok`
    - `Ran 5 tests in 0.013s`, `OK`.
- `git diff --check -- tests work/4/11 README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` → whitespace 경고 없음.
- handoff 지시에 따라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app` 재실행은 돌리지 않았습니다. 이번 슬라이스는 신규 helper 와 메소드 이름 변경만 하고, docs 본문과 browser / runtime 코드는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 tighter regression 은 "한 줄 단위 매칭" 이라는 가정 위에 작동합니다. 미래에 특정 doc 이 페어 설명을 여러 줄로 쪼개면 매칭 카운트가 0 이 되어 "could not find" 로 실패합니다. 그 경우에는 해당 doc 의 문구를 다시 한 줄로 합치거나, 스캔 단위를 "paragraph (연속 non-empty line 블록)" 레벨로 넓히는 별도 후속 슬라이스가 필요합니다. 이번 슬라이스는 현재 계약에 맞춘 가장 단순한 구현을 유지했습니다.
- uniqueness 는 fragment 집합 기준으로만 판정합니다. 예를 들어 한 doc 안에서 같은 페어를 "history-card entity-card click-reload composer … plain follow-up … load_web_search_record_id … #claim-coverage-box visible …" 로 한 줄, 그리고 "history-card entity-card click-reload composer … plain follow-up … load_web_search_record_id … #claim-coverage-box hidden …" 로 또 한 줄 쓴다면 후자는 entity-card 기준으로는 `visible` 불만족으로 매칭되지 않지만 latest-update 기준으로도 `history-card latest-update` 불만족으로 매칭되지 않아 둘 다 fragment set 에 걸리지 않습니다. 현재 shipped wording 은 이런 이상한 패턴을 만들지 않고, 만들 가능성도 낮습니다. 그러나 매우 이상한 wording 변경은 uniqueness 이전에 기존 presence 가드에서 먼저 실패하도록 설계되어 있습니다.
- duplication 실패 메시지는 매칭 라인 번호 목록을 돌려주지만, 이는 하드코딩된 라인 번호를 테스트 logic 에 넣는 것과는 다릅니다. logic 은 여전히 substring 매칭 기반이고, 라인 번호는 실패 시 사람이 drift 위치를 찾기 위한 힌트로만 노출됩니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` 등 dirty 상태입니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_docs_sync.py` 확장과 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke root-doc pair uniqueness guard 범위 밖은 건드리지 말라" 제약을 유지했습니다.
