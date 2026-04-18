# entity-card trusted-agreement and conflict-sensitive claim coverage

HANDOFF_SHA: e3544ff8ffbee9cd57ac61f14addf25e08ede04f18fdef648e5bed8eb8c793ac

## 변경 파일

- `core/web_claims.py`
- `tests/test_smoke.py`
- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음

## 변경 이유

- `docs/TASK_BACKLOG.md`의 current-phase browser-investigation quality axis 중, 이번 라운드 직전 verified-top3 reinvestigation ranking까지 닫힌 뒤에도 `core/web_claims.py`의 `summarize_slot_coverage()`가 raw `support_count >= 2`만 보고 slot을 `strong`(`[교차 확인]`)으로 올리는 rule이 남아 있었습니다. 그 결과 low-trust peer들의 noisy agreement도 `strong`이 되거나, 같은 slot 안에 cross-verified된 두 값이 공존해도 primary만 보고 `strong`으로 올리는 문제가 있었습니다.
- Gemini advice `seq 286`이 이 구간을 agreement-over-noise 계열의 현재 최상단 current-risk slice로 좁혔습니다. 이번 슬라이스는 `summarize_slot_coverage()` 한 곳 안에서 trusted-agreement 규칙과 conflict-sensitive downgrade만 추가해서 user-visible `[교차 확인]` 표기의 의미를 더 정확하게 만드는 bounded 변경입니다. 새 schema/UI/answer mode/권한 흐름을 요구하지 않습니다.

## 핵심 변경

- `core/web_claims.py`에 두 개의 작은 helper를 추가하고 `summarize_slot_coverage()`의 `strong` 판정 규칙을 재정의했습니다. `merge_claim_records()` / `_claim_sort_key()` / 다른 출력 구조와 `ClaimRecord` / `SlotCoverage` 필드는 건드리지 않았습니다.
  - `_trusted_supporting_source_count(record)`: primary 카드의 `supporting_sources` 안에서 `TRUSTED_CLAIM_SOURCE_ROLES`(백과 기반 / 공식 기반 / 데이터 기반 / 설명형 출처)에 속한 supporter의 distinct URL (URL 없으면 title) 개수를 계산합니다. `supporting_sources`가 비어 있을 때도 record 자체의 `source_role`이 trusted면 단일 fallback으로 잡아 안전한 값을 돌려줍니다.
  - `_has_competing_trusted_alternative(items, primary)`: 같은 slot 안에서 primary 값과 겹치지 않는 다른 record가 자체적으로도 cross-verified trusted-agreement(≥2 distinct trusted supporter)를 가질 때만 conflict로 판정합니다. single-source 반대 의견 하나만으로 primary의 cross-verification을 내리지 않도록, 반대쪽도 같은 기준을 통과해야 downgrade합니다.
- `summarize_slot_coverage()`의 판정은 이제 `primary.support_count >= 2 and trusted_supporting_count(primary) >= 2 and not _has_competing_trusted_alternative(items, primary)`일 때만 `CoverageStatus.STRONG`이고, 그 외에는 `CoverageStatus.WEAK`입니다. primary 선택, `primary_claim`, `candidate_count`는 기존과 동일한 `_claim_sort_key` 결과를 그대로 유지해서 `_select_entity_fact_card_claims()` / `_build_entity_claim_coverage_items()` 쪽 primary 값과 어긋나지 않게 했습니다.
- `core/agent_loop.py`는 건드리지 않았습니다. 기존 call-site(`summarize_slot_coverage(claim_records, slots=CORE_ENTITY_SLOTS)` × 4곳)는 strict한 새 규칙을 그대로 받아 rendering/verification-label downgrade에 반영됩니다.
- `docs/PRODUCT_SPEC.md`의 "entity-card agreement-over-noise baseline" 줄에 새 shipped 규칙을 한 문장으로 덧붙여 `[교차 확인]` = trusted-agreement + conflict-resolved 임을 설명했습니다. UI/새 tag/새 status는 추가하지 않았습니다.

## 검증

