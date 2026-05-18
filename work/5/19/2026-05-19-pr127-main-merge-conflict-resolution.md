# 2026-05-19 PR127 main merge conflict resolution

## 변경 파일

- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `pipeline_runtime/operator_autonomy.py`
- `watcher_dispatch.py`
- `verify/5/19/2026-05-19-release-gate-publication-prep.md`
- `work/5/19/2026-05-19-publish-held-dirty-bundle-freshness-guard.md`
- `work/5/19/2026-05-19-pr127-main-merge-conflict-resolution.md`
- `verify/5/19/2026-05-19-pr127-main-merge-conflict-resolution.md`

## 사용 skill

- `github:yeet`: 이미 승인된 draft PR 브랜치를 `origin/main`과 맞추고 다시 push하는 publish follow-up 흐름에 사용했습니다.

## 변경 이유

- draft PR #127이 `origin/main`과 충돌 상태로 표시되어, 브랜치 병합 가능성을 회복해야 했습니다.
- 충돌은 문서 2곳과 runtime helper 2곳에서 발생했고, 양쪽 변경은 상호 배타적이지 않았습니다.
- 사용자의 `진행` 승인은 commit/push/draft PR 업데이트까지로 해석했고, merge/release/external publication은 계속 별도 operator boundary로 남겼습니다.

## 핵심 변경

- `.pipeline/README.md`와 runbook의 release-gate/operator-autonomy 설명을 양쪽 변경의 합집합으로 정리했습니다.
- `pipeline_runtime/operator_autonomy.py`는 `publish_boundary_accumulated_dirty_tree` 계열 alias와 `mNN_publish_bundle_authorization` alias를 모두 `commit_push_bundle_authorization`으로 정규화하도록 유지했습니다.
- `watcher_dispatch.py`는 Codex stale paste backoff/literal fallback 상수와 Gemini read-only git permission prompt guard 상수를 모두 보존했습니다.
- 직전 publish-held freshness guard `/work`와 해당 `/verify` 추가 기록은 당시의 pre-approval history로 보존했습니다.

## 검증

- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_dispatch.py watcher_core.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 출력 없이 통과했습니다.
- `python3 -m unittest -v tests.test_operator_request_schema tests.test_pipeline_runtime_supervisor tests.test_watcher_core`
  - `Ran 438 tests in 13.230s`, `OK`로 통과했습니다.
- 충돌 표식 확인:
  - `rg -n "<<<<<<<|=======|>>>>>>>" .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md pipeline_runtime/operator_autonomy.py watcher_dispatch.py`
  - 출력 없음.

## 남은 리스크

- 이번 post-merge 라운드에서는 `make e2e-test`, `make controller-test`, Playwright focused rerun, long soak를 다시 실행하지 않았습니다.
- broader gate는 merge 전 이미 `591`개 unittest, `make e2e-test` `184 passed`, `make controller-test` `19 passed`로 통과했지만, 이번 충돌 해소 후에는 runtime/operator/watch 단위 회귀로 범위를 좁혔습니다.
- PR은 draft 상태로 유지합니다. merge/release/external publication은 수행하지 않습니다.
