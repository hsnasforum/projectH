# 2026-03-31 needs_operator reason requirement sync

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md`
- `verify/README.md`
- `.pipeline/README.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `doc-sync`: single-Codex handoff 규칙 변경을 관련 운영 문서에 같이 반영하기 위해 사용했습니다.
- `work-log-closeout`: 이번 operator-rule 변경을 `/work` closeout 형식에 맞춰 정리하기 위해 사용했습니다.

## 변경 이유
- `STATUS: needs_operator`가 bare stop line 한 줄만 남는 상태면 watcher 제어 신호로는 충분해도, 사람이 나중에 왜 멈췄는지와 무엇을 다시 결정해야 하는지 복원하기 어려웠습니다.
- single-Codex 흐름에서는 Claude가 slice를 고르지 않아야 하므로, `needs_operator`일 때도 stop reason과 operator next step이 반드시 남는 쪽이 더 truthful합니다.
- 현재 `.pipeline/codex_feedback.md`도 `STATUS: needs_operator`만 남아 있어 최신 `/work`·`/verify` 근거를 같이 적는 편이 운영상 더 안전했습니다.

## 핵심 변경
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`에 `STATUS: needs_operator`는 bare stop line으로 두지 않고, stop reason / latest `/work`·`/verify` 근거 / operator next decision을 함께 남기도록 규칙을 추가했습니다.
- `work/README.md`, `verify/README.md`, `.pipeline/README.md`에 같은 규칙을 반영해 handoff 문서와 rolling slot 문서의 기대 형식을 맞췄습니다.
- `.pipeline/README.md`에 최소 `needs_operator` 예시 블록을 추가했습니다.
- 현재 `.pipeline/codex_feedback.md`를 최신 pair 기준 설명형 stop handoff로 다시 채웠습니다.

## 검증
- `rg -n "STATUS: needs_operator|needs_operator" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md .pipeline/README.md .pipeline/codex_feedback.md`
- `sed -n '1,220p' .pipeline/codex_feedback.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- `sed -n '1,220p' CLAUDE.md`
- `sed -n '1,200p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `ls -1t work/3/31 | head -n 8`
- `ls -1t verify/3/31 | head -n 8`
- `sed -n '1,220p' work/3/31/2026-03-31-acceptance-criteria-metadata-sync.md`
- `sed -n '1,220p' verify/3/31/2026-03-31-acceptance-criteria-metadata-sync-verification.md`
- `rg -n 'bare stop line|stop reason|operator가 다음에 무엇을 정해야|STATUS: needs_operator' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md work/README.md verify/README.md .pipeline/README.md .pipeline/codex_feedback.md`
- `git diff --check`

## 남은 리스크
- `pipeline-watcher-v3.sh` 쪽 분기 로직은 이번 라운드에서 건드리지 않았으므로, 사용자님이 이미 맞춘 `STATUS` 해석과 계속 일치하는지 실운영에서 한 번 더 확인이 필요합니다.
- 현재 worktree에는 이번 라운드와 무관한 dirty files가 넓게 섞여 있으므로, 이후 operator-rule 변경이나 handoff 파일 갱신 시 범위를 더 엄격하게 확인해야 합니다.
