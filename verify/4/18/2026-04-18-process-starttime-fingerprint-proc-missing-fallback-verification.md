# 2026-04-18 process_starttime_fingerprint /proc-missing fallback verification

## 변경 파일
- `verify/4/18/2026-04-18-process-starttime-fingerprint-proc-missing-fallback-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-process-starttime-fingerprint-proc-missing-fallback.md`가 shared fingerprint helper에 `/proc`-missing fallback을 추가했다고 주장하므로, 그 helper 분기와 supervisor inheritance 경계가 현재 트리에서 실제로 맞는지 다시 확인해야 했습니다.
- 같은 날 기존 `/verify`인 `verify/4/18/2026-04-18-watcher-exporter-current-run-owner-metadata-verification.md`가 지적한 다음 same-family current-risk가 정확히 이 `/proc`-missing fallback이었으므로, 이번 라운드는 그 후속 구현이 truthful한지 닫는 새 verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `pipeline_runtime/schema.py`의 `process_starttime_fingerprint(pid)`가 `_proc_starttime_fingerprint(pid)`를 primary source로, `_ps_lstart_fingerprint(pid)`를 `/proc`-missing fallback source로 순서대로 사용합니다.
  - non-positive pid, `/proc` read failure, `ps` 실행 실패/타임아웃/빈 stdout은 모두 `""`로 정리돼 caller가 "inheritance 불가"로 처리하게 되어 있습니다.
  - `tests/test_pipeline_runtime_schema.py`의 `ProcessStarttimeFingerprintTest`와 `tests/test_pipeline_runtime_supervisor.py`의 `test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`도 `/work` 설명과 일치하게 존재합니다.
  - `.pipeline/README.md`에도 `/proc`이 없을 때 `ps -p <pid> -o lstart=`를 보조 fingerprint로 쓰고, 두 source가 모두 비어 있을 때만 fresh `_make_run_id()`로 fall through 한다는 현재 계약 문장이 들어가 있습니다.
- 이번 verify 라운드에서 실제로 다시 실행한 최소 검증은 모두 통과했습니다.
  - `py_compile`은 `pipeline_runtime/schema.py`, 관련 test 2개에 대해 통과했습니다.
  - focused unittest는 `Ran 8 tests`, `OK`로 통과했고, 새 schema fallback 경계 7개와 supervisor inheritance 1개가 함께 확인됐습니다.
  - `git diff --check`도 대상 파일 경계에서 통과했습니다.
- 다만 next same-family current-risk도 이번 verify에서 하나 분명해졌습니다.
  - `tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest.test_process_starttime_fingerprint_uses_proc_when_available`는 실제 `/proc/<pid>/stat`가 읽히는 호스트를 전제로 합니다.
  - 그래서 이번 Linux verify에서는 통과했지만, 이번 라운드가 열어 둔 `/proc`-missing host에서 같은 회귀 파일을 돌리면 fallback path를 검증하기 전에 test 자체가 흔들릴 수 있습니다.
  - 즉 runtime fallback 구현은 현재 트리에서 truthful하지만, fallback regression의 host portability는 아직 닫히지 않았습니다.
- 현재 worktree가 runtime/controller/docs 쪽으로 넓게 dirty한 상태라, `.pipeline/README.md`는 fallback contract 문장 존재 여부만 대조했습니다. 이 verify note는 README 전체 diff를 이번 `/work` 한 라운드의 단독 변경으로 재귀속하지 않습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.ProcessStarttimeFingerprintTest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_when_fingerprint_helper_uses_ps_fallback`
  - 결과: `Ran 8 tests`, `OK`
- `git diff --check -- pipeline_runtime/schema.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- `/work`에 적힌 broader full-module rerun(`tests.test_pipeline_runtime_schema`, `tests.test_pipeline_runtime_supervisor`, `tests.test_watcher_core`)은 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 code change가 `pipeline_runtime/schema.py` helper와 그 helper를 직접 쓰는 supervisor inheritance regression 1개에 좁게 한정돼 있었기 때문입니다.

## 남은 리스크
- `/proc`-missing fallback 자체는 현재 구현되어 있지만, 새 regression 하나가 여전히 `/proc`-available host를 가정합니다. non-Linux POSIX나 restricted container에서 이 test는 fallback 계약을 검증하기보다 host 전제 때문에 실패할 수 있습니다.
- `ps -p <pid> -o lstart=` 자체를 지원하지 않는 minimal 환경에서는 helper가 여전히 `""`로 safe degradation 합니다. 이번 verify는 그 경계를 regression으로만 확인했고, 더 portable한 third fallback은 아직 없습니다.
- current tree에는 unrelated dirty changes가 많으므로, 다음 Claude 라운드는 이 verify note가 지목한 test portability slice만 다루고 다른 runtime/controller/docs 변경은 건드리지 않는 편이 안전합니다.
