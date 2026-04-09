# docs: ACCEPTANCE_CRITERIA reviewed-memory precondition and apply residual truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 3곳(line 845, 970, 976): precondition-status/unblock/apply 계층 shipped 현재형 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 845: "no reviewed-memory apply"가 blocked-only status 슬라이스 안에 있어 apply 자체 미출하처럼 프레이밍; apply path는 이미 출하
- line 970: "through later reviewed-memory-layer machinery"가 unblock을 미래로만 프레이밍; `capability_outcome = unblocked_all_required`는 이미 출하
- line 976: "emitted transition records, reviewed-memory apply ... remain closed"가 출하된 계층을 미출하로 프레이밍

## 핵심 변경
- ACCEPTANCE_CRITERIA:845 — "no reviewed-memory apply" 제거 → "the reviewed-memory apply path is shipped above this status object"
- ACCEPTANCE_CRITERIA:970 — "through later machinery" → "unblock is shipped: `capability_outcome = unblocked_all_required` materializes when source-family-plus-basis path is present; per-precondition satisfaction booleans and resolver machinery remain later"
- ACCEPTANCE_CRITERIA:976 — "emitted transition records, reviewed-memory apply ... remain closed in that slice" → "emitted transition records and reviewed-memory apply are shipped above this unblock slice; repeated-signal promotion and cross-session counting remain later"

## 검증
- `git diff -- docs/ACCEPTANCE_CRITERIA.md` — 3줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — ACCEPTANCE_CRITERIA reviewed-memory precondition/apply 진실 동기화 완료
