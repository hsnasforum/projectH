# 2026-04-19 product spec conflict docs truth sync verification

## 변경 파일
- `verify/4/19/2026-04-19-product-spec-conflict-docs-truth-sync-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-product-spec-conflict-docs-truth-sync.md`)의 docs 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`reinvestigation-conflict-suggestions-probe-cap-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 401 (`CONFLICT Family PRODUCT_SPEC Docs Truth-Sync Bounded Bundle`)은 `docs/PRODUCT_SPEC.md` 한 파일 안 6문장만 bounded 묶음으로 맞추는 docs-only 슬라이스였습니다. `:347, :370, :269`는 truthful 상태라 의도적으로 untouched 지시였고, 다른 파일은 건드리지 않는 조건이었습니다.
- 이번 `/work`가 target 6문장(`:107, :155, :344, :348, :367, :369`)이 정확히 업데이트되고 untouched 3문장(`:269, :347, :370`)은 그대로 유지됐다고 주장했으므로, 각 변경이 현재 tree와 일치하는지와 handoff scope_limit을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`reinvestigation-conflict-suggestions-probe-cap-verification`)는 seq 400 reinvestigation round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `docs/PRODUCT_SPEC.md:107`이 이제 `claim coverage panel with status tags (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`), ... (reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state)`로 panel 4-tag + focus-slot 5-state 확장을 모두 반영합니다.
  - `docs/PRODUCT_SPEC.md:155`가 `explanation covering reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state`로 focus-slot 5-state tail만 확장했고 bracket-tag 열거는 건드리지 않았습니다.
  - `docs/PRODUCT_SPEC.md:344`가 `status tags (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`) leading each slot line`으로 panel 4-tag를 반영합니다.
  - `docs/PRODUCT_SPEC.md:348`이 `telling the user whether the slot was reinforced, regressed, is still single-source, is still unresolved, or remains in an explicit \`정보 상충\` state after reinvestigation`으로 focus-slot 5-state 확장을 반영합니다.
  - `docs/PRODUCT_SPEC.md:367`이 panel 4-tag와 focus-slot 5-state tail을 모두 반영합니다.
  - `docs/PRODUCT_SPEC.md:369`가 `weak-slot reinvestigation baseline: weak/missing/conflict slots all eligible for reinvestigation suggestions, with MISSING preferred over WEAK and CONFLICT below both, ...`로 seq 400 구현(`_build_entity_reinvestigation_suggestions::status_priority`에 CONFLICT: 2 추가)과 일치합니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `docs/PRODUCT_SPEC.md:347` "response-body section headers annotated with matching status tags (`확인된 사실 [교차 확인]`, `단일 출처 정보 [단일 출처]`, `확인되지 않은 항목 [미확인]`)"는 `core/agent_loop.py:4700-4725` response-body emission 현실과 일치하므로 그대로입니다. `docs/ACCEPTANCE_CRITERIA.md:49`의 "does not emit a dedicated `[정보 상충]` response-body header tag" 주장과도 정합.
  - `docs/PRODUCT_SPEC.md:370` response-body 3-tag enumeration도 위와 같은 이유로 그대로입니다.
  - `docs/PRODUCT_SPEC.md:269` `claim_coverage_summary` 4-key shape는 seq 376에서 이미 truthful하게 synced됐습니다.
- `/work`가 편집한 6문장은 `docs/ACCEPTANCE_CRITERIA.md:35/48/49/1375` canonical phrasing(seq 381/382)와 정합하도록 `정보 상충` wording을 같은 Korean으로 사용합니다. 두 문서 간 CONFLICT framing이 어긋나지 않습니다.
- 이번 라운드에서 다른 파일은 수정되지 않았습니다. code, tests, `CLAUDE.md`/`AGENTS.md`/`GEMINI.md`/`README.md`/`PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md` 모두 untouched로 남았습니다.
- 같은 날 same-family docs-only round count는 seq 381과 이번 seq 401을 합쳐 2회입니다. 3회째는 `3+ docs-only same-family` guard 경고 임계값에 도달하므로, 남은 drift는 더 쪼개지 말고 한 번에 닫는 bounded bundle로 가야 합니다. 이어지는 후속 bundle(ARCHITECTURE / PRODUCT_PROPOSAL / project-brief / TASK_BACKLOG tail) 대상 drift는 패턴이 단일(`(reinforced / regressed / still single-source / still unresolved)` → `정보 상충` state 추가)하므로 한 라운드에 묶기 합리적입니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `docs/PRODUCT_SPEC.md:107/155/267/269/344/347/348/367/369/370`, `docs/ACCEPTANCE_CRITERIA.md:35/48/49/1375`, `core/agent_loop.py:4700-4725`.
  - 결과: `/work`가 설명한 6문장 편집이 현재 tree와 일치하고, untouched 3문장과 ACCEPTANCE_CRITERIA / response-body emission은 실제로 그대로입니다.
- `git diff --check -- docs/PRODUCT_SPEC.md` → 이번 verify 독립 실행, 출력 없음, exit `0`.
- `grep -nE "정보 상충|\[교차 확인\]|\[정보 상충\]|\[단일 출처\]|\[미확인\]|reinforced|regressed|still single-source|still unresolved|weak/missing|weak-slot reinvestigation baseline" docs/PRODUCT_SPEC.md` → 이번 verify 독립 실행. 6 target 문장 모두 예상 `정보 상충` 확장을 포함하고, untouched 3문장은 의도대로 유지됐음을 확인.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `tests.test_web_app`, `tests.test_smoke`, Playwright, `make e2e-test`: 이번 라운드는 `docs/PRODUCT_SPEC.md` 한 파일 docs-only sync라 code/test/runtime 변화가 전혀 없었습니다. `.claude/rules/browser-e2e.md`와 `.claude/rules/doc-sync.md` 기준 모두 재실행 불필요.

## 남은 리스크
- 동일 패턴의 stale 문장이 여전히 4개 파일에 남아 있습니다: `docs/ARCHITECTURE.md:11/142/1377`, `docs/PRODUCT_PROPOSAL.md:26/65`, `docs/project-brief.md:15/89`, `docs/TASK_BACKLOG.md:25` focus-slot tail. 이들은 전부 `(reinforced / regressed / still single-source / still unresolved)` enumeration이라 한 번의 bounded bundle로 닫을 수 있습니다. 다음 라운드는 이 4개 파일을 한 번에 sync하는 docs-only round 3(같은 날 same-family `3+ docs-only` guard 경고 임계)으로 잡고, 그 이후에는 code 라운드로 돌아가 4+ 미만으로 유지하는 편이 맞습니다.
- `docs/TASK_BACKLOG.md:26` Playwright scenario 설명과 `:823` SQLite parity gate 설명은 각각 historical/implemented coverage를 묘사하는 문장입니다. CONFLICT-state Playwright scenario가 이미 base config에 포함돼 있지만 SQLite parity gate에 편입됐는지가 별도 확인되기 전에는 `reinforced / regressed / still single-source / still unresolved`를 "이미 cover되는 상태 목록"으로 해석하면 여전히 truthful일 수 있으므로, 다음 bundle에서도 `:26, :823`은 대상에서 제외하고 current-contract 요약 성격의 `:25` tail만 수정하는 편이 안전합니다.
- Milestone 4의 remaining code sub-axis(COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, 추가 reinvestigation tuning)는 여전히 future code round 후보입니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
