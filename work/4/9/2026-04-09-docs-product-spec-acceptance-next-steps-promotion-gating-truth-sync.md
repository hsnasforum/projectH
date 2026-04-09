# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA NEXT_STEPS promotion-gating truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1474): promotion-ineligible gating shipped 현재형 반영
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 580, 641): cross-session counting 근거 및 unblock intro shipped 현재형 반영
- `docs/NEXT_STEPS.md` — 1곳(line 108): promotion-ineligible gating shipped 현재형 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1474: "until precondition family is satisfied in full"이 promotion 해제를 precondition 충족에 결부; capability satisfaction은 이미 출하, promotion은 별도로 later
- line 580: "until a later local store, rollback, conflict, and reviewed-memory boundary exists"가 이미 출하된 contract surface를 미존재로 프레이밍
- line 641: "must remain closed until every precondition is explicit"가 이미 출하된 unblock path를 미출하로 프레이밍
- line 108: "until the full precondition family exists and is satisfied"가 이미 출하된 capability path를 미래로 프레이밍

## 핵심 변경
- PRODUCT_SPEC:1474 — "promotion-ineligible until ... satisfied in full" → "promotion-ineligible; capability path satisfies through source-family-plus-basis chain while promotion remains later"
- ACCEPTANCE_CRITERIA:580 — "until a later local store, rollback, conflict ..." → "remains later because no payload-visible store and no cross-session scope; current contract surfaces shipped read-only"
- ACCEPTANCE_CRITERIA:641 — "must remain closed until every precondition is explicit" → "is now shipped with every precondition explicit; `unblocked_all_required` materializes through source-family-plus-basis chain"
- NEXT_STEPS:108 — "until the full family exists and is satisfied" → "precondition family is shipped and capability satisfaction path is open while promotion remains later"

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md` — 4줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/ACCEPTANCE_CRITERIA/NEXT_STEPS promotion-gating 진실 동기화 완료
