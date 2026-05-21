# verify: 2026-05-21 Group B cluster verification roadmap

## 대상 work
`work/5/21/2026-05-21-group-b-cluster-verification-roadmap.md`

## 검증 결과

| 클러스터 | 파일 수 | 판정 |
|---|---:|---|
| 1. 문서 | 10 | **커밋 준비 완료** |
| 2. watcher/verify | 4 | **커밋 준비 완료** |
| 3. app/controller/launcher | 10 | **커밋 준비 완료** |
| 4. 테스트 + e2e | 9 | **Python 테스트 준비 완료 / e2e 판정 불가** |

## 재실행 검증

| 검사 | 결과 |
|---|---|
| 클러스터 1 `diff --check` | PASS |
| 클러스터 2 `py_compile` + `test_watcher_core` 255개 + `diff --check` | PASS |
| 클러스터 3 `py_compile` + `test_controller_server` + `test_http_integration` 84개 + `diff --check` | PASS |
| 클러스터 4 `py_compile` + `test_pipeline_runtime_control_writers` + `test_pipeline_launcher` 45개 + `diff --check` | PASS |
| 클러스터 4 e2e (Playwright) | 미실행 — live server 필요 |

## 클러스터 4 분리 권고

Python 테스트 7개 파일과 e2e 스펙 2개 파일을 분리하면 e2e 미검증 부담 없이 커밋 가능:

- **4-A** (Python 테스트, 즉시 커밋 가능):
  `tests/test_controller_server.py`, `tests/test_http_integration.py`,
  `tests/test_pipeline_launcher.py`, `tests/test_pipeline_runtime_control_writers.py`,
  `tests/test_smoke.py`, `tests/test_watcher_core.py`, `tests/test_web_app.py`

- **4-B** (e2e 스펙, Playwright 검증 후 커밋):
  `e2e/tests/controller-smoke.spec.mjs`, `e2e/tests/web-smoke.spec.mjs`

## 전체 커밋 시퀀스 (operator 실행)

```
Group A  → Cluster 1 → Cluster 2 → Cluster 3 → Cluster 4-A → Cluster 4-B(보류)
```

4-B는 Playwright 실행 환경이 준비되면 별도로 커밋.

## 확인하지 않은 항목

- Playwright / live e2e (클러스터 4-B)
- 각 클러스터 diff 내용 설계 리뷰 (이번 라운드 범위 밖)
- untracked 파일 (work/, verify/, fixtures/ 등 — 이번 분류 대상 밖)
