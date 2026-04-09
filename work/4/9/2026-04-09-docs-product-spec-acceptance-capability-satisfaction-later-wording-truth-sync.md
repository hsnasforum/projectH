# docs: PRODUCT_SPEC and ACCEPTANCE_CRITERIA capability-satisfaction later-wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 1480, 1516): capability-satisfaction "later" 문구 shipped 현재형 반영
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 680): same-session unblock "later" → shipped 현재형 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1480: "satisfying the full family later"가 capability satisfaction을 미래로만 프레이밍; source-family-plus-basis path는 이미 출하
- line 1516: "until later machinery can satisfy them"이 contract object 충족을 미래 machinery에만 의존하는 것처럼 프레이밍; shipped source-family-plus-basis path가 이미 truthful `unblocked_all_required` 실현
- line 680: "same-session unblock later"가 unblock을 미래로 프레이밍; 이미 출하됨

## 핵심 변경
- PRODUCT_SPEC:1480 — "satisfying the full family later means" → "satisfying the full family means ... this path is now shipped through the current source-family-plus-basis chain"
- PRODUCT_SPEC:1516 — "remain `contract exists` only until later machinery can satisfy them" → "remain `contract exists` as read-only surfaces; the current truthful `unblocked_all_required` state materializes through the shipped source-family-plus-basis path above them"
- ACCEPTANCE_CRITERIA:680 — "same-session unblock later must still remain separate" → "same-session unblock is shipped and must remain separate"

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 3줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/ACCEPTANCE_CRITERIA capability-satisfaction later-wording 진실 동기화 완료
