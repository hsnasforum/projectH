# 2026-04-21 commit/push large-bundle policy

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.pipeline/README.md`
- `work/README.md`
- `verify/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/operator_request.md`
- `work/4/21/2026-04-21-commit-push-large-bundle-policy.md`
- `verify/4/21/2026-04-21-no-soak-automation-handoff.md`

## 사용 skill
- `security-gate`: commit/push operator boundary가 작은 local slice의 자동 publish로 번지지 않도록 approval 경계를 확인했습니다.
- `work-log-closeout`: 운영 정책 변경 사실과 실제 검증만 기준으로 closeout을 남겼습니다.

## 변경 이유
- 작은 작업마다 commit/push approval stop이 반복되면 pipeline automation이 operator loop로 빠질 수 있습니다.
- commit/push는 큰 검증 묶음이나 release/soak/PR 경계에서만 다뤄야 하고, 일반 small/local slice는 `/work` closeout과 local dirty state로 남겨야 합니다.

## 핵심 변경
- implement-owner lane은 계속 bounded edits와 `/work` closeout에서 멈추도록 유지했습니다.
- commit/push automation을 operator가 명시 승인한 release, soak, PR stabilization, direct publish bundle 같은 큰 검증 묶음 경계로 제한했습니다.
- Gemini advisory도 일반 small/local slice에는 commit/push recommendation을 내지 않도록 역할 문서에 반영했습니다.
- satisfied commit/push recovery 문서에는 이미 승인돼 끝난 큰 묶음을 인식하는 경로일 뿐, 작은 dirty state를 새 commit/push stop으로 올리라는 뜻이 아니라고 명시했습니다.
- 2026-04-21 현재 operator 방향은 6h/24h synthetic soak를 실행하지 않고 watcher/supervisor/launcher 자동화 안정화 작업에 집중하는 것입니다.
- `.pipeline/operator_request.md` seq 696을 `waiting_next_control` / `internal_only`로 갱신해 seq 695의 `commit/push -> 6h synthetic soak -> PR` 묶음을 supersede하고 verify/handoff follow-up으로 전환했습니다.

## 검증
- `git diff --check -- AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md work/README.md verify/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md .pipeline/operator_request.md work/4/21/2026-04-21-commit-push-large-bundle-policy.md verify/4/21/2026-04-21-no-soak-automation-handoff.md` → 통과
- `python3 -m unittest tests.test_operator_request_schema` → 11 tests OK

## 남은 리스크
- verify/handoff owner는 다음 control을 쓸 때 seq 695의 `commit/push → 6h synthetic soak → PR` 묶음을 current next action으로 유지하지 말고, long soak 없이 자동화 안정화 슬라이스로 좁혀야 합니다.
- tmux Claude pane direct paste는 현재 target이 없어 실패했습니다. 대신 rolling `.pipeline/operator_request.md`에 같은 지시를 canonical control로 남겼습니다.
