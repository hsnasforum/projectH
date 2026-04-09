# docs: TASK_BACKLOG precondition-status and unblock residual shipped wording truth sync

## 변경 파일
- `docs/TASK_BACKLOG.md` — 2곳(line 329, 476): blocked-only status 객체 및 unblock 의미론 shipped 현재형 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 329: "no reviewed-memory apply"가 status 객체 블록 안에 있어 apply 자체가 미출하인 것처럼 프레이밍됨; apply path는 이미 출하됨 (status 객체에 apply-result 필드가 없다는 것이 정확한 의미)
- line 476: "through later machinery"가 unblock을 미래로만 프레이밍; `capability_outcome = unblocked_all_required`는 이미 출하됨

## 핵심 변경
- TASK_BACKLOG:329 — "no reviewed-memory apply" → "the reviewed-memory apply path is shipped above this status object; no apply-result fields on the status object itself"
- TASK_BACKLOG:476 — "unblock may occur only when ... satisfied through later machinery" → "unblock is shipped: `capability_outcome = unblocked_all_required` materializes when source-family-plus-basis path is present; per-precondition satisfaction booleans and resolver machinery remain later"

## 검증
- `git diff -- docs/TASK_BACKLOG.md` — 2줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — TASK_BACKLOG precondition-status/unblock shipped wording 진실 동기화 완료
