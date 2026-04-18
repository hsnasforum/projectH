# 2026-04-18 fingerprint family 종료 및 cleanup 축 전환 권고

## 배경
- `process_starttime_fingerprint`에 3단계 fallback(`/proc/<pid>/stat`, `ps -p <pid> -o lstart=`, `/proc/<pid>` ctime) 구현 및 검증이 완료되었습니다.
- 현재 tree의 regression tests는 이 세 가지 경로를 end-to-end로 보호하고 있으며, `/proc`이 없는 호스트에서의 safe-degradation 계약도 명확히 고정되었습니다.
- Codex는 다음 단계로 "Watcher-owned identity file" 추가와 "가족 종료 및 축 전환" 사이에서 arbitration을 요청했습니다.

## Gemini 판단 및 권고
- **판단 우선순위:** `GEMINI.md` 기준 `current-risk reduction` (Priority 1)은 현재 설계 범위 내에서 충분히 달성되었습니다. 다음 단계인 "Watcher-owned identity"는 `new quality axis` (Priority 3)에 해당하지만, 현재 document-first MVP의 내부 운영 도구 수준에서는 투자 대비 효용이 낮습니다.
- **권고 사항:** **`fingerprint` family를 여기서 닫고(close), 파이프라인 운영 안정성을 위한 `pipeline-state-cleanup` 축으로 전환**할 것을 권고합니다.
- **이유:**
    - `fingerprint` family는 오늘 이미 2회의 구현 라운드를 거쳐 충분히 성숙했습니다.
    - `.pipeline/` 디렉토리에 stale `live-smoke-*` 및 `live-arb-smoke-*` 디렉토리가 쌓여 있어 `git status` 및 자동화 조사(glob/find) 시 노이즈를 유발하고 있습니다.
    - 이는 `internal cleanup` (Priority 4)에 해당하지만, 현재 family의 risk가 해소된 상태에서 워크스페이스의 "truthful baseline"을 유지하기 위해 가장 적절한 다음 슬라이스입니다.

## 권고 슬라이스: `Archive stale live-smoke and live-arb-smoke directories in .pipeline`
- **구현 범위:**
    - `.pipeline/` 내의 `live-smoke-*`, `live-blocked-smoke-*`, `live-arb-smoke-*` 디렉토리를 찾아 `archive-stale-control-slots.sh`와 유사한 방식으로 처리하거나 삭제하는 좁은 정리 작업.
    - 가능하다면 `pipeline_runtime/schema.py`나 관련 툴에 이런 stale artifact를 감지하고 경고하거나 정리하는 규칙을 짧게 추가.
- **검증 범위:**
    - `.pipeline/` 디렉토리 구조가 깨끗해졌는지 확인.
    - 기존 `archive-stale-control-slots.sh` 등 정리 스크립트와의 충돌 여부 확인.
- **주의 사항:**
    - 현재 진행 중인 `live-*` 디렉토리가 있다면 제외할 것 (mtime 기준 필터링 권장).
    - `git status` 노이즈를 줄이는 데 집중할 것.
