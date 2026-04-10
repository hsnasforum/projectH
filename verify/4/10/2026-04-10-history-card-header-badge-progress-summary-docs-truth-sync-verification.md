# history-card header-badge progress-summary docs truth-sync verification

## 변경 파일
- `verify/4/10/2026-04-10-history-card-header-badge-progress-summary-docs-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/10/2026-04-10-history-card-header-badge-progress-summary-docs-truth-sync.md`가 현재 코드와 root docs truth를 정직하게 설명하는지 다시 확인해야 했습니다.
- 동시에 docs-only truth-sync 다음 라운드를 또 다른 docs micro-sync가 아니라 한 개의 exact current-risk reduction slice로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work` closeout은 현재도 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs:1113`과 `e2e/tests/web-smoke.spec.mjs:1166-1168`에는 non-empty `claim_coverage_progress_summary` fixture와 표시 assertion이 있습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1350`, `docs/MILESTONES.md:50`, `docs/TASK_BACKLOG.md:36`, `docs/NEXT_STEPS.md:22`는 모두 현재 header-badge smoke contract와 `82` scenario count를 반영합니다.
- 이번 라운드의 최소 검증도 `/work` 주장과 일치합니다.
  - `git diff --check`는 대상 docs와 `/work` note에 공백 오류를 보고하지 않았습니다.
  - `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l`은 현재도 `82`입니다.
  - docs/README 검색 결과도 progress-summary wording이 현재 smoke contract와 맞습니다.
- 다음 exact slice는 broad investigation-quality work가 아니라 same-family current-risk reduction이 맞습니다.
  - `app/static/app.js:2962-2965`는 `claim_coverage_progress_summary`를 trim한 뒤 non-empty일 때만 history-card meta에 렌더링합니다.
  - 그러나 generic header-badge smoke는 empty summary를 가진 card 2~4가 실제로 summary text를 렌더링하지 않는다는 negative assertion을 아직 잠그지 않았습니다.
  - 따라서 `CONTROL_SEQ: 19`의 가장 작은 truthful next slice는 `web-search history card header badges` 시나리오에서 empty `claim_coverage_progress_summary` 부재를 명시적으로 검증하는 smoke tightening입니다.

## 검증
- `git status --short`
- `find work/4/10 -maxdepth 1 -type f | sort`
- `find verify/4/10 -maxdepth 1 -type f | sort`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md work/4/10/2026-04-10-history-card-header-badge-progress-summary-docs-truth-sync.md`
- `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l`
- `rg -n "claim_coverage_progress_summary|header badge" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1108,1202p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1347,1367p'`
- `nl -ba docs/MILESTONES.md | sed -n '48,50p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '34,36p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '21,22p'`
- `nl -ba core/agent_loop.py | sed -n '6053,6064p'`
- `nl -ba app/static/app.js | sed -n '2954,2965p'`
- broader unit/Playwright rerun은 하지 않았습니다. latest `/work`가 docs-only round였고, 현재 검증 목적은 docs/code direct comparison과 diff hygiene 확인이었기 때문입니다.

## 남은 리스크
- 현재 header-badge smoke는 non-empty progress-summary positive path는 잠그지만, empty summary hidden path는 아직 직접 잠그지 못합니다.
- repo에 unrelated local changes가 많아서 다음 라운드는 `app.web` history-card smoke 범위를 넘기지 않는 편이 안전합니다.
- 이번 verify는 docs-only closeout truth 확인 범위이므로 broader Milestone 4 후보들(가중치 조정, slot reinvestigation 강화 등)은 새 evidence 없이 다음 slice로 승격하지 않았습니다.
