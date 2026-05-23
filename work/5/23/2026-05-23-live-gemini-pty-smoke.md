# 2026-05-23 live Gemini PTY smoke 준비

## 변경 파일
- `.pipeline/config/runtime_policy.json`
- `work/5/23/2026-05-23-live-gemini-pty-smoke.md`

## 사용 skill
- `security-gate`: `pty_pilot_lane` 활성화가 runtime control 및 PTY subprocess shell execution 경로에 영향을 주므로, 기본 위험과 rollback 경계를 확인했습니다.
- `work-log-closeout`: 코드 변경 없는 runtime-policy 활성화와 사용자가 파이프라인 재시작 후 관찰할 항목을 `/work` closeout으로 기록했습니다.

## 변경 이유
- CONTROL_SEQ 2160 지시에 따라 Step 10 live Gemini PTY smoke를 준비하기 위해 `.pipeline/config/runtime_policy.json`의 `pty_pilot_lane`을 `"Gemini"`으로 설정했습니다.
- 이번 라운드는 smoke 실행 전 준비 단계입니다. Codex는 파이프라인을 재시작하거나 live Gemini PTY smoke를 직접 실행하지 않습니다.
- 파이프라인 재시작 뒤 실제 Gemini PTY 경로가 등록되는지, 실패 시 tmux fallback/기존 cycle이 유지되는지를 관찰해야 합니다.
- 이 노트는 재시작 전 관찰 가이드이며, 재시작 후 결과를 같은 기준으로 기록할 결과 슬롯 역할도 합니다.

## 핵심 변경
- `.pipeline/config/runtime_policy.json`의 `"pty_pilot_lane"` 값을 `""`에서 `"Gemini"`으로 변경했습니다.
- 코드 파일은 수정하지 않았습니다.
- live smoke 관찰 항목과 사전 로컬 검증 명령을 이 closeout에 고정했습니다.

## 관찰 대상 (파이프라인 재시작 후)
- `events.jsonl`에서 `pty_pilot_lane_register` 이벤트 발생 여부를 확인합니다.
  - 핸드오프 관찰 기준: `source=watcher`, `payload.lane="Gemini"`, `payload.result=registered|failed`
  - 현재 `watcher_core.py` 구현상 직접 기록되는 필드: `payload.lane="Gemini"`, `payload.registered=true|false`, `payload.policy_source="runtime_policy.json"`
- `status.json`의 `profile_adoption.state`가 `current`로 유지되는지 확인합니다.
- Gemini PTY lane의 health dict가 `alive`, `pid`, `exit_code` 키를 포함하는 형태인지 확인합니다.
- watcher log에 `PtyLane` spawn 관련 오류가 없는지 확인합니다.
- 기존 Codex implement / Claude verify 사이클 회귀가 없는지 확인합니다.
  - 기대 관찰: `TASK_DONE source=wrapper lane=Codex` 및 `TASK_DONE source=wrapper lane=Claude` 정상 발행
- `gemini` binary가 없을 때 fail-open 동작을 확인합니다.
  - 기대 흐름: bridge 등록 실패 -> tmux 경로 fallback -> watcher 정상 가동 유지

## 검증
- 통과: `python3 -m json.tool .pipeline/config/runtime_policy.json`
- 통과: `python3 -c "import json; d=json.load(open('.pipeline/config/runtime_policy.json')); assert d['pty_pilot_lane']=='Gemini'; print('pty_pilot_lane OK')"`
  - 결과: `pty_pilot_lane OK`
- 통과: `git diff --check -- .pipeline/config/runtime_policy.json`

## 남은 리스크
- 파이프라인 재시작과 live Gemini PTY smoke는 아직 실행하지 않았습니다. 사용자가 재시작 후 관찰 결과를 보고해야 합니다.
- `pty_pilot_lane: "Gemini"`은 Gemini target에만 PTY bridge를 활성화하는 runtime policy 변경입니다. 문제가 있으면 값을 `""`로 되돌리면 기존 tmux 경로로 복귀합니다.
- Codex/Claude implement/verify lane PTY 전환은 이번 범위 밖입니다.
- commit, push, PR, merge, release는 실행하지 않았습니다.
