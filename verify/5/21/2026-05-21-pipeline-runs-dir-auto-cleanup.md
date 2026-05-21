# verify: 2026-05-21 pipeline runs dir auto cleanup

## 대상 work
`work/5/21/2026-05-21-pipeline-runs-dir-auto-cleanup.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py | PASS |
| `unittest` supervisor 193개 테스트 | PASS (1.040s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| 항목 | 위치 | 내용 | 확인 |
|---|---|---|---|
| `_cleanup_old_runs()` | supervisor.py:2687 | 신규 메서드 — disable env 확인, keep_n 결정, sorted_runs, keep_ids 이중 보호, shutil.rmtree, 이벤트 기록 | ✓ |
| `_launch_runtime()` 호출 | supervisor.py:3019 | `_terminate_repo_watchers()` 직후, `_prepare_runtime_surfaces()` 직전 | ✓ |
| keep_n <= 0 방어 | supervisor.py:2699 | `if keep_n <= 0: keep_n = 10` | ✓ |
| 삭제 성공 후 리스트 추가 | supervisor.py:2719–2724 | `rmtree` 성공 후 `deleted.append()` — 실패 시 `continue` | ✓ |
| 이벤트 payload 제한 | supervisor.py:2729 | `deleted_run_ids: deleted[:20]` — 과도한 payload 방지 | ✓ |

## 확인하지 않은 항목

- live runtime start/stop (실제 334개 디렉터리 정리 동작): 현재 환경 미실행
- Playwright / E2E: 변경 없음

## 현재 shipped truth

- supervisor 기동(`_launch_runtime`) 시 `.pipeline/runs/` 오래된 런 자동 정리
- `self.run_id` + `current_run.json` run_id + 최신 10개 보존
- `PIPELINE_RUNTIME_DISABLE_RUNS_CLEANUP=1` 로 비활성화 가능
- `PIPELINE_RUNTIME_KEEP_RECENT_RUNS=N` 으로 보존 개수 조정 가능
- 삭제 없을 때 이벤트 미기록 (노이즈 없음)

## 남은 리스크

- 현재 쌓인 334개는 다음 supervisor 기동 시 자동 정리됨 (별도 수동 작업 불필요)
- commit/push/PR/merge/publish 미실행 상태 유지
