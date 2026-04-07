## 변경 파일
- `verify/4/2/2026-04-02-search-results-chunk-note-target-length-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/2/2026-04-02-search-results-chunk-note-target-length.md`를 기준으로, 이번 라운드의 `search_results` chunk-note prompt 길이 가이드 추가와 테스트 rename 주장이 실제 코드/검증 결과와 맞는지 다시 확인해야 했습니다.
- 같은 날짜 최신 `/verify`인 `verify/4/2/2026-04-02-search-results-summary-target-length-verification.md` 이후 새 `/work`가 추가되었으므로, 이전 verify truth를 덮어쓰지 않고 이번 추가 변경만 좁게 재검수해야 했습니다.

## 핵심 변경
- `/work`의 코드 변경 주장은 현재 트리와 커밋 `ca08aff` 기준으로 사실이었습니다.
  - `core/agent_loop.py`의 `_build_individual_chunk_summary_prompt(..., summary_source_type="search_results")`에 `Target length: 1~2 sentences (50~150 Korean characters). Do not exceed 3 sentences.`가 실제로 추가돼 있습니다.
  - 같은 파일의 `_build_short_summary_prompt(..., summary_source_type="search_results")`와 `_build_chunk_summary_reduce_prompt(..., reduce_source_type="search_results")`에는 직전 라운드의 길이 가이드가 그대로 남아 있어, 현재 `search_results` summary family의 세 prompt 모두가 `Target length:` 지시를 포함하는 상태가 맞습니다.
- 테스트 변경 주장도 사실이었습니다.
  - `tests/test_smoke.py`의 기존 `test_target_length_guidance_only_in_local_document_prompts`는 `test_target_length_guidance_in_all_summary_prompts`로 rename돼 있습니다.
  - 같은 테스트는 `search_chunk`, `search_short`, `search_reduce` 모두에 대해 `assertIn("Target length:", ...)`를 확인해 이번 슬라이스 범위를 정확히 잠급니다.
- 커밋 범위도 `/work` 설명과 일치했습니다.
  - 이번 커밋은 `core/agent_loop.py`, `tests/test_smoke.py`, 해당 `/work` 메모 3개 파일로만 닫혔습니다.
- 문서 sync 누락은 이번 라운드에서 발견되지 않았습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 exact prompt sentence-range wording을 계약으로 서술하지 않아, 이번 prompt-line 추가와 충돌하지 않았습니다.
- 이번 변경은 현재 projectH 방향을 벗어나지 않았습니다.
  - local-first document assistant MVP 안에서 `search_results` 요약 품질을 좁게 개선한 변경입니다.
  - approval flow, session schema, storage, UI contract, web investigation policy, reviewed-memory surface는 건드리지 않았습니다.

## 검증
- `git show --stat --summary ca08aff -- core/agent_loop.py tests/test_smoke.py work/4/2/2026-04-02-search-results-chunk-note-target-length.md`
  - 관련 커밋 범위가 `core/agent_loop.py`, `tests/test_smoke.py`, 해당 `/work` 메모로만 닫히는 것을 확인했습니다.
- `git diff --check 3f2e08e ca08aff -- core/agent_loop.py tests/test_smoke.py work/4/2/2026-04-02-search-results-chunk-note-target-length.md`
  - 통과
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 통과
- `python3 -m unittest -v tests.test_smoke`
  - `Ran 98 tests in 1.180s`
  - `OK`
- 재실행하지 않은 검증
  - browser-visible UI, approval payload, session schema 변경이 아니므로 `make e2e-test`는 이번 라운드에 필요하지 않아 재실행하지 않았습니다.

## 남은 리스크
- `search_results` summary family에서 빠져 있던 `Target length:` gap은 이번 라운드로 닫혔습니다.
- 다만 `_build_short_summary_prompt(..., summary_source_type="search_results")`는 선택 결과가 한두 개뿐인 sparse 입력에도 기본 목표를 `3~5 sentences`로만 제시해, 짧은 결과 집합에서 불필요한 padding이나 장황화를 유도할 리스크가 남아 있습니다.
- 따라서 다음 자동 handoff는 같은 family의 가장 작은 current-risk reduction으로, `search_results` short-summary prompt에만 sparse/single-result 입력용 `2~3 sentences` 예외를 추가하고 그 wording regression을 잠그는 슬라이스로 좁히는 편이 맞습니다.
