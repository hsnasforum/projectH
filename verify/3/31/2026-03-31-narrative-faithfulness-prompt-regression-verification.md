## 변경 파일
- `.pipeline/codex_feedback.md`
- `verify/3/31/2026-03-31-narrative-faithfulness-prompt-regression-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 읽고, 최신 Claude `/work`인 `work/3/31/2026-03-31-narrative-faithfulness-prompt-regression.md`와 같은 날짜의 최신 `/verify`인 `verify/3/31/2026-03-31-narrative-summary-faithfulness-docs-sync-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 이번 round는 local-document summary strict faithfulness rule을 `tests/test_smoke.py`의 focused regression으로 고정하는 성격이므로, 실제 테스트 변경 유무, source-type split 검증 범위, 그리고 필요한 최소 회귀만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: `ready`
- latest `/work`의 변경 주장은 현재 파일 상태와 대체로 맞습니다.
  - `tests/test_smoke.py`의 기존 `test_short_local_document_summary_uses_local_document_prompt`에는 `STRICT:` 와 `Do not add events that did not happen` assertion이 실제로 추가돼 있습니다.
  - 새 `test_local_document_prompt_strict_rule_absent_in_search_results`도 실제로 존재하며, 3개 prompt builder를 `local_document` / `search_results` 양쪽으로 호출해 local-document branch에는 strict rule이 있고 search-results branch에는 없다는 점을 고정합니다.
  - `core/agent_loop.py`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에는 이번 라운드에서 새 변경이 없다는 `/work` 설명도 현재 상태와 맞습니다.
- 범위 판단도 맞습니다.
  - 이번 라운드는 current document-first MVP 안의 summary quality regression 방지용 test-only risk reduction입니다.
  - browser UI, reviewed-memory, approval flow, investigation UI, runtime behavior를 새로 넓히지 않았습니다.
- 약한 표현 보정:
  - `/work`의 “6개 prompt를 직접 비교”는 구현을 약간 세게 요약한 표현입니다.
  - 실제 테스트는 6개 prompt를 pairwise string-compare 하지는 않고, 각 prompt family에 대해 strict rule의 존재/부재 invariant를 확인합니다.
  - 다만 source-type split을 회귀 방지한다는 핵심 주장은 그대로 성립하므로 blocker로 보지는 않았습니다.
- docs 판단:
  - 이번 라운드는 shipped behavior를 바꾸지 않고 focused regression만 추가한 round라서 docs 변경이 필수는 아니었습니다.
  - 직전 round에서 root docs honesty gap은 이미 닫혔고, 이번 round의 핵심은 verification depth 보강이므로 docs 미수정은 허용 가능합니다.

## 검증
- `python3 -m py_compile tests/test_smoke.py`
  - 통과
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_local_document_prompt_strict_rule_absent_in_search_results tests.test_smoke.SmokeTest.test_short_local_document_summary_uses_local_document_prompt`
  - 통과 (`Ran 2 tests in 0.006s`)
- `python3 -m unittest -v tests.test_smoke`
  - 통과 (`Ran 87 tests in 0.975s`)
- `git diff --check`
  - 통과
- 수동 truth 대조
  - `work/3/31/2026-03-31-narrative-faithfulness-prompt-regression.md`
  - `verify/3/31/2026-03-31-narrative-summary-faithfulness-docs-sync-verification.md`
  - `tests/test_smoke.py`
  - `core/agent_loop.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_web_app`
  - `make e2e-test`
  - 이유: 이번 최신 `/work`는 browser-visible contract 변경이 아니라 `tests/test_smoke.py` 내부 focused regression 보강이며, 필요한 범위는 같은 테스트 파일의 focused / full service regression이면 충분했기 때문입니다.

## 남은 리스크
- current automated coverage는 strict faithfulness rule의 exact English sentence 전체를 product-facing contract로 노출하진 않습니다. 지금은 prompt-family split과 핵심 금지 문구 존재를 regression으로 고정한 상태입니다.
- 현재 summary source-type boundary는 docs와 internal tests에는 정직하지만, user-visible UI에서는 여전히 직접 드러나지 않습니다. 다음 slice를 연다면 internal completeness가 아니라 summary response meta에서 이 경계를 작게 보여 주는 user-visible clarity 쪽이 더 적절합니다.
- dirty worktree는 여전히 넓습니다. 다음 라운드도 unrelated 변경을 섞지 않도록 주의가 필요합니다.