- `python3 -m py_compile core/web_claims.py tests/test_smoke.py tests/test_web_app.py` → 통과.
- `python3 -m unittest tests.test_smoke -k summarize_slot_coverage` → `Ran 2 tests`, `OK` (새 `test_summarize_slot_coverage_untrusted_only_agreement_stays_weak`, `test_summarize_slot_coverage_conflicting_trusted_alternative_downgrades_to_weak`).
- `python3 -m unittest tests.test_smoke -k claim_coverage` → `Ran 5 tests`, `OK`.
- `python3 -m unittest tests.test_smoke -k entity` → `Ran 21 tests`, `OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 3 tests`, `OK`.
- `python3 -m unittest tests.test_web_app -k claim_coverage` → `Ran 21 tests`, `OK`.
- `python3 -m unittest tests.test_web_app -k entity` → `Ran 55 tests`, `OK`.
- `python3 -m unittest tests.test_web_app -k reinvestigation` → `Ran 3 tests`, `OK`.
- `python3 -m unittest tests.test_smoke` → `Ran 113 tests`, `OK`.
- `python3 -m unittest tests.test_web_app` → `Ran 310 tests`, `OK`.
- `git diff --check -- core/web_claims.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` → 이슈 없음.
- Playwright / `make e2e-test` → 미실행. 이번 변경은 backend 내부 status 판정 규칙과 Python regression 범위였고 selector/copy/layout/기존 dual-probe·multi-source 고정 수량(`strong:3 · 미확인:2`, `strong:1 · 단일 출처:4`)과 fact-card rendering 텍스트는 기존 그대로 유지된 것을 `test_web_app -k entity` 55건이 잠그고 있어 browser-visible contract가 넓어지지 않았다고 판단했습니다. `docs/ACCEPTANCE_CRITERIA.md`의 browser-visible 고정 문자열은 변경하지 않았습니다.

## 남은 리스크

- 이번 downgrade는 primary와 경쟁하는 값이 자체적으로도 `≥2 distinct trusted supporter`를 가질 때만 발동합니다. 한쪽 trusted source 하나 vs 다른 trusted source 하나 같은 single-vs-single trusted disagreement는 기존처럼 primary 기준으로 `strong`이 되지 않고 자연스럽게 `weak`으로 남지만, single-vs-double trusted disagreement처럼 primary가 이미 trusted agreement를 쥔 경우에는 경쟁 값이 single trusted라도 downgrade하지 않습니다. 이건 "genuinely uncertain only when both camps are cross-verified"라는 spec 문장에 맞추어 보수적으로 잡은 기준입니다. 실제 corpus에서 single trusted source가 반박하는 사실이 많이 관측되면, 추후 "trusted rival 1건 이상"까지 conflict 기준을 넓히는 후속 슬라이스가 필요할 수 있습니다.
- `supporting_sources`가 비어 있는 legacy in-memory record를 직접 `summarize_slot_coverage()`에 넣는 경우, 현재 fallback은 primary의 자신 `source_role`만 보고 최대 1개의 trusted supporter로 센다. 이 경우 새 규칙상 `strong`은 나올 수 없고 `weak`로 남습니다. production 경로는 모두 `merge_claim_records()`를 통과해 `supporting_sources`가 채워지므로 실제 영향은 없지만, 외부에서 이 helper를 재사용할 일이 생기면 명시적 contract 문서화가 필요해질 수 있습니다.
- 이번 변경은 `core/web_claims.py` 한 파일에 닫았고 `core/agent_loop.py`는 그대로 두었습니다. 다음에 같은 family의 다음 슬라이스(예: "설명형 다중 출처 합의" verification label 문장을 trusted-agreement 기준에 맞춰 더 정확한 Korean 문구로 조정) 가 필요해지면 그때 `agent_loop` 쪽 rendering을 함께 다루는 것이 맞습니다.
- 더티 worktree(`docs/projectH_pipeline_runtime_docs/**`, `verify/4/9/**`, 그리고 untracked `report/gemini/...`, `work/4/17/...default-cleanup*.md`, `verify/4/17/...default-cleanup-verification.md`, `verify/4/17/...entity-card-reinvestigation-top3-ranking-verification.md`)는 이번 슬라이스와 무관해 그대로 두었습니다.
