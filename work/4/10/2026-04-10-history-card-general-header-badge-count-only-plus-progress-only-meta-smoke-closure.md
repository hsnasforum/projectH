# history-card general header-badge count-only-plus-progress-only meta smoke closure

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` — `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다` 시나리오에 card8(`answer_mode: "general"`, non-empty `claim_coverage_summary` + empty `claim_coverage_progress_summary`) 와 card9(`answer_mode: "general"`, empty `claim_coverage_summary` + non-empty `claim_coverage_progress_summary`) fixture 두 건과 각각의 두 부분 `.meta` 합성 어서션을 추가

## 사용 skill
- `round-handoff`
- `e2e-smoke-triage`

## 변경 이유
- 직전 `/work` (`2026-04-10-history-card-general-header-badge-count-plus-progress-meta-smoke-tightening.md`) 와 그 `/verify` 는 general 카드의 label → count → progress 세 부분 합성 경로(card7) 를 잠갔지만, non-investigation general 카드에는 두 가지 partial 경로가 여전히 스모크에서 관찰되지 않았음
  - label + count-only (no progress)
  - label + progress-only (no count)
- `app/static/app.js:2954-2969` 의 렌더러는 investigation 이 아닌 카드에 대해 `detailLines.push(formatAnswerModeLabel(item.answer_mode))` 로 label 을 먼저 넣고, `claim_coverage_summary` 가 있을 때만 `사실 검증 ...` 라인을 push, `claim_coverage_progress_summary` 가 있을 때만 progress 라인을 push 한 뒤 `detailLines.join(" · ")` 로 `.meta` 를 구성함 — 두 partial 경로 모두 `일반 검색 · <second part>` 라는 정확히 두 부분 합성이어야 하고, 한 부분이 비어 있는 경우 leading/trailing ` · ` artifact 가 생겨서는 안 됨
- 두 경로가 동일 branch, 동일 selector surface, 동일 scenario 안에 있고 각각 한 건의 fixture + 몇 줄의 어서션으로 잠기기 때문에 한 라운드에 묶어 닫는 것이 추가 micro-slice 라운드보다 이득임 (handoff `implementation scope` 가 이를 명시함)
- 이 슬라이스는 런타임/도큐먼트 변경 없이 동일 isolated scenario 안에서 fixture 두 건과 `.meta` 어서션만 추가해 non-investigation renderer 경로의 마지막 두 partial 합성 경로를 고정하는 범위임

## 핵심 변경
1. **card8 fixture 추가** (`e2e/tests/web-smoke.spec.mjs`) — label + count-only
   - `answer_mode: "general"` (non-investigation → label prepend)
   - `claim_coverage_summary: { strong: 2 }` — 단일 카테고리만 채워 `formatClaimCoverageCountSummary` 가 `교차 확인 2` 를 내고 count segment 자체에 ` · ` artifact 가 없음
   - `claim_coverage_progress_summary` 미정의 — 세 번째 detailLine 이 push 되지 않음
2. **card9 fixture 추가** — label + progress-only
   - `answer_mode: "general"`
   - `claim_coverage_summary` 미정의 — 두 번째 detailLine 이 push 되지 않음
   - `claim_coverage_progress_summary: "일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다."` — 유일한 두 번째 detailLine 으로 push 됨
3. **cards count 어서션 갱신**
   - `await expect(cards).toHaveCount(7)` → `await expect(cards).toHaveCount(9)`
4. **card8 label+count-only `.meta` 어서션 추가**
   - `await expect(card8Meta).toHaveCount(1)` / `toHaveText("일반 검색 · 사실 검증 교차 확인 2")`
   - `not.toContainText("출생일: 단일 출처")`, `"혼합 지표:"`, `"일반 지표:"`, `"일반 진행:"`, `"설명 카드"`, `"최신 확인"` — 다른 카드 progress 문자열/answer-mode label 누출 방지
   - `length > 0`, `startsWith("·") === false`, `endsWith("·") === false`
   - `card8LabelIdx >= 0`, `card8CountIdx > card8LabelIdx` — label → count 순서 잠금
5. **card9 label+progress-only `.meta` 어서션 추가**
   - `toHaveText("일반 검색 · 일반 진행: 커뮤니티 단서가 단일 출처 상태로 남아 있습니다.")`
   - `not.toContainText("사실 검증")` — count segment 가 섞여서는 안 됨
   - `not.toContainText("출생일: 단일 출처")`, `"혼합 지표:"`, `"일반 지표:"`, `"설명 카드"`, `"최신 확인"` — 다른 카드 progress/라벨 누출 방지
   - `length > 0`, `startsWith("·") === false`, `endsWith("·") === false`
   - `card9LabelIdx >= 0`, `card9ProgressIdx > card9LabelIdx` — label → progress 순서 잠금
- 재사용 원칙: 기존 scenario 내부의 `cards = historyBox.locator(".history-item")`, `.meta` 셀렉터, 기존 `renderSearchHistory` 호출 경로만 재사용했고 새 selector/helper/fixture 파일을 만들지 않았음. `formatAnswerModeLabel("general")` → `"일반 검색"`, `formatClaimCoverageCountSummary({strong:2})` → `"교차 확인 2"`, `detailLines.join(" · ")` 합성 경로도 기존 런타임 코드를 그대로 사용함

## 검증
이번 라운드 실행:
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다" --reporter=line` → `1 passed (6.7s)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs work/4/10` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- broader Playwright suite 또는 `make e2e-test` — browser-visible contract 가 넓어지지 않았고 isolated scenario 한 개 안에 fixture 두 건/assertions 몇 줄만 추가함
- `tests.test_web_app` 등 unit suite — 런타임/라우트/도큐먼트 미변경
- 다른 history-card family scenario — 이번 변경은 해당 isolated scenario 안에서만 동작함

## 남은 리스크
- `toHaveText` 는 `formatAnswerModeLabel("general")` 이 `"일반 검색"`, `formatClaimCoverageCountSummary({strong:2})` 이 `"교차 확인 2"`, `detailLines.join(" · ")` 의 구분자가 ` · ` 라는 점에 의존함. 해당 포맷(`app/static/app.js:2225-2239`, `:2969`) 이 바뀌면 이 스모크가 먼저 깨짐 — 다만 같은 문자열이 다른 claim-coverage / answer-mode UI 곳에서도 사용 중이므로 drift 범위는 런타임 전반과 동일
- card8 의 `not.toContainText("·")` 는 의도적으로 넣지 않았음. label + count 두 부분 합성은 join separator 가 한 번 등장하므로 `"·"` 부정 어서션은 여기서는 유효하지 않음. 대신 `toHaveText` 고정 문자열 + `startsWith/endsWith` 로 separator artifact 를 잠금
- card9 의 `not.toContainText("사실 검증")` 은 count segment 가 아예 섞이지 않았음을 잠그지만, 향후 progress 문자열 자체가 `사실 검증` 을 포함하게 된다면 fixture 문구를 함께 조정해야 함
- card3 (general, 모든 claim_coverage_* empty) label-only 경로는 기존 어서션(`not.toContainText("·")`, `length > 0`) 으로 이미 잠겨 있으므로 이번 라운드에서는 건드리지 않음
- 이번 슬라이스로 general 카드의 네 가지 `.meta` 조합(label-only / label+count / label+progress / label+count+progress) 이 모두 어서션으로 잠겼고, investigation 카드의 empty / count-only / count+progress 조합도 이전 라운드들에서 이미 잠겼음 — 동일 scenario 내부에서 확인 가능한 `.meta` 조합 공간은 이 라운드로 family closure 에 도달함
