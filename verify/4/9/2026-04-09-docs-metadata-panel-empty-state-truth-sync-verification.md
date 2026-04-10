# Docs metadata panel empty-state truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-metadata-panel-empty-state-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-metadata-panel-empty-state-truth-sync.md`가 직전 verification note가 고정한 response payload metadata/panel empty-state drift를 실제로 닫았는지 다시 확인하고, 같은 top-level response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-control-list-field-default-empty-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:312-315`는 이제 `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`를 각각 `default []` 또는 `default ""` 기준으로 직접 설명합니다.
  - 이 문구는 shipped top-level response payload contract와 맞습니다.
    - response model은 `evidence`, `summary_chunks`, `claim_coverage`를 list default로 고정하고, `claim_coverage_progress_summary`는 nullable internal field로 둡니다 (`core/agent_loop.py:81-84`).
    - top-level serializer는 세 panel list 필드를 `[]` 기반으로 직렬화하고, `claim_coverage_progress_summary`는 빈 값일 때 `""`로 내립니다 (`app/serializers.py:55-65`, `app/serializers.py:895-962`).
    - shell은 response/session 렌더링에서 세 list 필드를 `[]`, progress summary를 `""` 폴백으로 소비합니다 (`app/static/app.js:3159-3178`, `app/static/app.js:3205-3211`).
    - focused tests도 payload shape를 잠급니다 (`tests/test_web_app.py:4492-4501`, `tests/test_web_app.py:5413`).
- 이로써 `PRODUCT_SPEC`의 top-level response payload metadata/panel empty-state drift는 닫혔습니다.
- 같은 top-level response payload family 안의 다음 smallest coherent current-risk reduction은 `ARCHITECTURE` + `ACCEPTANCE_CRITERIA` sync입니다.
  - `docs/ARCHITECTURE.md:157-160`은 현재 top-level response payload table에서 `evidence`, `summary_chunks`, `claim_coverage`, `claim_coverage_progress_summary`를 generic `list` / `string`로만 적고 있어 empty-state truth를 직접 드러내지 않습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:119`도 top-level response payload metadata fields를 재열거하지만 `[]` / `""` empty-state를 직접 적지 않습니다.
  - 반면 nested/per-message shape sections는 이미 separate truth를 가지고 있으므로, 다음 slice는 top-level response payload wording만 좁게 sync하는 편이 가장 방어적입니다 (`docs/ARCHITECTURE.md:206-209`).
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE ACCEPTANCE_CRITERIA response payload metadata panel empty-state truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-metadata-panel-empty-state-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-control-list-field-default-empty-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '307,316p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '136,170p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '92,121p'`
- `nl -ba core/agent_loop.py | sed -n '81,85p'`
- `nl -ba app/serializers.py | sed -n '55,65p'`
- `nl -ba app/serializers.py | sed -n '895,962p'`
- `nl -ba app/static/app.js | sed -n '3158,3211p'`
- `nl -ba tests/test_web_app.py | sed -n '4490,4501p'`
- `nl -ba tests/test_web_app.py | sed -n '5408,5414p'`
- `rg -n 'response payload|Metadata fields|claim_coverage_progress_summary|summary_chunks|evidence|claim_coverage' docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'default `\\[\\]`|default \"\"|never `null`|empty-state' docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -1 verify/4/9 | tail -n 12`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- `PRODUCT_SPEC`는 닫혔지만, 같은 top-level response payload metadata/panel empty-state truth가 `docs/ARCHITECTURE.md`와 `docs/ACCEPTANCE_CRITERIA.md`에는 아직 직접 반영되지 않았습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
