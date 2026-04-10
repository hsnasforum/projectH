# history-card entity-card claim-coverage count-summary persistence tightening

## 변경 파일
- `tests/test_web_app.py` — `WebSearchStore.save → list_session_record_summaries` 와 `WebAppService._serialize_web_search_history` 가 `_summarize_claim_coverage` 로부터 집계된 `claim_coverage_summary` dict 를 올바르게 누적/직렬화하는지 잠그는 두 개의 단위 테스트 추가
- `e2e/tests/web-smoke.spec.mjs` — 기존 entity-card reload Playwright 시나리오(`history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다`) 를 확장: 시드 record 에 entity-card 계열 `response_origin` 을 명시하고, 렌더된 history-item 에 `claim_coverage_summary: {strong:0, weak:1, missing:1}` 을 포함하며, 클릭 전과 `다시 불러오기` 클릭 후 모두 history-card `.meta` 가 `사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.` 정확 문자열을 유지하는지 어서션

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-general-header-badge-count-only-plus-progress-only-meta-smoke-closure.md`) 와 그 `/verify` 는 synthetic header-badge 시나리오 안의 generic `.meta` composition 가족(label-only / label+count / label+progress / label+count+progress / investigation count-only / investigation count+progress) 을 모두 잠갔음. 같은 가족 내부의 synthetic 추가 variant 는 더 이상 current-risk 가 아님
- 아직 잠기지 않은 current-risk 는 entity-card 경로의 `claim_coverage_summary` **persistence/reload** continuity. `storage/web_search_store.py:316` 의 `_summarize_claim_coverage` 는 record.claim_coverage 를 `{strong, weak, missing}` counts 로 집계하고, `app/serializers.py:280-284` 는 이를 그대로 직렬화하며, `app/static/app.js:2958-2960` 은 `formatClaimCoverageCountSummary` 를 거쳐 history-card `.meta` 의 `사실 검증 ...` 라인으로 렌더함
- 기존 검증은 progress-summary 쪽만 end-to-end 로 잠겨 있고(`tests/test_web_app.py:9649-9694`, `e2e/tests/web-smoke.spec.mjs:1379-1484`), count-summary 쪽은 store→serializer→browser reload 경로가 명시적 회귀 잠금을 갖지 않은 상태였음
- 이 슬라이스는 런타임 변경 없이 entity-card 의 current shipped persistence/reload contract 를 하나의 focused unit regression 두 개와 기존 browser reload scenario 한 개의 확장으로 잠그는 범위임. latest-update 나 general reload 는 이번 라운드 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` 단위 회귀 추가**
   - `test_web_search_store_list_summaries_includes_claim_coverage_summary`
     - entity-card record (strong×2, weak×1, missing×1) 과 빈 record 두 건을 `WebSearchStore.save` 로 저장
     - `store.list_session_record_summaries(session_id)` 가 반환하는 항목에 대해:
       - entity-card → `claim_coverage_summary == {"strong": 2, "weak": 1, "missing": 1}`
       - 빈 record → `claim_coverage_summary == {"strong": 0, "weak": 0, "missing": 0}`
   - `test_web_search_history_serializer_includes_claim_coverage_summary`
     - `WebAppService.web_search_store.save` 로 mixed-status record 를 저장 후 `service._serialize_web_search_history(session_id)` 호출
     - 반환된 history item 의 `claim_coverage_summary == {"strong": 1, "weak": 1, "missing": 1}` 을 잠금
   - 두 테스트 모두 기존 `_progress_summary` 테스트 쌍의 구조/스타일을 그대로 mirror 함 — 신규 helper/fixture/import 추가 없이 기존 `WebSearchStore`, `WebAppService`, `AppSettings`, `TemporaryDirectory` 를 재사용
