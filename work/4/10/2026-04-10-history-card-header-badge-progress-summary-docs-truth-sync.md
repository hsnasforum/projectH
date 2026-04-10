# history-card header-badge progress-summary docs truth-sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — Playwright smoke 커버리지 총합을 `79 core browser scenarios` → `82 core browser scenarios`로 정정
- `docs/MILESTONES.md` — web-search history card header badge browser smoke 라인에 `investigation progress summary text when claim_coverage_progress_summary is non-empty` 포함
- `docs/TASK_BACKLOG.md` — shipped task 22번(Web-search history card header badge Playwright smoke coverage)에 `investigation progress summary text when claim_coverage_progress_summary is non-empty` 포함
- `docs/NEXT_STEPS.md` — header-badge contract 문구에 `investigation progress summary text when claim_coverage_progress_summary is non-empty` 포함

## 사용 skill
- `doc-sync`

## 변경 이유
- 커밋 `59e9941`(`test: add progress-summary assertion to header-badge smoke scenario`)로 `e2e/tests/web-smoke.spec.mjs`의 generic header-badge 시나리오가 이미 non-empty `claim_coverage_progress_summary` fixture와 `.meta` `toContainText` assertion을 포함하게 되었고, 이 슬라이스는 직전 `/work` closeout `2026-04-10-history-card-header-badge-progress-summary-smoke-tightening.md`로 canonical truth에 닫힌 상태임
- 그러나 root docs는 shipped contract를 아직 완전히 반영하지 않아 same-family docs drift가 남아 있었음
  - `docs/ACCEPTANCE_CRITERIA.md:1350`은 `79 core browser scenarios`로 표기되어 있었으나, 실제 `rg -n '^test(' e2e/tests/web-smoke.spec.mjs | wc -l`은 `82`
  - `docs/MILESTONES.md:50`, `docs/TASK_BACKLOG.md:36`, `docs/NEXT_STEPS.md:22`의 header-badge contract 문구는 progress-summary 가시성 부분을 빠뜨리고 있었음
- 이 슬라이스는 런타임/테스트 변경 없이 root docs만 현재 shipped contract와 `82` 시나리오 수에 맞게 truth-sync하는 범위임

## 핵심 변경
1. **scenario count 정정** (`docs/ACCEPTANCE_CRITERIA.md:1350`): `Playwright smoke covers 79 core browser scenarios` → `Playwright smoke covers 82 core browser scenarios`
2. **MILESTONES 라인** (`docs/MILESTONES.md:50`): header-badge browser smoke 설명 끝에 `, and investigation progress summary text when \`claim_coverage_progress_summary\` is non-empty` 추가
3. **TASK_BACKLOG 라인** (`docs/TASK_BACKLOG.md:36`): shipped 항목 22번 괄호에 `, investigation progress summary text when \`claim_coverage_progress_summary\` is non-empty` 추가
4. **NEXT_STEPS 라인** (`docs/NEXT_STEPS.md:22`): header-badge contract 문구 끝에 `, and investigation progress summary text when \`claim_coverage_progress_summary\` is non-empty` 추가
5. **재사용 원칙**: README.md:138과 docs/ACCEPTANCE_CRITERIA.md:1366에 이미 있는 progress-summary 문구를 그대로 재사용하여 새 contract 용어를 발명하지 않음

## 검증
이번 라운드 실행:
- `rg -n '^test(' e2e/tests/web-smoke.spec.mjs | wc -l` → `82`
- `rg -n "claim_coverage_progress_summary|header badge" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` → 각 파일의 header-badge 항목이 progress-summary 문구를 포함하는 것을 육안 확인
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` → 출력 없음 (공백 오류 없음)

이번 라운드에서 재실행하지 않음:
- `tests.test_web_app` 전체 unit suite — docs-only 변경이며 런타임 경로 미변경
- Playwright 전체 또는 history-card 계열 family — 직전 `/work`가 이미 해당 isolated scenario rerun 결과를 남겼고 이번 라운드는 docs만 만짐
- `make e2e-test` — browser-visible contract 변경 아님

## 남은 리스크
- root docs는 progress-summary 항목을 다시 반영했지만, 동일 계약을 설명하는 다른 보조 문서(예: report/, plandoc/)에는 이번 라운드에서 따로 손대지 않았음. canonical 우선순위가 root docs이므로 추가 drift가 관찰되면 후속 라운드에서 좁게 닫는 편이 맞음
- 이번 docs truth-sync는 isolated 시나리오 `web-search history card header badges는 answer-mode, verification-strength, source-role trust를 올바르게 렌더링합니다`에만 직접 연결되어 있으므로, broader header-badge family drift는 독립적으로 재확인하지 않았음
