# 2026-04-03 search-results single-result wording doc sync

**범위**: root docs에서 selected local search-result summary 설명을 현재 구현(single-result non-comparative wording)에 맞게 truth-sync

---

## 변경 파일

- `docs/PRODUCT_SPEC.md` — 3곳 (line 41, 134, 135)
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳 (line 25)
- `docs/NEXT_STEPS.md` — 1곳 (line 17)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

이전 라운드(`work/4/3/2026-04-03-search-results-single-result-non-comparative-wording.md`)에서 `core/agent_loop.py`의 short-summary와 reduce prompt에 single-result non-comparative wording 분기가 추가되었으나, root docs 3개 파일은 모든 search-result summary를 일괄적으로 "shared facts, differences, actions, and conclusion" 중심으로만 설명하고 있어 현재 구현과 충돌. `verify/4/3/` 검수에서도 이 docs-sync 누락이 지적됨.

---

## 핵심 변경

1. `docs/PRODUCT_SPEC.md:41` — search-result summary 일반 설명에 multi-result vs single-result 구분 추가: multi-result는 shared facts/meaningful differences, single-result는 non-comparative wording (main facts, actions, grounded conclusion without cross-result comparison)
2. `docs/PRODUCT_SPEC.md:134-135` — document search 세부 설명에서 "selected results"를 "multiple selected results"로 좁히고, single-result 경로의 non-comparative wording 설명 병기
3. `docs/ACCEPTANCE_CRITERIA.md:25` — search-synthesis guidance 설명에 multi-result/single-result 구분 추가
4. `docs/NEXT_STEPS.md:17` — source-type boundary 설명에 multi-result/single-result 구분 추가

---

## 검증

- `rg -n "shared facts|meaningful differences|single-result|search-result summaries|search-result-oriented" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md` — 수정된 3개 파일에서 multi/single 구분 반영 확인, MILESTONES.md와 TASK_BACKLOG.md는 해당 wording 없음
- `git diff --check -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` — 통과 (공백 오류 없음)
- README.md:47 — "source-backed synthesis guidance"라는 일반적 표현으로 직접적 wording 충돌 없어 수정하지 않음
- 코드, 테스트, UI, approval, storage, web investigation, reviewed-memory, watcher 경로는 수정하지 않음

---

## 남은 리스크

- 이번 라운드는 docs wording sync only이므로 코드/테스트 변경 없음. `python3 -m unittest`는 이번 변경과 무관하여 재실행하지 않음
- chunk-note prompt wording은 이번 범위 밖이며 변경하지 않음 (multi/single 구분이 chunk-note 단계에는 아직 적용되지 않음 — 현재 코드도 chunk-note에는 분기 없음)
- prompt-level wording은 soft constraint이므로 실제 LLM 출력의 hard guarantee는 아님
- same-family current-risk가 이번 라운드로 닫혔으므로, 다음 슬라이스는 새 quality axis로 넘어갈 수 있음
