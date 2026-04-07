## 변경 파일
- `verify/4/7/2026-04-07-latest-update-noisy-community-docs-next-steps-family-closure-truth-sync-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `latest-update noisy-community docs-next-steps family-closure truth-sync tightening` 주장이 현재 트리와 docs-only focused verification 결과에 맞는지 다시 확인하고, 같은 root-summary truth-sync family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`가 말한 changed-file 범위는 현재 트리와 일치했습니다. [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 이제 latest-update noisy community source exclusion에 `full natural-reload + click-reload follow-up/second-follow-up chain exclusion`과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention을 함께 적고 있습니다. `git diff --check -- docs/NEXT_STEPS.md`도 clean이었습니다.
- docs-only verification 범위 자체도 통과했습니다. `rg`로 `docs/NEXT_STEPS.md` 안의 `보조 커뮤니티`, `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`, `follow-up`, `second-follow-up` 반영을 다시 확인했습니다.
- 다만 latest `/work`의 family-complete 문구는 아직 과장입니다. later docs인 [`README.md`](/home/xpdlqj/code/projectH/README.md#L178)부터 [`README.md`](/home/xpdlqj/code/projectH/README.md#L181), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1387)부터 [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1390), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L93)부터 [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L94), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L85)부터 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L88)까지는 noisy-community family를 `보조 커뮤니티`, `brunch` 미노출과 positive retention으로 explicit하게 적습니다.
- 반대로 root summary인 [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 여전히 `brunch`를 explicit negative anchor로 적지 않고 `noisy content` / generic exclusion 수준에 머뭅니다. 실제 rerun에서도 `brunch` count는 `0`이었습니다. 따라서 latest `/work`의 “latest-update noisy-community family ... service/browser/docs(root summary 포함) 모두 truth-sync 완료” 문구는 아직 과장입니다.
- 그래서 현재 truthful closure는 `latest-update noisy-community docs-next-steps family-closure tightening 일부 반영`까지로 정리했고, 다음 단일 슬라이스는 `latest-update noisy-community docs-next-steps exact negative-anchor truth-sync completion`으로 고정했습니다. 목표는 `docs/NEXT_STEPS.md:16` 한 곳에서 later docs와 동일하게 `brunch`까지 explicit negative anchor로 드러내, root summary도 noisy-community family closure truth를 토큰 수준에서 따라가게 하는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-latest-update-noisy-community-docs-next-steps-family-closure-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-family-closure-truth-sync-tightening-verification.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n "latest-update noisy community source|history-card latest-update noisy community source|보조 커뮤니티|brunch|follow-up|second-follow-up|hankyung\\.com|mk\\.co\\.kr|기사 교차 확인|보조 기사" docs/NEXT_STEPS.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `printf "보조 커뮤니티 count: "; rg -o "보조 커뮤니티" docs/NEXT_STEPS.md | wc -l`
- `printf "brunch count: "; rg -o "brunch" docs/NEXT_STEPS.md | wc -l`
- `nl -ba README.md | sed -n '178,181p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1387,1390p'`
- `nl -ba docs/MILESTONES.md | sed -n '93,94p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,88p'`
- `git diff --check -- docs/NEXT_STEPS.md`

## 남은 리스크
- latest `/work`의 changed-file와 broad family wording 반영은 맞았지만, root summary가 later docs처럼 `brunch`를 explicit negative anchor로 적지 않아 family-complete claim은 아직 과장입니다.
- same root-summary truth-sync axis에서 `latest-update noisy-community` family는 `docs/NEXT_STEPS.md` 한 줄만 더 다듬으면 later docs와 토큰 수준으로 맞출 수 있습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 `docs/NEXT_STEPS.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
