## 변경 파일
- `verify/4/3/2026-04-03-search-results-general-doc-wording-scope-narrowing-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-search-results-general-doc-wording-scope-narrowing.md`를 기준으로, 이번 general-doc wording scope narrowing 주장이 실제 코드/문서와 맞는지 다시 좁게 확인해야 했습니다.
- 같은 날짜 최신 기존 `/verify`인 `verify/4/3/2026-04-03-search-results-single-result-doc-sync-verification.md`는 직전 docs-sync 라운드 기준 검수였으므로, 그 뒤에 추가된 latest `/work`가 same-family truth-sync를 실제로 닫았는지 별도로 확인해야 했습니다.

## 핵심 변경
- latest `/work`의 변경 주장은 현재 코드/문서와 맞습니다.
  - 커밋 `8c76483`는 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/NEXT_STEPS.md`, 그리고 이번 `/work` 메모만 변경했습니다.
  - current MVP 범위를 벗어나는 코드, UI, approval, storage, web investigation, reviewed-memory, watcher 실험 경로 변경은 없습니다.
- latest `/work`가 좁힌 general docs 3줄은 현재 구현과 정합합니다.
  - `docs/PRODUCT_SPEC.md:41`는 search-result summary family 전체의 source-type split은 유지하되, multi/single-result 추가 split을 `short-summary`와 `reduce`에만 한정하고 `per-chunk chunk-note`는 uniform wording이라고 명시합니다.
  - `docs/ACCEPTANCE_CRITERIA.md:25`도 같은 경계를 유지합니다.
  - `docs/NEXT_STEPS.md:17`도 `Short-summary, per-chunk chunk-note, and reduce prompts`로 정확히 적고, count-based split은 short-summary와 reduce에만 적용되며 chunk-note는 uniform이라고 적습니다.
- 현재 코드와 focused regression도 위 문서 설명과 맞습니다.
  - `_build_individual_chunk_summary_prompt()`는 여전히 `Prioritize source-backed facts, meaningful differences, and explicit actions or decisions visible in this excerpt.`를 사용하며 single-result 분기가 없습니다.
  - 반면 short-summary와 reduce는 기존 라운드에서 이미 single-result non-comparative wording 분기를 갖고 있고, 관련 smoke test도 그대로 잠겨 있습니다.
- 따라서 latest `/work`의 truth-sync closeout은 이번 라운드 기준으로 truthful합니다.
  - 이번 라운드로 search-results summary prompt family의 current docs truth는 닫혔습니다.
  - 이번 closeout은 current MVP를 벗어나지 않았고, docs-only 범위도 실제로 지켰습니다.
- 다만 다음 라운드 자동 handoff는 멈출 필요가 없습니다.
  - same-family truth-sync blocker는 닫혔지만, same-family user-visible improvement 1개는 여전히 남아 있습니다.
  - long single-result search summaries의 `per-chunk chunk-note`는 아직 uniform `meaningful differences` wording을 유지하므로, short-summary/reduce와 같은 non-comparative framing을 chunk-note에도 좁게 확장하면 long single-result path의 출력 압력을 더 직접적으로 줄일 수 있습니다.
  - 따라서 다음 자동 handoff는 새 quality axis가 아니라, 같은 family의 가장 작은 same-family user-visible improvement로 `single-result search chunk-note non-comparative wording` 1건이 맞습니다.

## 검증
- `git show --stat --summary 8c76483 -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md work/4/3/2026-04-03-search-results-general-doc-wording-scope-narrowing.md`
  - latest `/work`가 docs 3개와 closeout만 바꿨는지 확인했습니다.
- `rg -n "_build_individual_chunk_summary_prompt|meaningful differences|selected search-result excerpt|source-backed evidence chunk within a larger search-result synthesis" core/agent_loop.py tests/test_smoke.py`
  - chunk-note가 여전히 uniform wording을 유지하는 현재 코드/테스트 truth를 확인했습니다.
- `rg -n "short-summary|per-chunk|final reduce|single-result|non-comparative|long-summary prompts" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - general docs 3줄이 short-summary + reduce split only / chunk-note uniform 경계로 실제로 좁혀졌는지 확인했습니다.
- `git diff --check -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
  - 통과
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_search_short_summary_single_result_non_comparative tests.test_smoke.SmokeTest.test_search_reduce_single_result_non_comparative tests.test_smoke.SmokeTest.test_long_search_summary_reduce_uses_search_result_synthesis_prompt`
  - `Ran 3 tests in 0.012s`
  - `OK`
  - short-summary / reduce의 single-result split과 chunk-note의 existing wording truth를 함께 재확인했습니다.
- 재실행하지 않은 검증
  - 코드 동작 변경이 없는 docs-only 라운드이므로 전체 `tests.test_smoke`, `tests.test_web_app`, `make e2e-test`는 이번 라운드에 필요하지 않아 재실행하지 않았습니다.

## 남은 리스크
- latest `/work`의 docs truth-sync 주장은 이번 라운드 기준으로 맞습니다. 현재 search-results summary prompt family의 docs/code mismatch는 보이지 않습니다.
- 다만 long single-result search summaries에서는 intermediate `chunk_note` 단계가 아직 generic search-synthesis wording을 유지하므로, short-summary / reduce와 동일한 non-comparative framing으로 좁히는 same-family user-visible 개선 여지는 남아 있습니다.
- 현재 `.pipeline/codex_feedback.md`는 위 exact next slice 1개만 구현하도록 갱신했습니다.
