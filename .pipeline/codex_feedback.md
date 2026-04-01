STATUS: implement

완료 슬라이스: `overwrite approval execution only`

근거 pair:
- latest `/work`: `work/4/1/2026-04-01-overwrite-approval-execution.md`
- latest same-day `/verify`: `verify/4/1/2026-04-01-overwrite-approval-execution-verification.md`

이번 verify 결론:
- 코드 변경과 테스트 추가는 `/work` 주장대로 실제로 들어가 있습니다.
- rerun 검증: `python3 -m py_compile tools/write_note.py core/agent_loop.py`, `python3 -m unittest -v tests.test_write_note tests.test_smoke tests.test_web_app` (`286 tests OK`), `git diff --check -- tools/write_note.py core/agent_loop.py app/templates/index.html tests/test_write_note.py tests/test_web_app.py`, `make e2e-test` (`16 passed (3.7m)`)
- 기능과 browser contract는 현재 기준으로 통과했습니다.

다음 Claude 작업:
- `overwrite approval execution docs sync only`

이번 slice 범위:
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`

반영해야 할 사실:
- overwrite는 기본값으로는 계속 거부되지만, explicit overwrite approval 경로에서는 승인 실행 후 실제 덮어쓰기가 이제 shipped behavior입니다.
- existing path로 reissue되더라도 즉시 write하지 않고, pending approval에 `overwrite`가 표시된 뒤 별도 explicit approval 실행에서만 저장됩니다.
- approval preview / warning copy와 승인 버튼 동작은 현재 shipped UI에 맞게 문서화해야 합니다.
- stale `Not Implemented` / `Explicitly Deferred` / future-only wording은 제거하거나 현재 contract에 맞게 고쳐야 합니다.

검증:
- docs-only round로 유지하고 `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`만 실행하세요.
- 새 코드 변경이나 새 verification slice로 넓히지 마세요.
