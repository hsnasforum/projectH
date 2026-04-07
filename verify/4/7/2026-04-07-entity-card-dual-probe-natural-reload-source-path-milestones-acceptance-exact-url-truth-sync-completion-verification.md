## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-milestones-acceptance-exact-url-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-milestones-acceptance-exact-url-truth-sync-completion.md`가 docs-only focused verification 범위에서 truthful한지 다시 확인하고, 같은 entity-card dual-probe natural-reload source-path truth-sync family에서 남은 가장 작은 staged-doc under-spec을 다음 Claude 슬라이스로 고정하기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364)는 이제 generic `pearlabyss.com` dual-probe wording 대신 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` exact URL pair를 직접 적고 있습니다.
- latest `/work`가 주장한 focused 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었고, 대응 문서인 [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L155), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62)와 wording도 일치했습니다.
- 따라서 entity-card dual-probe natural-reload source-path milestones-acceptance exact-url truth-sync completion은 이번 verification 범위에서 truthful하게 닫혔습니다.
- 다음 same-family current-risk는 natural-reload second-follow-up source-path + response-origin continuity staged-doc line의 exact URL under-spec입니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L82), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)는 아직 generic `pearlabyss.com` dual-probe URLs wording에 머물러 있지만, 대응 root truth인 [README.md](/home/xpdlqj/code/projectH/README.md#L164)는 이미 exact boardNo URL pair와 `WEB`/`설명 카드`/`설명형 다중 출처 합의`/`공식 기반`·`백과 기반` drift prevention을 직접 적고 있습니다.
- 이 under-spec은 `second-follow-up` 한 시나리오를 `TASK_BACKLOG`/`MILESTONES`/`ACCEPTANCE` 세 문서가 함께 반복하는 형태라서, 파일별로 더 쪼개기보다 같은 exact URL pair anchor를 한 번에 맞추는 쪽이 더 작은 coherent current-risk reduction입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-milestones-acceptance-exact-url-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-task-backlog-exact-url-truth-sync-completion-verification.md`
- `git status --short`
- `nl -ba docs/MILESTONES.md | sed -n '70,74p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1365p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '58,64p'`
- `nl -ba README.md | sed -n '152,156p'`
- `git diff --check -- docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "dual-probe|pearlabyss\\.com|boardNo=200|boardNo=300|공식 기반|백과 기반" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba README.md | sed -n '160,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '80,85p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1376p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '70,73p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `sed -n '1,240p' .pipeline/claude_handoff.md`

## 남은 리스크
- initial/follow-up natural-reload source-path staged docs는 이번 verification 범위에서 닫혔지만, second-follow-up natural-reload pair는 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L82), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)에서 아직 generic wording을 유지합니다.
- 다음 라운드는 code/test/runtime 변경 없이 위 3파일 3개 line만 exact URL pair로 맞추는 docs-only truth-sync로 제한하는 편이 안전합니다.
- unrelated dirty worktree가 이미 크므로, 이번에도 범위 밖 파일 정리나 widening은 피해야 합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
