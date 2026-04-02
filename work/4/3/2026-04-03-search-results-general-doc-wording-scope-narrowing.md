# 2026-04-03 search-results general-doc wording scope narrowing

**범위**: root docs general 설명 3줄에서 multi/single-result split 범위를 short-summary + reduce only로 좁히고, chunk-note는 uniform wording으로 명시

---

## 변경 파일

- `docs/PRODUCT_SPEC.md` — 1곳 (line 41)
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳 (line 25)
- `docs/NEXT_STEPS.md` — 1곳 (line 17)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드(`work/4/3/2026-04-03-search-results-single-result-doc-sync.md`)에서 root docs에 multi/single-result 구분을 추가했으나, general 설명 3줄이 `short-summary, per-chunk, and reduce` 또는 `Short-summary and long-summary prompts` 전체에 대해 single-result non-comparative wording이 열린 것처럼 읽혀, 실제 코드의 `_build_individual_chunk_summary_prompt()`가 여전히 uniform `meaningful differences` search-synthesis wording을 유지하는 현실과 충돌. `verify/4/3/` 검수에서도 이 over-broad scope가 지적됨.

---

## 핵심 변경

1. `docs/PRODUCT_SPEC.md:41` — source-type split은 전체(short-summary, per-chunk, reduce)에 유지하되, multi/single-result 추가 split을 short-summary와 reduce에만 한정. chunk-note는 "uniform search-synthesis wording regardless of result count"로 명시.
2. `docs/ACCEPTANCE_CRITERIA.md:25` — search-synthesis guidance 후 문장을 분리하여, short-summary + reduce만 result count 기준 추가 split, chunk-note는 uniform으로 명시.
3. `docs/NEXT_STEPS.md:17` — "Short-summary and long-summary prompts"를 "Short-summary, per-chunk chunk-note, and reduce prompts"로 정확하게 좁히고, multi/single split은 short-summary + reduce에만 적용되며 chunk-note는 uniform으로 명시.

---

## 검증

- `rg -n "_build_individual_chunk_summary_prompt|meaningful differences|selected search-result excerpt|source-backed evidence chunk within a larger search-result synthesis" core/agent_loop.py tests/test_smoke.py` — chunk-note가 single-result 분기 없이 uniform wording 유지 확인
- `rg -n "short-summary|per-chunk|final reduce|single-result|non-comparative|long-summary prompts" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` — general 설명에서 "long-summary prompts" 제거, multi/single split이 short-summary + reduce에만 한정됨 확인, PRODUCT_SPEC.md:134-135 상세 라인 변경 없음 확인
- `git diff --check -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` — 통과
- 코드/테스트/UI/approval/storage/web investigation/reviewed-memory/watcher 경로 수정 없음

---

## 남은 리스크

- search-result summary prompt family의 docs truth-sync는 이번 라운드로 닫힌 상태: source-type split(3개 prompt 공통) + multi/single-result split(short-summary + reduce only) + chunk-note uniform wording 모두 docs에 반영됨
- chunk-note에도 single-result 분기가 필요한지 여부는 별도 product decision이며, 현재는 코드와 docs가 일치하는 상태
- prompt-level wording은 soft constraint이므로 실제 LLM 출력의 hard guarantee는 아님
- same-family current-risk가 이번 라운드로 닫혔으므로, 다음 슬라이스는 새 quality axis로 넘어갈 수 있음
