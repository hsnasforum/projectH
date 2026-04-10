## 변경 파일
- 없음

## 사용 skill
- round-handoff

## 변경 이유
- latest `/work`가 claimed docs-only `PRODUCT_SPEC Web Investigation Rules` wording clarification을 실제 current docs truth에 맞게 반영했는지 확인해야 했습니다.
- `PRODUCT_SPEC` top-level summary family에서 `Stored Evidence` 뒤 same-family next slice를 한 개로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work` `work/4/8/2026-04-08-product-spec-web-investigation-rules-wording-clarification.md`는 truthful하다고 확인했습니다.
- current `docs/PRODUCT_SPEC.md:308-312`는 `/work` 주장대로 아래 web-investigation truth를 반영하고 있습니다.
  - read-only external search with permission-gated execution (`enabled` / `disabled` / `ask` per session)
  - local JSON history with in-session reload and history-card header badges
  - response origin with `WEB` badge, answer-mode badge, verification-strength badge, source-role trust badges
  - entity-card / latest-update distinction with separate verification labels and entity-card strong-badge downgrade when no slot is cross-verified
  - claim coverage panel with status tags, actionable hints, fact-strength summary bar, slot reinvestigation scaffolding
- same-family shipped contract와도 일치했습니다.
  - top-level docs: `README.md:68-69`, `README.md:128`, `docs/ACCEPTANCE_CRITERIA.md:37`, `docs/ACCEPTANCE_CRITERIA.md:53`
  - deeper acceptance/product-spec contract: `docs/ACCEPTANCE_CRITERIA.md:1337-1341`, `docs/PRODUCT_SPEC.md:281-288`
- next slice는 같은 `PRODUCT_SPEC` web-investigation family에서 가장 자연스러운 후속으로 `PRODUCT_SPEC Product Modes Web Investigation wording clarification` 한 개로 고정했습니다.
  - current `docs/PRODUCT_SPEC.md:151-155`는 `permission-gated read-only external search`, `stores local JSON history`, `supports entity-card and latest-update style responses`, `secondary mode` 수준의 generic wording에 머물러 있습니다.
  - 반면 current shipped truth는 이미 `README.md:68-69`, `docs/ACCEPTANCE_CRITERIA.md:37`, `docs/ACCEPTANCE_CRITERIA.md:53`, 방금 닫힌 `docs/PRODUCT_SPEC.md:307-313`에 더 직접적으로 고정돼 있습니다.
  - `Product Modes > Web Investigation`은 같은 family의 상위 entry point summary이므로, history reload/badges, answer-mode distinction, claim coverage, secondary-mode guardrail을 한 bounded slice로 맞추는 편이 가장 자연스럽습니다.

## 검증
- `git diff -- docs/PRODUCT_SPEC.md`
- `git diff --check -- docs/PRODUCT_SPEC.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '305,321p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '127,170p'`
- `nl -ba README.md | sed -n '47,69p;124,128p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '24,39p;53,53p'`
- `rg -n "### 4\\. Web Investigation|### 2\\. Document Search|### 3\\. General Chat|local JSON history|answer-mode badge|history cards show|search-only responses hide|선택 경로 복사|search-plus-summary responses show|permission-gated read-only external search|secondary mode" docs/PRODUCT_SPEC.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md -S`
- docs-only verification 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:151-155`의 `Product Modes > Web Investigation` summary는 아직 current shipped web-investigation surface를 fully 직접 반영하지 못합니다.
- unrelated dirty worktree(`pipeline_gui/*`, `watcher_core.py`, 관련 tests, `windows-launchers/README.md`, unrelated `work/`/`verify/` notes)는 이번 검수 범위 밖이라 손대지 않았습니다.
