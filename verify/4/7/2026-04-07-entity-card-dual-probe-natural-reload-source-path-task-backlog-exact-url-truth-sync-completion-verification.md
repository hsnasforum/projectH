## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-task-backlog-exact-url-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-task-backlog-exact-url-truth-sync-completion.md`가 docs-only focused verification 범위에서 truthful한지 다시 확인하고, 같은 entity-card dual-probe natural-reload source-path truth-sync family에서 남은 가장 작은 문서 under-spec을 다음 Claude 슬라이스로 고정하기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62)는 이제 generic `pearlabyss.com` dual-probe wording 대신 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` exact URL pair를 직접 적고 있습니다.
- latest `/work`가 주장한 focused 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/TASK_BACKLOG.md`는 clean이었고, 대응 root docs인 [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L155)와 current wording도 일치했습니다.
- 따라서 entity-card dual-probe natural-reload source-path task-backlog exact-url truth-sync completion은 이번 verification 범위에서 truthful하게 닫혔습니다.
- 다음 same-family current-risk는 staged docs의 exact URL anchor under-spec입니다. [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364)는 아직 generic `pearlabyss.com` dual-probe URLs wording에 머물러 있어, README와 TASK_BACKLOG가 이미 반영한 exact boardNo URL pair continuity truth보다 약합니다.
- 이 under-spec은 파일별로 따로 쪼개기보다 한 번에 닫는 편이 더 자연스럽습니다. 두 문서는 같은 entity-card dual-probe natural-reload source-path pair를 같은 initial/follow-up 축으로 반복하고 있고, 필요한 수정도 exact URL pair 4개 anchor를 맞추는 동일한 docs-only truth-sync이기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-task-backlog-exact-url-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-task-backlog-browser-truth-sync-completion-verification.md`
- `git status --short`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '58,64p'`
- `nl -ba README.md | sed -n '152,156p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,74p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1365p'`
- `git diff --check -- docs/TASK_BACKLOG.md`
- `rg -n "pearlabyss\\.com|dual-probe URLs|boardNo=200|boardNo=300|dual-probe natural-reload|자연어 reload" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`

## 남은 리스크
- task-backlog pair는 이번 verification 범위에서 닫혔지만, staged docs인 `docs/MILESTONES.md`와 `docs/ACCEPTANCE_CRITERIA.md`에는 같은 family의 generic `dual-probe URLs` wording이 아직 남아 있습니다.
- 다음 라운드는 code/test/runtime 변경 없이 위 2파일 4개 line만 exact URL pair로 맞추는 docs-only truth-sync로 제한하는 편이 안전합니다.
- unrelated dirty worktree가 이미 크므로, 이번에도 범위 밖 파일 정리나 widening은 피해야 합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
