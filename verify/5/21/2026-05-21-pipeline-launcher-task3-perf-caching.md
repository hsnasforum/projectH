# verify: 2026-05-21 pipeline launcher Task 3 perf caching

## 대상 work
`work/5/21/2026-05-21-pipeline-launcher-task3-perf-caching.md`

## 검증 결과: READY (Task 3 범위)

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` supervisor.py | PASS |
| `unittest` supervisor 187개 테스트 | PASS (1.098s) |
| `git diff --check` 변경 파일 | PASS |

## 수정 확인 (코드 직접 열람)

| ID | 위치 | 내용 | 확인 |
|---|---|---|---|
| P4 | supervisor.py:212 | `_control_sha_cache: dict[str, tuple[float, str]] = {}` 멤버 | ✓ |
| P4 | supervisor.py:585–603 | `stat().st_mtime` 확인 → 캐시 히트 시 `read_bytes()` 생략 | ✓ |
| P3 | supervisor.py:213–214 | `_duplicate_marker_cache_key`, `_duplicate_marker_cache_result` 멤버 | ✓ |
| P3 | supervisor.py:783–789 | `_cache_result()` 헬퍼로 모든 return 경로 일관 갱신 | ✓ |
| P3 — 누락 경로 | supervisor.py:834 | `return _cache_result(fallback)` — 최종 return도 갱신 | ✓ |
| P3 — 조기 캐시 적중 | supervisor.py:783 | `cache_key == _last` 시 바로 반환, raw.jsonl 미접근 | ✓ |

> 주목: `completed_truth` 분기(artifact truth로 즉시 탐지)는 캐시 키 계산 전에 return하므로
> 캐시를 거치지 않는다. 이 경로는 artifact 파일 변경이 있을 때마다 정확히 재평가되어야
> 하므로 의도적 설계이며 결함 아님.

## 확인하지 않은 항목

- Playwright / E2E / controller-smoke: 변경 없음
- live runtime start/stop: 이번 변경은 supervisor 내부 캐싱만
- Task 4-C/D (P5/P7): 아직 미수정

## 현재 shipped truth (누적)

| 라운드 | 완료 이슈 | 내용 |
|---|---|---|
| Task 1 | P6/P9/P10/P14/P15/P17 | 단순 버그 6건 |
| Task 4-A/B | P1/P2 | raw.jsonl 보존, events.jsonl 중복 억제 |
| Task 2 | P8/P11/P13/P16/P18 | 로직 교정 5건 |
| Task 3 | P3/P4 | SHA/raw.jsonl 캐싱 — 폴 사이클당 I/O 감소 |

## 남은 미수정 이슈

| ID | 태스크 | 내용 |
|---|---|---|
| P5 | Task 4-C | 동시 start 직렬화 (fcntl flock) |
| P7 | Task 4-D | TOCTOU pid 재확인 |

## 다음 슬라이스 권고

**Task 4-C/D (P5/P7)** — 경쟁 조건 마무리. 이것으로 18개 이슈 전체 완료.
P5는 `_spawn_supervisor()`에 `fcntl.flock` 추가가 필요하므로 변경 범위가
앞선 태스크보다 넓다. P7은 `_inherited_run_id_from_live_watcher()` 끝에
pid 재확인 한 줄 추가로 단순하다. 두 건을 묶어 한 라운드에 처리 가능.
