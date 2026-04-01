# 2026-03-31 transcript/quick-meta source-type predicate drift 검증 및 확인

## 변경 파일
- `app/templates/index.html` (변경 없음 — 기존 미커밋 상태가 이미 올바름)

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md` (`STATUS: implement`) 지시에 따라, transcript meta와 quick-meta의 summary source-type 판정식이 동일한 boundary를 쓰는지 검증하고, evidence-bearing non-document 응답에 `문서 요약`이 잘못 붙는 누수를 막아야 했음

## 핵심 검증 결과

### 현재 코드 상태 (미커밋 working tree)
- 공유 helper `getSourceTypeLabel` (line 2722–2727)이 이미 존재:
  ```js
  function getSourceTypeLabel(obj) {
    const kind = String(obj?.active_context?.kind || "").trim();
    if (kind === "search") return "선택 결과 요약";
    if (kind === "document" && (obj?.summary_chunks?.length || obj?.evidence?.length)) return "문서 요약";
    return null;
  }
  ```
- `renderTranscript` (line 2546)과 `renderResponseSummary` (line 3135) 모두 동일 함수 호출
- 이전 `renderResponseSummary`의 인라인 로직은 `getSourceTypeLabel` 호출로 교체 완료
- `kind === "document"` 가드가 `&&` 연산자로 `(summary_chunks || evidence)` 전체를 감싸고 있어, `kind !== "document"`일 때 `문서 요약`이 반환될 수 없음

### verify 노트와의 대조
- `verify/3/31/2026-03-31-transcript-meta-source-type-label-verification.md`에서 지적한 predicate drift 버그는 현재 working tree 코드에서는 **이미 해결된 상태**
- verify 시점과 현재 사이에 working tree가 수정되었거나, verify가 HEAD 기준으로 평가한 것으로 추정
- 계약 boundary는 정확히 충족:
  - `active_context.kind === "search"` → `선택 결과 요약` ✅
  - `active_context.kind === "document"` + `summary_chunks` 또는 `evidence` → `문서 요약` ✅
  - 그 외 → label 없음 ✅

### 변경하지 않은 것
- 새 코드 변경 없음 (기존 미커밋 코드가 올바르므로)
- backend field, prompt, summary behavior 변경 없음
- unrelated dirty file 정리 없음
- docs 변경 없음 (copy/contract wording 변경 없음)

## 검증
- `git diff --check -- app/templates/index.html` — 통과
- `make e2e-test` — `12 passed (2.7m)`
- 수동 코드 대조:
  - `getSourceTypeLabel` 함수의 operator precedence 확인 (`&&`가 `||`보다 높음, 괄호로 명시적 그룹핑)
  - `renderTranscript`와 `renderResponseSummary` 모두 동일 함수 사용 확인
  - `git diff HEAD -- app/templates/index.html`로 미커밋 변경 내용 전체 검토

## 남은 리스크
- 이 변경들은 아직 커밋되지 않은 상태 (working tree에만 존재)
- current smoke suite는 evidence-bearing non-document 케이스를 직접 테스트하지 않음 (mock adapter 한계)
- dirty worktree에 unrelated 변경이 넓게 섞여 있어, 커밋 시 선별 staging 필요
