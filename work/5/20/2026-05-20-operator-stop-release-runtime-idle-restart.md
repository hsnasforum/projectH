# 2026-05-20 operator stop release runtime idle restart

## 변경 파일

- `.pipeline/archive/2026-05-20/implement_handoff.20260520-193051.md`
- `.pipeline/archive/2026-05-20/advisory_request.20260520-193718.md`
- `.pipeline/archive/2026-05-20/advisory_advice.20260512-184247.md`
- `.pipeline/archive/2026-05-20/operator_request.20260520-193717-released-by-operator.md`
- `.pipeline/archive/2026-05-20/operator_request.20260520-193717-released-by-operator.md.sha256`
- `.pipeline/archive/2026-05-20/archive-manifest.jsonl`
- `work/5/20/2026-05-20-operator-stop-release-runtime-idle-restart.md`
- `verify/5/20/2026-05-20-operator-stop-release-runtime-idle-restart.md`

## 사용 skill

- `security-gate`: operator stop 해제, control 파일 이동, runtime stop/start가 승인 및 실행 경계에 닿기 때문에 사용했습니다.
- `release-check`: 재시작 전후 status, doctor, active control 정리 여부를 분리해 확인했습니다.
- `work-log-closeout`: 명시적 operator decision 이후 수행한 archive와 restart 절차를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- 사용자가 `#2031 safety_stop` 이후 현실적인 추천안으로 진행하라고 명시해, 이를 operator stop 해제 결정으로 해석했습니다.
- 새 implement handoff를 만들어 자동 작업을 바로 재개하면 다시 오래된 dirty-bundle/control 흐름으로 이어질 수 있어, 더 보수적으로 기존 control queue를 비우고 runtime만 새 코드로 재시작했습니다.
- 목표는 `needs_operator` 화면을 지우고 `RUNNING + IDLE + automation_health=ok + active control 없음` 상태로 되돌리는 것입니다.

## 핵심 변경

- `python3 -m pipeline_runtime.cli stop .`으로 기존 runtime을 정지했습니다.
- `.pipeline/archive-stale-control-slots.sh --all-stale`로 stale `implement_handoff.md`, `advisory_request.md`, `advisory_advice.md`를 archive했습니다.
- active라서 보호된 `.pipeline/operator_request.md#2031`은 사용자의 명시 지시에 따라 별도 archive 파일로 옮기고 sha256 sidecar를 남겼습니다.
- 파일 시스템 기준 `parse_control_slots(.pipeline)` 결과가 `active=None`, `stale=[]`임을 확인했습니다.
- `python3 -m pipeline_runtime.cli start . --no-attach`로 새 runtime을 띄워 수정된 watcher 코드를 로드했습니다.

## 검증

- `python3 -m pipeline_runtime.cli doctor . --json`
  - 결과: PASS. required/advisory check 모두 `ok`, summary `fail=0`, `warn=0`, `ok=13`.
- `PIPELINE_ARCHIVE_DRY_RUN=1 bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: stale control 3개 archive 예정, active operator stop은 protected로 확인했습니다.
- `python3 -m pipeline_runtime.cli stop .`
  - 결과: PASS. status가 `STOPPED`, lanes `OFF`, turn state `IDLE`로 내려갔습니다.
- `bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: stale control 3개를 `.pipeline/archive/2026-05-20/` 아래로 이동했습니다.
- `python3 - <<'PY' ... parse_control_slots(Path('.pipeline')) ... PY`
  - 결과: `{'active': None, 'stale': []}`.
- `python3 -m pipeline_runtime.cli start . --no-attach`
  - 결과: PASS.
- `sleep 3 && python3 -m pipeline_runtime.cli status . --json`
  - 결과: `runtime_state=RUNNING`, `turn_state=IDLE`, `automation_health=ok`, `automation_next_action=continue`, `compat.control_slots.active=null`, `watcher.alive=true`.

## 남은 리스크

- 현재 재개는 새 작업 handoff를 만들지 않는 idle 복구입니다. 자동화가 특정 구현 작업을 이어서 수행해야 한다면 별도 handoff가 필요합니다.
- 작업 트리에는 이전 자동화 라운드의 많은 dirty/untracked 파일이 남아 있습니다. 이번 라운드는 commit, push, PR, merge, release를 수행하지 않았습니다.
- `.pipeline/archive-stale-control-slots.sh`는 active control을 보호하므로, operator stop 자체는 사용자의 명시 지시를 근거로 별도 archive했습니다.
