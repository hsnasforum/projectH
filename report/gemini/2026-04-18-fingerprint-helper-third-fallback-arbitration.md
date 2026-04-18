# 2026-04-18 fingerprint helper third fallback arbitration

## 배경
- `process_starttime_fingerprint`는 현재 `/proc/<pid>/stat`(primary)과 `ps -p <pid> -o lstart=`(fallback) 두 가지 source를 사용하며, 최근 라운드에서 이 두 경로에 대한 regression tightening이 완료되었습니다.
- 하지만 BusyBox와 같은 minimal host 환경에서는 `ps` 명령어가 제한적이고 `/proc` 파일 파싱이 어려울 수 있어, fingerprint가 `""`로 safe-degradation 되어 `run_id` 상속이 실패하는 리스크가 여전히 남아 있습니다.
- Codex는 helper 레벨의 세 번째 fallback 추가(same-family current-risk reduction)와 watcher-led identity handshake(new quality axis) 사이에서 결정을 유보하고 arbitration을 요청했습니다.

## Gemini 판단 및 권고
- **판단 우선순위:** `GEMINI.md` 기준 `same-family current-risk reduction` (Priority 1)이 `new quality axis` (Priority 3)보다 우선합니다.
- **권고 사항:** `pipeline_runtime/schema.py` 내의 `process_starttime_fingerprint`에 **`os.stat("/proc/<pid>").st_ctime`을 활용한 세 번째 fallback**을 추가할 것을 권고합니다.
- **이유:**
    - Linux 환경에서 `/proc/<pid>` 디렉토리의 생성 시간은 프로세스 시작 시간을 나타내는 매우 강력하고 이식성 높은 지표입니다.
    - 이는 기존 `watcher_fingerprint` 계약을 유지하면서도 minimal host에서의 리스크를 실질적으로 줄이는 가장 좁고 확실한 슬라이스입니다.
    - "Watcher-led identity" 방식은 설계적으로 견고할 수 있으나, 현재 검증된 supervisor-led 계약을 넓히는 "new quality axis"에 해당하므로 현 단계에서는 helper 강화가 더 적절합니다.

## 권고 슬라이스: `Add os.stat st_ctime third fallback to fingerprint helper`
- **구현 범위:**
    - `pipeline_runtime/schema.py`: `_proc_ctime_fingerprint(pid)` 추가 (`os.stat(f"/proc/{pid}").st_ctime` 사용, int casting 후 string 반환).
    - `pipeline_runtime/schema.py`: `process_starttime_fingerprint`에서 기존 두 source가 모두 실패할 경우 이 helper를 호출하도록 수정.
    - `tests/test_pipeline_runtime_schema.py`: 새로운 fallback 경로에 대한 mock 기반 regression test 추가.
- **검증 범위:**
    - `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py`
    - `python3 -m unittest` (해당 helper 및 regression test 중심의 focused rerun)
- **주의 사항:**
    - 현재 tree의 dirty changes(controller/browser 등)는 그대로 두고 해당 파일만 수정할 것.
    - `st_ctime`은 float이므로 `str(int(ctime))` 형식을 사용하여 안정성을 확보할 것.
