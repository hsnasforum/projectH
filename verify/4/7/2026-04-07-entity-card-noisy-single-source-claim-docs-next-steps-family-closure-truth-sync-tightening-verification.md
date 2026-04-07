## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-family-closure-truth-sync-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim docs-next-steps family-closure truth-sync tightening` 주장이 현재 트리와 docs-only focused verification 결과에 맞는지 다시 확인하고, 같은 root-summary truth-sync family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`가 말한 changed-file 범위는 현재 트리와 일치했습니다. [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 이제 history-card entity-card noisy single-source claim에 대해 `설명형 다중 출처 합의`, `출시일` / `2025` / `blog.example.com` 본문·origin detail 미노출, `blog.example.com` provenance in context box, 그리고 click-reload / natural-reload follow-up·second-follow-up chain provenance truth-sync까지 root summary에 적고 있습니다. entity-card 붉은사막 natural-reload 쪽도 same-family closure wording으로 정리돼 있습니다.
- docs-only verification 범위 자체도 통과했습니다. `rg`로 `docs/NEXT_STEPS.md` 안의 `설명형 다중 출처 합의`, `blog.example.com`, `follow-up`, `second-follow-up` 반영을 다시 확인했고, `git diff --check -- docs/NEXT_STEPS.md`도 clean이었습니다.
- 다만 latest `/work`의 검증 서술 중 하나는 정확하지 않았습니다. `/work`는 `설명형 단일 출처` 잔존이 1건이라고 적었지만, 실제 rerun에서 [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16) 안의 `설명형 단일 출처`는 3건이었습니다. 모두 zero-strong-slot family의 legitimate wording이어서 product truth와는 충돌하지 않지만, count claim 자체는 정직하지 않았습니다.
- current truth 기준으로 entity-card noisy single-source claim family의 root summary drift는 now truthfully 닫혔습니다. later docs인 [`README.md`](/home/xpdlqj/code/projectH/README.md#L182), [`README.md`](/home/xpdlqj/code/projectH/README.md#L185), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L95), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L89)부터 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L92)까지와도 더 이상 `docs/NEXT_STEPS.md`가 어긋나지 않습니다.
- 따라서 다음 단일 슬라이스는 `latest-update noisy-community docs-next-steps family-closure truth-sync tightening`으로 고정했습니다. 이유는 같은 root-summary truth-sync family에서 [`README.md`](/home/xpdlqj/code/projectH/README.md#L178)부터 [`README.md`](/home/xpdlqj/code/projectH/README.md#L181), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1387)부터 [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1390), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L93)부터 [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L94), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L85)부터 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L88)까지는 latest-update noisy-community natural-reload + click-reload follow-up/second-follow-up closure를 explicit하게 닫고 있는데, root summary인 [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 아직 initial noisy exclusion 수준에 머물러 있기 때문입니다.

## 검증
- `git status --short`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-family-closure-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-truth-sync-completion-verification.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n "entity-card noisy single-source claim|follow-up|second-follow-up|blog\\.example\\.com|설명형 다중 출처 합의|설명형 단일 출처" docs/NEXT_STEPS.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -o "설명형 단일 출처|설명형 다중 출처 합의|blog\\.example\\.com|follow-up|second-follow-up" docs/NEXT_STEPS.md`
- `rg -n "설명형 단일 출처" docs/NEXT_STEPS.md`
- `printf "설명형 단일 출처 count: "; rg -o "설명형 단일 출처" docs/NEXT_STEPS.md | wc -l`
- `rg -n "latest-update noisy community source|history-card latest-update noisy community source|보조 커뮤니티|brunch" docs/NEXT_STEPS.md`
- `nl -ba README.md | sed -n '176,181p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1387,1391p'`
- `nl -ba docs/MILESTONES.md | sed -n '93,95p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,88p'`
- `git diff --check -- docs/NEXT_STEPS.md`

## 남은 리스크
- latest `/work`의 changed-file와 root-summary truth-sync 자체는 맞았지만, `설명형 단일 출처` 잔존 개수 1건 주장은 실제 파일 기준 3건이라 verification 디테일이 과장되었습니다.
- same root-summary truth-sync axis에서 latest-update noisy-community family는 still `docs/NEXT_STEPS.md`가 later docs 수준의 follow-up/second-follow-up closure를 요약하지 못합니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 `docs/NEXT_STEPS.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