2. **`e2e/tests/web-smoke.spec.mjs` entity-card reload 시나리오 확장**
   - 시드 record 의 `response_origin` 을 `{}` 에서 `{provider: "web", badge: "WEB", label: "외부 웹 설명 카드", answer_mode: "entity_card", verification_label: "설명형 단일 출처", source_roles: ["백과 기반"]}` 로 확장
     - `core/agent_loop.py:6370-6410` 의 `show_only` reload path 는 `stored_origin.get("answer_mode")` 가 있을 때 `dict(stored_origin)` 을 그대로 사용하므로, 이 필드들이 누락되면 reload 후 history 재직렬화가 `general` 로 떨어져 history-card `.meta` 가 `일반 검색 · ...` label 로 바뀜. entity-card persistence 경로를 잠그려면 stored origin 자체가 entity-card 여야 하며, `badge: "WEB"` 가 없으면 frontend `formatOrigin` 이 provider 를 badge 로 fallback 해 `WEB` 어서션이 깨짐
   - 렌더된 history item 에 `claim_coverage_summary: {strong: 0, weak: 1, missing: 1}` 을 추가 — record 의 claim_coverage (`weak`×1, `missing`×1) 와 동일한 카운트로 고정하고, `formatClaimCoverageCountSummary` 가 `"단일 출처 1 · 미확인 1"` 을 내어 count segment 자체가 합법적으로 ` · ` 를 포함하도록 함
   - 클릭 전 `.meta` 어서션 추가:
     - `toHaveCount(1)` / `toHaveText("사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.")`
     - `not.toContainText("설명 카드")` / `not.toContainText("최신 확인")` / `not.toContainText("일반 검색")` — entity_card 는 investigation 이므로 detailLines 에 answer-mode label 이 섞이지 않아야 함
     - `startsWith("·") === false` / `endsWith("·") === false` — leading/trailing separator artifact 방지
     - `historyCardMetaText.indexOf("사실 검증 단일 출처 1 · 미확인 1") < indexOf("단일 출처 상태 1건")` — count 라인이 progress 라인보다 앞에 오는 합성 순서 잠금
   - `다시 불러오기` 클릭 후 `.meta` 가 동일한 정확 문자열을 유지하는지 어서션 추가 — store→serializer→reload path 에서 count-summary 와 progress-summary 가 함께 보존됨을 end-to-end 로 잠금
- 재사용 원칙: 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#claim-coverage-hint`, `#transcript .message-when`), `prepareSession`, `renderSearchHistory`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않았음

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app` → `Ran 230 tests in 59.022s — OK` (신규 `_includes_claim_coverage_summary` 단위 테스트 두 개 모두 `ok`)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반이 유지됩니다" --reporter=line` → `1 passed (7.2s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 단일 isolated reload scenario 한 개만 확장함
- 다른 latest-update / general reload scenario — 이번 슬라이스는 entity-card 경로 only 로 의도적으로 한정

## 남은 리스크
- `toHaveText("사실 검증 단일 출처 1 · 미확인 1 · 단일 출처 상태 1건, 미확인 1건.")` 은 `formatClaimCoverageCountSummary({strong:0,weak:1,missing:1})` 이 `"단일 출처 1 · 미확인 1"` 을 내고 `detailLines.join(" · ")` separator 가 ` · ` 라는 점에 의존함. 해당 포맷(`app/static/app.js:2225-2232`) 이 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- 시드 record 의 `response_origin` 에 `badge: "WEB"` 와 `label: "외부 웹 설명 카드"` 가 명시되어야 reload 후 `WEB` 배지와 `설명 카드` 라벨이 유지됨. 만약 `_build_web_search_origin` 이 label 포맷을 바꾸면 시드와 실제 런타임 사이에 드리프트가 생길 수 있음 — 이 경우 시드를 함께 조정해야 함 (기존 `_build_web_search_origin` label 매핑은 `app/../core/agent_loop.py:5275-5279` 참고)
- `claim_coverage_summary` 를 렌더된 history item 에 client-side 로 추가해야 reload 전 pre-click `.meta` 에서도 `사실 검증 ...` 라인이 관찰됨. reload 후에는 store→serializer path 가 동일한 카운트를 재직렬화해 같은 문자열을 유지함. 만약 record 의 `claim_coverage` 와 client-seeded `claim_coverage_summary` 가 다른 값으로 준비되면 pre-click 과 post-reload 가 서로 다른 meta 문자열을 낼 수 있어, 이번 라운드는 두 값을 동일하게 맞춰 잠갔음
- latest-update 및 general reload 의 count-summary persistence 경로는 본 슬라이스 밖이며, latest-update 쪽은 `_infer_reloaded_answer_mode` (`core/agent_loop.py:6320-6327`) 분기와 `_build_web_search_origin` source-role 필터링을 함께 고려해야 하므로 별도 라운드로 남겨둠
- `response_origin: {}` 로 저장된 기존 record 는 reload 시 `_build_web_search_origin` fallback 을 타서 `general` 이 아닌 inference 결과(claim_coverage 있을 시 entity_card) 를 얻을 수 있지만, 그 fallback 경로에서도 stored record 자체의 `answer_mode` 는 여전히 `general` 이라 `list_session_record_summaries` 가 반환하는 history 는 `general` 로 보임 — 이 드리프트 자체는 런타임 버그가 아닌 "stored origin 이 없으면 history 라벨 과 reload 응답 라벨이 서로 다른 방식으로 유도된다" 는 기존 설계이며, 본 슬라이스는 이 경로를 다루지 않음
