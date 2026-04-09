# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA reviewed-memory apply-result absence truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 1451, 1469): boundary draft와 disable contract의 apply result 부재 문구 수정
- `docs/ACCEPTANCE_CRITERIA.md` — 8곳(line 701, 708, 717, 728, 743, 776, 783, 793): planning-target, rollback/disable/conflict/audit contract, emitted transition record, unblock contract, capability status의 apply result 부재 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `docs/PRODUCT_SPEC.md:1537`과 `docs/ACCEPTANCE_CRITERIA.md:923`/`930`에서 이미 reviewed-memory apply result (apply / stop-apply / reversal / conflict-visibility)가 출하 상태로 기술됨
- 그러나 각 개별 surface(boundary draft, rollback contract, disable contract 등)에서는 여전히 "no reviewed-memory apply result" 또는 "no apply result"로 적어 apply result가 아예 존재하지 않는 것처럼 프레이밍
- 실제로 이 surface들은 apply result를 직접 담지 않는 것이 맞지만, apply result 자체의 존재를 부정하는 문구는 shipped truth와 충돌

## 핵심 변경
- 모든 대상 라인에서 "no reviewed-memory apply result" / "no apply result" → "reviewed-memory apply result is shipped separately above the capability path; [이 surface]에는 담기지 않음" 패턴으로 교체
- 각 surface가 read-only이고 apply result를 직접 포함하지 않는다는 보수적 의미는 보존
- payload-visible store, cross-session widening, proof-record/proof-boundary 부재 등 기존 제약은 그대로 유지
- literal id, shipped enum value, 기존 계약 구조 변경 없음

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 10줄 변경 확인
- `rg -n 'no reviewed-memory apply result|no apply result' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md` — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/ACCEPTANCE_CRITERIA의 reviewed-memory apply-result absence 진실 동기화 완료
