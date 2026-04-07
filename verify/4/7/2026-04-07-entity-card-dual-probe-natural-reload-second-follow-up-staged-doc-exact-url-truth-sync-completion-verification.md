## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-second-follow-up-staged-doc-exact-url-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-second-follow-up-staged-doc-exact-url-truth-sync-completion.md`가 docs-only focused verification 범위에서 truthful한지 다시 확인하고, 같은 entity-card dual-probe natural-reload family에서 남은 root-summary under-spec을 다음 Claude 슬라이스로 고정하기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L82), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)는 이제 generic `pearlabyss.com` dual-probe wording 대신 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` exact URL pair를 직접 적고 있습니다.
- latest `/work`가 주장한 focused 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/TASK_BACKLOG.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었고, 대응 root doc인 [README.md](/home/xpdlqj/code/projectH/README.md#L164)와 wording도 일치했습니다.
- 따라서 entity-card dual-probe natural-reload second-follow-up staged-doc exact-url truth-sync completion은 이번 verification 범위에서 truthful하게 닫혔습니다.
- 다음 same-family current-risk는 [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16) root summary의 dual-probe natural-reload wording under-spec입니다. 현재 line 16은 `entity-card dual-probe browser natural-reload source-path continuity smoke`, `... exact-field smoke`, `... follow-up source-path continuity smoke`, `... follow-up response-origin continuity smoke` 정도만 generic하게 나열하고 있어, initial/follow-up/second-follow-up 전체 chain과 exact boardNo URL pair truth를 끝까지 반영하지 못합니다.
- 반면 대응 root/staged docs는 이미 더 강한 truth를 적고 있습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L155), [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L82), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)는 exact URL pair와 second-follow-up continuity까지 이미 반영하고 있습니다.
- 이 남은 드리프트는 `docs/NEXT_STEPS.md` 한 줄 요약만 current family closure truth를 못 따라오는 형태라서, 같은 family의 가장 작은 coherent current-risk reduction은 `docs/NEXT_STEPS.md` 한 파일에서 natural-reload dual-probe family summary를 exact URL pair + second-follow-up closure까지 truth-sync하는 것입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-second-follow-up-staged-doc-exact-url-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-source-path-milestones-acceptance-exact-url-truth-sync-completion-verification.md`
- `git status --short`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '70,72p'`
- `nl -ba docs/MILESTONES.md | sed -n '81,83p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1372,1374p'`
- `nl -ba README.md | sed -n '163,165p'`
- `git diff --check -- docs/TASK_BACKLOG.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '16p' docs/NEXT_STEPS.md | fold -s -w 220`
- `rg -n "entity-card dual-probe 자연어 reload 후 두 번째 follow-up|second-follow-up dual-probe|dual-probe browser natural-reload second-follow-up|boardNo=200|boardNo=300" README.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md verify/4/7 work/4/7`
- `rg -n "pearlabyss\\.com dual-probe URLs|pearlabyss\\.com/200|pearlabyss\\.com/300|boardNo=200|boardNo=300" docs/TASK_BACKLOG.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md README.md docs/NEXT_STEPS.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`

## 남은 리스크
- entity-card dual-probe natural-reload staged docs는 이번 verification 범위에서 닫혔지만, [docs/NEXT_STEPS.md](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)는 아직 same-family initial/follow-up/second-follow-up closure와 exact boardNo URL pair를 explicit하게 요약하지 않습니다.
- 다음 라운드는 code/test/runtime 변경 없이 `docs/NEXT_STEPS.md` 한 파일의 root summary wording만 current truth에 맞추는 docs-only truth-sync로 제한하는 편이 안전합니다.
- unrelated dirty worktree가 이미 크므로, 이번에도 범위 밖 파일 정리나 widening은 피해야 합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
