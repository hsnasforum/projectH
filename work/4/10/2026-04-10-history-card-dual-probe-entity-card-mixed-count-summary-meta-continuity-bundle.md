# history-card dual-probe entity-card mixed count-summary meta continuity bundle

## 변경 파일
- `tests/test_web_app.py` — dual-probe entity-card 의 click-reload 와 natural-reload 두 체인에서 baseline history entry 가 `설명형 다중 출처 합의` verification_label 과 mixed `claim_coverage_summary` (`strong>0`, `weak>0`, `missing==0`), 빈 `claim_coverage_progress_summary` 를 baseline equality 로 각 단계에서 유지하는지 잠그는 focused 서비스 회귀 두 건과 공유 dual-probe `WebAppService` fixture helper (`_build_dual_probe_service_for_mixed_count_summary`) 를 추가:
  - `test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary`
  - `test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_mixed_count_summary`
- `e2e/tests/web-smoke.spec.mjs` — dual-probe click-reload 와 natural-reload 두 체인에 대해 mixed `.meta` continuity 를 잠그는 두 개의 신규 브라우저 시나리오 추가:
  - `history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe mixed count-summary meta가 truthfully 유지됩니다`
  - `entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 mixed count-summary meta가 truthfully 유지됩니다`

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-zero-strong-slot-follow-up-chain-missing-only-meta-continuity-bundle.md`) 와 그 `/verify` 는 zero-strong missing-only reload-follow-up chain 을 잠갔고, 같은 라운드의 검증 단계에서 다음 현재 위험으로 dual-probe mixed count-summary 분기가 명확히 드러남
- `tests/test_web_app.py:16345-17430` 과 `e2e/tests/web-smoke.spec.mjs:3751-6147` 의 기존 dual-probe 회귀/시나리오는 `response_origin` 과 `source_paths` 만 잠갔고, 실제 런타임이 노출하는 `claim_coverage_summary` 가 `{strong>0, weak>0, missing==0}` 형태를 유지하는지는 명시적 회귀/스모크가 없었음. 기존 고정물은 `claim_coverage: []` 와 `claim_coverage_summary` 미시드 상태로 empty-summary 분기만 exercise
- focused service probe 결과: 실제 dual-probe 런타임은 `strong=1`, `weak=4`, `missing=0`, `claim_coverage_progress_summary=""`, `verification_label="설명형 다중 출처 합의"` 를 냄 → `app/static/app.js:2225-2231` + `:2958-2969` 의 렌더러 경로에 의해 `.meta` 는 `사실 검증 교차 확인 1 · 단일 출처 4` 한 줄이어야 함
- handoff 지시대로 네 개 micro-slice 대신 하나의 bounded bundle 로 click-reload 와 natural-reload 두 체인을 같은 라운드에 닫음. zero-strong / latest-update / actual-search / noisy / general / docs / pipeline 은 의도적으로 범위 밖

## 핵심 변경
1. **`tests/test_web_app.py` focused 서비스 회귀 두 건 추가**
   - 공유 helper `_build_dual_probe_service_for_mixed_count_summary(self, tmp_path)` 로 기존 `test_handle_chat_dual_probe_entity_search_natural_reload_exact_fields` 와 동일한 `_FakeWebSearchTool` 매핑(`붉은사막/공식 플랫폼/공식 서비스` 세 쿼리 + `pearlabyss.com/200|300` 페이지) 과 `AppSettings` 구성을 생성. 기존 긴 fixture 를 두 테스트에서 중복 없이 재사용하기 위한 private 서비스 빌더이며 외부 동작은 바꾸지 않음
   - 공통 내부 헬퍼 `_assert_mixed_count_summary_continuity(result, stage)` 로 각 단계에서 다음을 잠금:
     - `result["ok"]` 참
     - `actions_taken` 에 `load_web_search_record` 포함
     - `session.web_search_history` 에 동일 `record_id` 항목 존재
     - `verification_label == "설명형 다중 출처 합의"`
     - `claim_coverage_summary.strong == baseline_strong`, `.weak == baseline_weak`, `.missing == 0`
     - `claim_coverage_progress_summary == ""`
   - click-reload 회귀: 초기 검색 → `{load_web_search_record_id}` show-only reload → `{user_text + load_web_search_record_id}` 첫 follow-up → 두 번째 follow-up 네 단계
   - natural-reload 회귀: 초기 검색 → `{user_text: "방금 검색한 결과 다시 보여줘"}` 자연어 reload → 첫 follow-up → 두 번째 follow-up 네 단계
   - baseline `strong` / `weak` 값을 그대로 기록해 `_FakeWebSearchTool` 내부 slot 분류 세부가 바뀌어도 baseline drift 부재만 엄격히 비교하며, `strong > 0` / `weak > 0` / `missing == 0` 정규화 패턴은 첫 호출부터 실패-우선으로 확인됨
2. **`e2e/tests/web-smoke.spec.mjs` 신규 브라우저 시나리오 두 건 추가**
   - 두 시나리오 모두 디스크 record 의 `claim_coverage` 를 1 strong + 4 weak slot (`{개발사: strong, 장르/플랫폼/서비스/출시일: weak}`) 로 시드해 서버 `_summarize_claim_coverage` 가 실제 런타임과 동일한 `{strong:1, weak:4, missing:0}` 결과를 내도록 정렬
   - `renderSearchHistory` item 에 `claim_coverage_summary: {strong:1, weak:4, missing:0}` 와 `claim_coverage_progress_summary: ""` 를 시드해 click-reload 직전부터 post-reload 까지 `.meta` 가 동일한 문자열을 유지하도록 정렬
   - 공통 어서션 (첫/두 번째 follow-up 각각):
     - `.meta` 정확 문자열 `"사실 검증 교차 확인 1 · 단일 출처 4"`
     - `not.toContainText("설명 카드")` / `"최신 확인"` / `"일반 검색"` — investigation 카드는 answer-mode label 이 skip 되어야 함
     - handoff 지시대로 `not.toContainText("·")` 는 **사용하지 않음** — count line 자체에 ` · ` 가 합법적으로 포함되기 때문. 대신 `not.toContainText(" ·  · ")` (double separator) 와 leading/trailing `·` artifact 부정으로 대체
     - `#response-origin-badge === "WEB"` + `web` class, `#response-answer-mode-badge === "설명 카드"`, `#response-origin-detail` 이 `설명형 다중 출처 합의` / `공식 기반` / `백과 기반` 포함, `#context-box` 가 `pearlabyss.com/200`(click-reload 시나리오) 또는 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`(natural-reload 시나리오) 과 대응 `/300` 을 포함
   - click-reload 시나리오: `renderSearchHistory` → `다시 불러오기` 클릭 → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - natural-reload 시나리오: `renderSearchHistory` → `다시 불러오기` 클릭 → `sendRequest({ user_text: "방금 검색한 결과 다시 보여줘" })` → 첫 follow-up → `.meta` 어서션 → 두 번째 follow-up → `.meta` 어서션
   - 기존 selector (`#search-history-box`, `.history-item`, `.meta`, `#response-origin-badge`, `#response-answer-mode-badge`, `#response-origin-detail`, `#context-box`) 와 `prepareSession`, `renderSearchHistory`, `sendRequest`, `fs/path` 헬퍼만 재사용했고 새 helper/selector/fixture 파일을 만들지 않음. 두 기존 dual-probe 시나리오(3751, 6077) 는 전혀 건드리지 않음 (handoff 지시)

