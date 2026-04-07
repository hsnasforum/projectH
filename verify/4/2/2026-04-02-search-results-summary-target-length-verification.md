## 변경 파일
- `verify/4/2/2026-04-02-search-results-summary-target-length-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/2/2026-04-02-search-results-summary-target-length.md`를 기준으로, 이번 라운드의 `search_results` 최종 요약 prompt 길이 가이드 변경이 실제 코드와 검증 결과에 맞는지 다시 확인해야 했습니다.
- 같은 날짜 최신 `/verify`인 `verify/4/2/2026-04-02-streaming-general-follow-up-clamp-regression-verification.md` 이후 새 `/work`가 추가되었으므로, 이전 verify truth를 덮어쓰지 않고 이번 추가 변경만 좁게 재검수해야 했습니다.

## 핵심 변경
- `/work`의 코드 변경 주장은 현재 트리와 커밋 `3f2e08e` 기준으로 사실이었습니다.
  - `core/agent_loop.py`의 `_build_short_summary_prompt(..., summary_source_type="search_results")`에 `Target length: 3~5 sentences (200~400 Korean characters). Do not exceed 6 sentences.`가 실제로 추가돼 있습니다.
  - `core/agent_loop.py`의 `_build_chunk_summary_reduce_prompt(..., reduce_source_type="search_results")`에 `Target length: 4~7 sentences (300~600 Korean characters) covering all {N} search-result notes. Do not exceed 8 sentences.`가 실제로 추가돼 있습니다.
  - 같은 파일의 `_build_individual_chunk_summary_prompt(..., summary_source_type="search_results")`에는 여전히 `Target length:` 가이드가 없어서, `/work`가 말한 "최종 요약 prompt 2곳만 변경" 범위가 맞았습니다.
- 테스트 변경 주장도 사실이었습니다.
  - `tests/test_smoke.py`의 `test_target_length_guidance_only_in_local_document_prompts`는 `search_short`와 `search_reduce`에 대해 `assertIn("Target length:", ...)`로 바뀌었고,
  - `search_chunk`는 여전히 `assertNotIn("Target length:", ...)`로 남아 있어 이번 슬라이스 범위를 정확히 잠급니다.
- 문서 sync 누락은 이번 라운드에서 발견되지 않았습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 현재 `search_results` 요약이 source-backed synthesis guidance를 따른다고만 설명하고 있으며, 이번처럼 prompt 길이 가이드를 2곳에만 추가한 구현과 충돌하지 않았습니다.
- 이번 변경은 현재 projectH 방향을 벗어나지 않았습니다.
  - document-first MVP 안에서 local document search summary 품질을 좁게 개선한 변경입니다.
  - approval flow, session schema, storage, UI contract, web investigation policy, reviewed-memory surface는 건드리지 않았습니다.

## 검증
- `git show --stat --summary 3f2e08e -- core/agent_loop.py tests/test_smoke.py work/4/2/2026-04-02-search-results-summary-target-length.md`
  - 커밋 범위가 `core/agent_loop.py`, `tests/test_smoke.py`, 해당 `/work` 메모로만 닫히는 것을 확인했습니다.
- `git diff --check HEAD~1 HEAD -- core/agent_loop.py tests/test_smoke.py work/4/2/2026-04-02-search-results-summary-target-length.md`
  - 통과
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 통과
- `python3 -m unittest -v tests.test_smoke`
  - `Ran 98 tests in 1.292s`
  - `OK`
- 재실행하지 않은 검증
  - browser-visible UI, approval payload, session schema 변경이 아니므로 `make e2e-test`는 이번 라운드에 필요하지 않아 재실행하지 않았습니다.

## 남은 리스크
- `search_results` chunk-note prompt(`_build_individual_chunk_summary_prompt`)에는 아직 `Target length:` 가이드가 없습니다. 최종 short/reduce prompt는 이제 안내되지만, 중간 search-result note 길이는 여전히 모델 준수에 더 크게 의존합니다.
- prompt-level 길이 가이드는 soft constraint라 실제 출력 길이를 hard guarantee하지는 않습니다.
- 따라서 다음 자동 handoff는 같은 family의 가장 작은 current-risk reduction으로, `search_results` chunk-note prompt에만 길이 가이드를 추가하고 회귀 테스트를 그 범위만큼 갱신하는 슬라이스로 좁히는 편이 맞습니다.
