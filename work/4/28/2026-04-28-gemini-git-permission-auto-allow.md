# 2026-04-28 Gemini Git Permission Auto Allow

## 변경 파일
- `watcher_dispatch.py`
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/28/2026-04-28-gemini-git-permission-auto-allow.md`

## 사용 skill
- `security-gate`: shell permission prompt 자동 입력이 non-git/write/publication 명령으로 넓어지지 않도록 guard를 좁혔습니다.
- `doc-sync`: watcher runtime 동작 변경을 pipeline README, 기술설계서, RUNBOOK에 반영했습니다.
- `finalize-lite`: 변경 파일, 실제 검증, 남은 리스크를 구현 closeout 기준으로 정리했습니다.
- `work-log-closeout`: 이번 runtime 보완 작업을 `/work` 기록으로 남겼습니다.

## 변경 이유
- Gemini CLI가 `Allow execution of [git]?` permission prompt에서 멈추면 watcher가 lane을 busy/prompt-visible로만 보고 다음 진행을 이어가기 어렵습니다.
- 사용자가 이미지와 같은 read-only `git branch && git log -n 10 --oneline` 확인 prompt가 떠도 진행이 막히지 않게 watcher가 2번(`Allow for this session`)을 선택하도록 요청했습니다.
- 단, `git` permission은 session scope로 열릴 수 있으므로 `git push/reset/checkout/commit` 같은 write/publication 계열은 자동 승인하지 않는 제한이 필요했습니다.

## 핵심 변경
- `watcher_dispatch.py`에 Gemini git permission prompt 판별과 자동 입력 helper를 추가했습니다.
- 자동 입력은 `Allow execution of [git]?`와 `2. Allow for this session`이 함께 보이고, visible `Shell` command가 read-only git 조회 조합일 때만 동작합니다.
- 허용 subcommand를 `branch`, `log`, `status`, `show`, `diff`, `rev-parse` 등 read-only 조회로 제한하고, `git push/reset/checkout/commit` 및 shell redirection/pipe/semicolon은 거부합니다.
- `watcher_core.py` poll 초반에 Gemini pane을 확인해 해당 prompt를 발견하면 `2` + `Enter`를 보내고 `gemini_git_permission_auto_allow_session` runtime event를 남기도록 연결했습니다.
- CLI에는 비활성화 옵션 `--disable-gemini-git-permission-auto-allow`를 추가했습니다.
- 회귀 테스트로 read-only prompt 허용, mutating prompt 거부, tmux `2 Enter` 입력, startup grace 전 처리 순서를 고정했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_dispatch.py watcher_core.py`
- 통과: `python3 -m unittest -v tests.test_watcher_core.CodexDispatchConfirmationTest` (16 tests)
- 통과: `python3 -m unittest -v tests.test_watcher_core` (212 tests)
- 통과: `git diff --check -- watcher_dispatch.py watcher_core.py tests/test_watcher_core.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md .pipeline/README.md`
- 확인: `tmux capture-pane -t aip-projectH:0.2 -p -S -80`에서 기존 Gemini `git branch && git log -n 10 --oneline` prompt가 `✓ Shell ...`로 완료되어 있고 Gemini lane이 ready prompt로 돌아와 있었습니다.
- 확인: `python3 -m pipeline_runtime.cli status --json`에서 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, Gemini lane `READY`, active turn `VERIFY_FOLLOWUP`을 확인했습니다.
- 확인: `.pipeline/logs/experimental/raw.jsonl`에 `gemini_git_permission_auto_allow_session` event가 남았고, `.pipeline/runs/20260428T090011Z-p743890/events.jsonl`에서 watcher self-restart completed 이벤트가 관측되어 live watcher가 새 코드를 적용했습니다.
- 참고: `python3 -m pipeline_runtime.cli status --project-root /home/xpdlqj/code/projectH --json`는 CLI 인자 위치 오류로 실패했고, 올바른 status 명령으로 재확인했습니다.

## 남은 리스크
- 현재 live watcher에는 새 자동 입력 로직이 적용됐고, 기존 Gemini git prompt는 이미 자동 처리되어 재현 블록은 남아 있지 않았습니다. 다만 supervisor self-restart가 없는 수동/테스트 실행에서는 watcher 재시작 후 적용됩니다.
- 자동 입력은 read-only git 조회 prompt에만 적용됩니다. write/publication git 명령은 계속 operator/agent 명시 경계로 남겨야 합니다.
- 전체 browser/E2E와 장기 soak는 실행하지 않았습니다. 이번 변경은 watcher dispatch/poll prompt 처리와 runtime 문서화에 한정했습니다.
