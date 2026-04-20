# 2026-04-19 remaining conflict docs truth sync bundle verification

## 변경 파일
- `verify/4/19/2026-04-19-remaining-conflict-docs-truth-sync-bundle-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-remaining-conflict-docs-truth-sync-bundle.md`)의 docs 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`product-spec-conflict-docs-truth-sync-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 402 (`CONFLICT Family Remaining Docs Truth-Sync Bundle — ARCHITECTURE + PRODUCT_PROPOSAL + project-brief + TASK_BACKLOG focus-slot tails`)는 4개 파일 8문장을 한 번에 닫는 final bounded docs-sync 슬라이스였습니다. `docs/TASK_BACKLOG.md:26` Playwright scenario 설명과 `:823` SQLite parity gate 설명은 의도적 untouched 지시였고, 다른 파일은 건드리지 않는 조건이었습니다.
- 이번 `/work`가 8 target 문장이 정확히 `or remains in an explicit 정보 상충 state` 확장을 받았고, 두 untouched TASK_BACKLOG 문장이 그대로 유지됐으며, 다른 파일/코드/테스트는 수정되지 않았다고 주장했으므로, 각 변경이 현재 tree와 일치하는지와 scope_limit을 넘지 않았는지 이번 verify에서 고정해야 다음 control 선택이 안전합니다.
- 선행 verify(`product-spec-conflict-docs-truth-sync-verification`)는 seq 401 PRODUCT_SPEC-only sync 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `docs/ARCHITECTURE.md:11`, `:142`, `:1377` 세 문장이 모두 `(reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state)` 패턴으로 확장됐습니다.
  - `docs/PRODUCT_PROPOSAL.md:26`, `:65` 두 문장이 같은 패턴으로 확장됐고, `:26`의 trailing `already shipped.`는 보존됐습니다.
  - `docs/project-brief.md:15`, `:89` 두 문장이 같은 패턴으로 확장됐습니다. `:15`의 긴 요약 문장 구조는 그대로 유지됐습니다.
  - `docs/TASK_BACKLOG.md:25` item 11 focus-slot tail이 같은 패턴으로 확장됐고, 같은 줄 앞쪽의 4-segment bar `(\`교차 확인 / 정보 상충 / 단일 출처 / 미확인\`)`는 그대로입니다(seq 381에서 이미 synced).
- 의도적 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `docs/TASK_BACKLOG.md:26` Playwright scenario 설명은 여전히 `reinforced / regressed / still single-source / still unresolved with natural Korean particle normalization`로 남아 있습니다. 이 문장은 Playwright scenario가 현재 covered하는 상태 목록을 묘사하는 historical/implemented coverage 성격이므로 이번 CONFLICT-family docs-sync bundle 범위 밖입니다. 필요 시 별도 Playwright-parity-docs 라운드에서 다뤄야 합니다.
  - `docs/TASK_BACKLOG.md:823` SQLite parity gate 설명은 `reinforced slot after reinvestigation, regressed slot after reinvestigation` 같은 구체 Playwright scenario 나열이라 exact old-style 4-state literal이 아니며, 두 번째 grep에도 걸리지 않았습니다. intentionally untouched 상태 유지.
  - `docs/PRODUCT_SPEC.md`(seq 401 종료), `docs/ACCEPTANCE_CRITERIA.md`(seq 381/382 종료), `docs/MILESTONES.md`(seq 381 bullets 추가), `core/*`, `app/*`, `storage/*`, `tests/*`, `e2e/*`, `CLAUDE.md`/`AGENTS.md`/`GEMINI.md`/`README.md`/`PROJECT_CUSTOM_INSTRUCTIONS.md` 모두 untouched로 유지됐습니다.
  - response-body section-header 3-tag enumeration(`확인된 사실 [교차 확인]:` / `단일 출처 정보 [단일 출처] (추가 확인 필요):` / `확인되지 않은 항목 [미확인]:`)은 여전히 현재 `core/agent_loop.py:4700-4725` emission과 일치하므로 변경 없음. `docs/ACCEPTANCE_CRITERIA.md:49` "does not emit a dedicated `[정보 상충]` response-body header tag" 주장도 truthful.
- CONFLICT family docs truth-sync는 이제 모든 user-facing docs 파일에서 닫혔습니다.
  - `docs/PRODUCT_SPEC.md`: :269(seq 376), :107/155/344/348/367/369(seq 401)
  - `docs/ARCHITECTURE.md`: :222(seq 376), :11/142/1377(이번 라운드)
  - `docs/ACCEPTANCE_CRITERIA.md`: :35/48/49(seq 381), :1375(seq 382)
  - `docs/TASK_BACKLOG.md`: :25 bar + focus-slot tail(seq 381 + 이번 라운드)
  - `docs/MILESTONES.md`: :51/52/151(seq 381) 새 Playwright bullets 추가
  - `docs/PRODUCT_PROPOSAL.md`: :26/65(이번 라운드)
  - `docs/project-brief.md`: :15/89(이번 라운드)
- 같은 날 same-family docs-only round count는 이제 3입니다(seq 381 + seq 401 + 이번 seq 402). `3+ docs-only same-family` guard edge에 도달했고, 오늘은 더 이상의 CONFLICT-family docs-only round를 열어서는 안 됩니다. 다음 슬라이스는 code 라운드로 pivot해야 guard를 넘지 않습니다.

## 검증
- 직접 문서 대조
  - 대상: `docs/ARCHITECTURE.md:11/142/1377`, `docs/PRODUCT_PROPOSAL.md:26/65`, `docs/project-brief.md:15/89`, `docs/TASK_BACKLOG.md:25/26/823`.
  - 결과: `/work`가 설명한 8 target 문장 편집이 현재 tree와 일치하고, `docs/TASK_BACKLOG.md:26/823`가 intentionally untouched 상태로 남아 있음을 확인했습니다.
- `grep -nE "reinforced / regressed / still single-source / still unresolved / or remains in an explicit \`정보 상충\` state" docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: target 8문장 모두 hit. 추가 line hit 없음.
- `grep -nE "reinforced / regressed / still single-source / still unresolved" docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: target 8문장은 shared substring으로 hit되고, 추가로 `docs/TASK_BACKLOG.md:26`(Playwright scenario 설명)만 old-style 4-state literal로 hit됐습니다. 이는 handoff 지시대로 의도된 untouched 상태이며, 이번 bundle의 누락이 아닙니다.
- `git diff --check -- docs/ARCHITECTURE.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `tests.test_web_app`, `tests.test_smoke`, Playwright, `make e2e-test`: 이번 라운드는 4개 docs 파일 docs-only sync라 code/test/runtime 변화가 전혀 없었습니다. `.claude/rules/doc-sync.md`와 `.claude/rules/browser-e2e.md` 기준 모두 재실행 불필요.

## 남은 리스크
- CONFLICT same-family docs truth-sync는 이번 라운드까지로 user-facing docs 전 파일에서 닫힌 상태입니다. 당일 same-family docs-only round count가 3이므로 오늘 더 이상의 CONFLICT docs 라운드는 열지 말아야 합니다.
- `docs/TASK_BACKLOG.md:26` Playwright scenario 설명과 `:823` SQLite parity gate 설명은 Playwright 실제 coverage list를 묘사하는 historical/implemented 성격 문장입니다. CONFLICT-state Playwright scenario가 실제로 SQLite parity gate 스위트에 편입돼 있는지 확인 후 필요 시 별도 Playwright-parity-docs 라운드에서 다뤄야 합니다. 이번 family와 별개 축이므로 오늘의 3-guard를 넘지 않습니다.
- Milestone 4의 remaining code sub-axis인 COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, 추가 reinvestigation trigger threshold / probe retry tuning은 여전히 file+surface+boundary pre-pinning이 필요합니다. 다음 슬라이스는 code 라운드여야 하며, 옵션이 여러 개이고 각각 pre-pinning이 필요하므로 rule상 operator 전에 Gemini arbitration을 먼저 여는 편이 맞습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
