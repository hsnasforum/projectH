# 2026-03-31 codex auto slice tiebreak verification

## 변경 파일
- `verify/3/31/2026-03-31-codex-auto-slice-tiebreak-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-codex-auto-slice-tiebreak.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-malformed-utf8-request-400-handling-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 product code가 아니라 single-Codex operator-flow 문서를 동기화해 Codex 자동 다음-slice tie-break 기준을 명확히 했다고 적고 있으므로, 이번 검수에서는 관련 문서들의 실제 반영 여부, 범위가 current projectH 방향을 벗어나지 않았는지, 그리고 이 규칙을 바탕으로 다음 handoff를 truthful하게 좁힐 수 있는지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 문서 변경 주장은 현재 파일과 일치합니다.
- `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.pipeline/README.md`, `work/README.md`, `verify/README.md`에는 모두 다음 operator-flow 보강이 실제로 반영되어 있습니다.
  - `STATUS: needs_operator`는 bare stop line이 아니라 stop reason / latest `/work`-`/verify` 근거 / operator decision requirement를 같이 남겨야 한다는 점
  - latest `/work`와 `/verify`가 한 family를 truthfully 닫았다면 same-family current-risk reduction을 먼저 자동 선택한다는 점
  - 자동 tie-break 순서가 `same-family current-risk reduction -> same-family user-visible improvement -> new quality axis -> internal cleanup`이라는 점
- 이 변경은 current product contract를 넓히는 것이 아니라 single-Codex verification/handoff 규칙을 current MVP 범위 안에서 더 명확히 정리한 것입니다. product loop, approval flow, reviewed-memory semantics, web investigation contract, browser-visible behavior 확장은 확인되지 않았습니다.
- staged roadmap이나 north-star wording을 바꾼 것이 아니라 operator-flow 문서 보강이므로, 이번 round에서 `plandoc/` 추가 sync가 필요한 징후도 보이지 않았습니다.
- latest `/work`가 새 규칙을 충분히 좁게 문서화했기 때문에, 이번 `/verify`에서는 더 이상 `needs_operator`를 유지할 이유가 없습니다. same-family current-risk-first tie-break를 그대로 적용하면, malformed request-body family의 다음 최소 후속은 `valid UTF-8 but malformed JSON syntax -> 400` direct regression 1건입니다. 현재 `app/web.py`는 이미 그 branch를 `400`으로 처리하지만, `tests/test_web_app.py`에는 malformed UTF-8 branch만 직접 검증되고 malformed JSON syntax branch는 직접 보호되지 않습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `git diff -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md work/README.md verify/README.md`
  - latest `/work`가 주장한 문서 변경 실제 반영 여부 확인
- `rg -n "same-family current-risk reduction|same-family user-visible improvement|new quality axis|internal cleanup|needs_operator|truth-sync" AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md work/README.md verify/README.md`
  - tie-break 규칙과 bare-stop 금지 문구가 각 문서에 실제로 동기화됐는지 대조
- `git diff --check -- AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md work/README.md verify/README.md`
  - 통과 (출력 없음)
- `rg -n "JSON 요청 본문 형식이 올바르지 않습니다|요청 본문이 필요합니다|JSON 본문은 객체 형태여야 합니다|invalid json|malformed json|test_handler_returns_400_for_.*json|test_.*JSON.*400" tests/test_web_app.py app/web.py`
  - malformed request-body family의 다음 same-family regression 후보 존재 여부 확인
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v ...`
  - `make e2e-test`
  - 이유: latest `/work`가 operator-flow docs-only sync였고, product code/runtime contract를 새로 바꾸지 않았으므로 문서 대조와 formatting check만으로 이번 범위를 직접 검수할 수 있었습니다.

## 남은 리스크
- 새 tie-break 규칙이 실제로 계속 잘 적용되는지는 다음 몇 라운드의 Codex handoff에서 지켜봐야 합니다.
- current worktree가 여전히 넓게 dirty 상태라 다음 Claude 라운드도 unrelated 변경을 섞지 않는 좁은 범위 통제가 필요합니다.
