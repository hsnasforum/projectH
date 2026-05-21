# 2026-05-21 Pane fallback telemetry docs

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/21/2026-05-21-pane-fallback-telemetry-docs.md`

## 사용 skill

- `doc-sync`: `pane_text_fallback_used` telemetry의 운영 해석 기준을 runtime contract와 RUNBOOK에 맞춰 문서화하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `pane_text_fallback_used`는 오류 자체가 아니라 supervisor가 어느 채널을 근거로 상태를 판단했는지 보여주는 observability event입니다.
- 운영 중 이 기준이 흔들리지 않도록, Codex 초기 fallback 허용 범위와 작업 중 fallback 주의 조건을 문서에 고정했습니다.

## 핵심 변경

- `.pipeline/README.md`에 `pane_text_fallback_used`가 failure가 아닌 telemetry라는 runtime contract를 추가했습니다.
- Codex `BOOTING`/`READY` 초기 fallback은 run당 2~4회 수준이면 허용 범위로 보는 기준을 기록했습니다.
- `TASK_ACCEPTED` 이후 반복 fallback 또는 `WORKING` 유지가 pane fallback으로 이어지는 경우를 구조화 출력/bridge 보강 후보로 명시했습니다.
- `05_운영_RUNBOOK.md`에 관찰값 / 해석 / 다음 행동 기준표를 추가했습니다.
- raw pane text 또는 prompt 원문이 event payload에 보이면 privacy/audit boundary 회귀로 즉시 수정해야 한다는 기준을 남겼습니다.

## 검증

- 문서 whitespace 확인:
  - `git diff --check -- .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과했습니다.

## 남은 리스크

- 문서화 라운드라 코드와 테스트는 변경하지 않았습니다.
- live runtime에서 추가 누적 통계 집계 기능은 아직 없습니다. 현재 기준은 `events.jsonl` 관찰과 수동/스크립트 집계로 해석합니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
