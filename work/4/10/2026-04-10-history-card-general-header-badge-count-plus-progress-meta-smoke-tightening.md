# history-card general header-badge count-plus-progress meta smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` 시나리오에 card7(`answer_mode: "general"`, 다중 카테고리 `claim_coverage_summary` + non-empty `claim_coverage_progress_summary`) fixture 한 건과 세 부분 `.meta` 합성 순서(label → count → progress) 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-header-badge-count-plus-progress-claim-coverage-meta-smoke-tightening.md`) 와 그 `/verify` 는 investigation 카드(card6: entity_card) 의 count-plus-progress 경로를 잠갔지만, non-investigation (general) 카드는 여전히 count+progress 경로가 스모크에서 관찰되지 않았음
- `app/static/app.js:2954-2969` 의 렌더러는 investigation 이 아닌 카드에서는 `detailLines.push(formatAnswerModeLabel(item.answer_mode))` 로 answer-mode label 을 **먼저** 넣은 뒤 `claim_coverage_summary` 가 있으면 `사실 검증 <포맷 카운트>` 를 두 번째, `claim_coverage_progress_summary` 가 있으면 그것을 세 번째로 넣고 `detailLines.join(" · ")` 로 `.meta` 를 구성함 — 즉 general 카드에서 두 필드가 모두 채워지면 `일반 검색 · 사실 검증 ... · <progress>` 라는 **세 부분 합성 순서** 가 고정되어야 함
- `formatAnswerModeLabel` (`app/static/app.js:2234-2239`) 은 `general` 에 대해 `"일반 검색"` 을 반환하고, 다중 카테고리 `claim_coverage_summary: { strong: 2, weak: 1 }` 는 `formatClaimCoverageCountSummary` (`app/static/app.js:2225-2232`) 를 통해 `"교차 확인 2 · 단일 출처 1"` 을 내므로 count segment 자체가 합법적으로 ` · ` 를 포함해 스모크는 "label → count → progress" 순서를 별도로 명시적으로 잠글 수 있음
- `app/serializers.py:277-287` 가 history item 을 직렬화할 때 여전히 `answer_mode`, `claim_coverage_summary`, `claim_coverage_progress_summary` 를 함께 전달하므로, 세 필드가 동시에 채워지는 입력은 런타임상 관찰 가능한 현재 contract 임
- 이 슬라이스는 런타임/도큐먼트 변경 없이 동일 isolated scenario 안에서 fixture 한 건과 세 부분 합성 순서 어서션만 추가해 이미 shipped 된 non-investigation renderer 경로의 마지막 미잠금 합성 경로를 고정하는 범위임

## 핵심 변경
1. **card7 fixture 추가** (`e2e/tests/web-smoke.spec.mjs`)
   - `answer_mode: "general"` (non-investigation → answer-mode label line **prepend**)
   - `verification_label: "보조 커뮤니티 참고"`, `source_roles: ["보조 커뮤니티"]`
   - `claim_coverage_summary: { strong: 2, weak: 1 }` — 다중 카테고리로 채워 count segment 가 `교차 확인 2 · 단일 출처 1` 이 되도록 하고, count segment 자체에 ` · ` 가 합법적으로 포함되게 함
   - `claim_coverage_progress_summary: "일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다."` — non-empty 로 세 번째 detailLine 이 push 되게 함
2. **cards count 어서션 갱신**
   - `await expect(cards).toHaveCount(6)` → `await expect(cards).toHaveCount(7)`
3. **card7 label-plus-count-plus-progress `.meta` 어서션 추가**
   - `await expect(card7Meta).toHaveCount(1)` — detailMeta 가 정확히 하나 렌더링
   - `await expect(card7Meta).toHaveText("일반 검색 · 사실 검증 교차 확인 2 · 단일 출처 1 · 일반 지표: 커뮤니티 단서와 교차 확인이 함께 관찰되었습니다.")` — label + count segment + progress 합성 결과를 정확한 문자열로 잠금
   - `await expect(card7Meta).not.toContainText("출생일: 단일 출처")` — card1 progress-summary 텍스트 누출 없음
   - `await expect(card7Meta).not.toContainText("혼합 지표:")` — card6 progress-summary 텍스트 누출 없음
   - `await expect(card7Meta).not.toContainText("설명 카드")` / `not.toContainText("최신 확인")` — 다른 answer-mode label 이 meta 에 섞이지 않아야 함
   - `expect(card7MetaText.length).toBeGreaterThan(0)` — blank meta 가 아님
   - `expect(card7MetaText.startsWith("·")).toBe(false)` 및 `endsWith("·")` 는 `false` — leading/trailing separator artifact 없음
   - `card7LabelIdx >= 0`, `card7CountIdx > card7LabelIdx`, `card7ProgressIdx > card7CountIdx` — label → count → progress 세 부분이 모두 존재하고 이 순서로 배치됨을 명시적으로 잠금
- 재사용 원칙: 기존 scenario 내부의 `cards = historyBox.locator(".history-item")`, `.meta` 셀렉터, 기존 `renderSearchHistory` 호출 경로만 재사용했고 새 selector/helper/fixture 파일을 만들지 않았음. `formatAnswerModeLabel("general")` → `"일반 검색"`, `formatClaimCoverageCountSummary({strong,weak})` → `"교차 확인 N · 단일 출처 N"`, `detailLines.join(" · ")` 합성 경로도 기존 런타임 코드를 그대로 사용함

## 검증
이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (5.8s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 isolated scenario 한 개 안에 fixture 하나/assertions 몇 줄만 추가함
- `tests.test_web_app` 등 unit suite — 런타임/라우트/도큐먼트 미변경
- 다른 history-card family scenario — 이번 변경은 해당 isolated scenario 안에서만 동작함

## 남은 리스크
- `toHaveText` 는 `formatAnswerModeLabel("general")` 이 정확히 `"일반 검색"` 을 내고, `formatClaimCoverageCountSummary({strong:2,weak:1})` 이 정확히 `"교차 확인 2 · 단일 출처 1"` 을 내며, `detailLines.join(" · ")` 의 구분자가 ` · ` 라는 점에 의존함. 해당 포맷(`app/static/app.js:2225-2239`) 또는 join separator 가 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage / answer-mode UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- `indexOf` 기반 순서 어서션은 label/count/progress 문자열이 각각 정확히 한 번씩 등장한다는 가정을 전제로 함. 중복 등장 (예: progress 문자열 안에 `일반 검색` 문구가 포함) 같은 경우 잘못된 위치를 잡을 수 있어, fixture 의 progress 문자열은 label/count segment 과 겹치지 않는 `일반 지표: ...` 를 의도적으로 선택함
- card3 (general, `claim_coverage_*` 모두 empty) `.meta` 의 `not.toContainText("·")` 어서션은 여전히 single-line 경로에 특수화되어 있고 이번 라운드에서 건드리지 않음 — card7 은 card3 과는 **다른 별도 fixture** 로서 multi-line 경로를 잠금
- 반대 방향 (`claim_coverage_summary` 비어 있고 progress 만 non-empty) general 카드 경로는 `detailLines = [label, progress].join(" · ")` 형태의 2-part 합성이므로 별도 슬라이스에서 다뤄야 하고, 이번 슬라이스에서는 다루지 않음