## 검증
이번 라운드 실행:
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_card_history_card_reload_second_follow_up_preserves_mixed_count_summary` → `ok`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_mixed_count_summary` → `ok`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 dual-probe mixed count-summary meta가 truthfully 유지됩니다" --reporter=line` → `1 passed (7.2s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 mixed count-summary meta가 truthfully 유지됩니다" --reporter=line` → `1 passed (10.3s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `python3 -m unittest -v tests.test_web_app` 전체 슈트 — 본 슬라이스는 기존 `handle_chat` 경로에 순수 추가 회귀만 붙였고 기존 로직/helper 의 외부 동작은 바꾸지 않음. handoff 도 focused 두 회귀만 재실행을 요구함
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 두 개의 신규 isolated scenario 만 추가함
- 기존 dual-probe `response_origin` / `source_paths` 회귀/시나리오 및 zero-strong / latest-update / actual-search / noisy / general 계열 — handoff 는 이들을 그대로 두도록 명시함

## 남은 리스크
- 두 브라우저 시나리오의 `.meta` 어서션은 디스크 record 에 시드한 `claim_coverage` 의 strong/weak 비율(`1 strong + 4 weak`) 에 의존함. 이 비율을 바꾸면 서버가 재직렬화하는 count dict 도 함께 바뀌므로 `toHaveText("사실 검증 교차 확인 1 · 단일 출처 4")` 를 같이 조정해야 함. 의존성은 시드 배열 단일 지점에서 관리됨
- 두 서비스 회귀는 `strong > 0`, `weak > 0`, `missing == 0` 정규화 패턴과 baseline drift 부재만 단언함. 실제 런타임이 다른 분기(missing 포함, 전부 strong 등) 로 drift 하면 첫 호출부터 실패해 원인을 빠르게 가리킴 — failure-first 설계
- 공유 helper `_build_dual_probe_service_for_mixed_count_summary` 는 private 이므로 기존 테스트의 fixture 와 중복되지만 외부 동작은 동일함. 향후 `_FakeWebSearchTool` 매핑이 바뀌면 helper 와 기존 reload-exact-fields 테스트의 fixture 를 함께 맞춰야 함
- 내부 헬퍼 `_assert_mixed_count_summary_continuity` 의 `result` 인자는 `Any` 타입 힌트를 의도적으로 사용하지 않음 (`from typing import Any` 가 해당 파일 상단에 import 되어 있지 않음). dict-like 구조를 전제로 한 assertion 시퀀스만 수행함
- handoff 지시에 따라 `not.toContainText("·")` blanket rule 을 사용하지 않고 exact text + `not.toContainText(" ·  · ")` + leading/trailing `·` 부정 만으로 separator artifact 를 잠금. 향후 join separator 가 ` · ` 외 다른 문자로 바뀌면 이 조합이 먼저 깨짐
- zero-strong / latest-update / actual-search / noisy / general 가족의 mixed / missing-only / other `.meta` continuity 는 본 슬라이스 범위 밖. 각각 다른 `_infer_reloaded_answer_mode` 분기와 source-role 필터링을 고려해야 하므로 별도 라운드로 남겨둠
- `formatClaimCoverageCountSummary({strong:1, weak:4})` 이 현재 `"교차 확인 1 · 단일 출처 4"` 를 내는 포맷 가정(`app/static/app.js:2225-2232`)에 의존함. 포맷이 바뀌면 두 스모크가 먼저 깨짐 — 같은 문자열이 다른 claim-coverage UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
