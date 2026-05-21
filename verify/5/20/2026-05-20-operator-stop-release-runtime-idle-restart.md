STATUS: verified
WORK: work/5/20/2026-05-20-operator-stop-release-runtime-idle-restart.md
CONTROL_SEQ: none

# 검증 기록

## 요약

사용자의 명시적 진행 지시에 따라 `.pipeline/operator_request.md#2031`
`safety_stop`을 해제하고, 남아 있던 control slot을 archive한 뒤 runtime을
새 코드로 재시작했습니다. 검증 시점의 정상 목표는 새 작업 dispatch가 아니라
`RUNNING + IDLE + active control 없음`입니다.

## 변경 파일

- `.pipeline/archive/2026-05-20/implement_handoff.20260520-193051.md`
- `.pipeline/archive/2026-05-20/advisory_request.20260520-193718.md`
- `.pipeline/archive/2026-05-20/advisory_advice.20260512-184247.md`
- `.pipeline/archive/2026-05-20/operator_request.20260520-193717-released-by-operator.md`
- `.pipeline/archive/2026-05-20/operator_request.20260520-193717-released-by-operator.md.sha256`
- `.pipeline/archive/2026-05-20/archive-manifest.jsonl`
- `work/5/20/2026-05-20-operator-stop-release-runtime-idle-restart.md`
- `verify/5/20/2026-05-20-operator-stop-release-runtime-idle-restart.md`

## 확인한 대상

- `.pipeline` control slot 파일 존재 여부
- `pipeline_runtime.schema.parse_control_slots(Path(".pipeline"))`
- `.pipeline/archive/2026-05-20/archive-manifest.jsonl`
- `.pipeline/runs/20260520T105522Z-p292849/events.jsonl`
- `python3 -m pipeline_runtime.cli doctor . --json`
- `python3 -m pipeline_runtime.cli status . --json`

## 실행한 검증

- `python3 -m pipeline_runtime.cli doctor . --json`
  - 결과: PASS. summary `fail=0`, `warn=0`, `ok=13`.
- `PIPELINE_ARCHIVE_DRY_RUN=1 bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: stale control 3개 archive 대상과 protected operator stop을 확인했습니다.
- `python3 -m pipeline_runtime.cli stop .`
  - 결과: PASS. runtime status가 `STOPPED`로 내려갔습니다.
- `bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: `implement_handoff.md`, `advisory_request.md`, `advisory_advice.md` archive 완료.
- active `.pipeline/operator_request.md#2031` 별도 archive
  - 결과: `.pipeline/archive/2026-05-20/operator_request.20260520-193717-released-by-operator.md`와 `.sha256` sidecar 생성.
- `python3 - <<'PY' ... parse_control_slots(Path('.pipeline')) ... PY`
  - 결과: `{'active': None, 'stale': []}`.
- `python3 -m pipeline_runtime.cli start . --no-attach`
  - 결과: PASS.
- `sleep 3 && python3 -m pipeline_runtime.cli status . --json`
  - 결과: `runtime_state=RUNNING`, `turn_state=IDLE`, `automation_health=ok`,
    `automation_next_action=continue`, `compat.control_slots.active=null`,
    `compat.control_slots.stale=[]`, `watcher.alive=true`.

## 실행하지 않은 검증

- Playwright/e2e, broad unit, long soak
  - 이유: 이번 라운드는 product/browser behavior 변경이 아니라 operator stop 해제와 runtime idle 복구입니다.
- commit, push, PR, merge, release
  - 이유: 현 라운드 범위 밖이며 publication boundary입니다.

## 판정

- `#2031 safety_stop`은 해제되어 archive에 보존됐습니다.
- `.pipeline`의 active/stale control queue는 비었습니다.
- runtime은 새 run에서 살아 있고 watcher도 alive입니다.
- 정상 복구 기준은 `RUNNING + IDLE + automation_health=ok`로 충족됐습니다.

## 남은 리스크

- 자동 구현 작업을 이어 가는 control은 의도적으로 만들지 않았습니다.
- dirty worktree는 여전히 큽니다.
- 이후 새 작업을 진행하려면 새 handoff나 사용자 직접 작업 지시가 필요합니다.
