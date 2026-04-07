## 변경 파일
- `verify/4/7/2026-04-07-latest-update-noisy-community-docs-next-steps-exact-negative-anchor-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `latest-update noisy-community docs-next-steps exact negative-anchor truth-sync completion` 주장이 현재 트리와 docs-only focused verification 결과에 맞는지 다시 확인하고, 같은 noisy-community docs truth-sync family에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 이제 history-card latest-update noisy community source exclusion을 `보조 커뮤니티`, `brunch`의 origin detail, response body, context box 미노출로 명시하고, follow-up/second-follow-up chain에서 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 함께 적고 있습니다.
- latest `/work`가 주장한 docs-only 검증 핵심도 현재 트리에서 재현됐습니다. `brunch count`는 `1`이었고, `git diff --check -- docs/NEXT_STEPS.md`도 clean이었습니다.
- 다만 latest `/work`의 “latest-update noisy-community family와 entity-card noisy single-source claim family 모두 root summary 포함 전체 경로에서 truth-sync 완료” 문구는 아직 과장입니다. root summary는 맞아졌지만, same-family initial click-reload contract를 설명하는 staged docs는 아직 partial/stale wording이 남아 있습니다.
- 구체적으로 [`README.md`](/home/xpdlqj/code/projectH/README.md#L133)은 initial noisy-community path를 본문과 origin detail 미노출까지만 적고 context box exclusion을 빠뜨립니다. [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1342)도 같은 수준에 머뭅니다. [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51)과 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L40)은 더 오래된 wording으로 `brunch` explicit anchor와 context box exclusion 대신 generic `noisy content` 표현을 유지합니다.
- 그래서 현재 truthful closure는 `docs/NEXT_STEPS.md` root summary exact negative-anchor completion까지로 정리했고, 다음 단일 슬라이스는 `latest-update noisy-community initial click-reload staged-doc truth-sync completion`으로 고정했습니다. 목표는 initial history-card latest-update noisy-community exclusion truth를 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에서 current wording으로 한 번에 맞추는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-latest-update-noisy-community-docs-next-steps-exact-negative-anchor-truth-sync-completion.md`
- `sed -n '1,240p' verify/4/7/2026-04-07-latest-update-noisy-community-docs-next-steps-family-closure-truth-sync-tightening-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `printf "brunch count: "; rg -o "brunch" docs/NEXT_STEPS.md | wc -l`
- `rg -n "blog\\.example\\.com|source_paths|설명형 다중 출처 합의|latest-update noisy community source exclusion|보조 커뮤니티|brunch" docs/NEXT_STEPS.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '48,52p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '38,41p'`
- `nl -ba README.md | sed -n '131,134p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1340,1344p'`

## 남은 리스크
- root summary인 `docs/NEXT_STEPS.md`는 now truth에 맞지만, same-family initial click-reload docs wording은 아직 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에 분산된 partial/stale 상태입니다.
- 따라서 latest `/work`의 family-wide docs completion 서술은 아직 과장이고, 다음 구현 라운드는 staged docs 네 파일을 함께 맞추는 docs-only slice로 마무리하는 편이 안전합니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 위 네 문서만 건드리고 code/test/runtime 파일은 건드리지 않는 편이 좋습니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
