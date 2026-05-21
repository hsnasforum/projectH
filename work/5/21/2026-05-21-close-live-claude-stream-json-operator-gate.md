# 2026-05-21 close live Claude stream-json operator gate

## 변경 파일
- `.pipeline/operator_request.md` 이동으로 제거
- `.pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md` 신규 archive
- `work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md` 신규 작성
- 이번 라운드에서 코드 파일은 수정하지 않았습니다.

## 사용 skill
- `security-gate`: operator gate 파일 이동이 승인 경계와 archive 추적 경계를 올바르게 닫는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: HOLD 결정, 근거, archive 이동 결과를 `/work`에 기록하기 위해 사용했습니다.

## 변경 이유
- `.pipeline/operator_request.md#2078`는 live Claude stream-json 검증 여부를 operator-only boundary로 세운 gate였습니다.
- 이후 `AUTHORIZE_LIVE_CLAUDE_STREAM_JSON_VALIDATION` 범위의 live 검증에서 Case B가 확인됐습니다.
- `verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`는 #2109 교정이 READY임을 확인했습니다.
- 이번 라운드는 남은 gate를 `HOLD_LIVE_VALIDATION_LOCAL_ONLY` 결정으로 닫고, 활성 operator request 슬롯을 비우는 목적입니다.

## 핵심 변경
- `.pipeline/operator_request.md`를 `.pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md`로 이동했습니다.
- 결정은 `HOLD_LIVE_VALIDATION_LOCAL_ONLY`로 기록합니다.
- 근거는 Case B입니다: tmux PTY 인터랙티브 세션에서 `--output-format stream-json`은 JSONL이 아니라 TUI를 출력합니다.
- 단기 교정은 #2109에서 완료됐습니다: Claude lane 기본 command에서 `--output-format stream-json`을 제거하고 wrapper 초기화를 `jsonl_mode=False`로 고정했습니다.
- 장기 방향은 별도 슬라이스입니다: `claude --print --verbose --output-format stream-json`을 stdin 파이프로 실행하는 wrapper 구조가 필요합니다.

## 검증
- 확인: `.pipeline/operator_request.md` 읽기
  - 결과: `CONTROL_SEQ: 2078`, `REASON_CODE: live_claude_stream_json_validation_boundary`
- 확인: `verify/5/21/2026-05-21-claude-stream-json-flag-revert.md` 읽기
  - 결과: `검증 결과: READY`, Claude command에서 `--output-format` 제거 확인
- 실행: `mkdir -p .pipeline/archive/2026-05-21 && mv .pipeline/operator_request.md .pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md`
- 통과: `test ! -f .pipeline/operator_request.md && echo "gate closed"`
  - 결과: `gate closed`
- 통과: `ls .pipeline/archive/2026-05-21/ | grep operator_request.2078`
  - 결과: `operator_request.2078-hold-live-validation-resolved.md`
- 통과: `git diff --check -- .pipeline/ work/5/21/`

## 남은 리스크
- live Claude stream-json은 local-only hold 상태로 닫았습니다.
- `--print` stdin pipe wrapper 구현은 이번 범위 밖이며, 다음 슬라이스로 자동 선택하지 않았습니다.
- 현재 worktree에는 이전 라운드에서 남은 코드/verify/work dirty 항목이 있습니다. 이번 라운드에서는 operator gate archive와 이 `/work` 기록만 추가했습니다.
- commit, push, PR, merge, publish는 실행하지 않았습니다.
