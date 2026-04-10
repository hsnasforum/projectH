# docs: MILESTONES conflict and operator-audit apply-vocabulary open wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 3곳(line 236, 248-249): conflict-contract 및 operator-audit 블록에서 "before any apply vocabulary opens" / "no reviewed-memory apply" 제거, shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 236, 249: "before any apply vocabulary opens"로 apply를 미래 대상으로 프레이밍
- line 248: "no reviewed-memory apply"로 전역 부정
- 동일 파일 line 320-340에서 이미 shipped로 기술
- ARCHITECTURE(line 1132), ACCEPTANCE_CRITERIA(line 806), PRODUCT_SPEC(line 1537-1540) 모두 shipped 프레이밍 완료
- `app/web.py:302-306`, `app/handlers/aggregate.py:392-435, 636-649`에서 출하 확인

## 핵심 변경
- line 236: "before any apply vocabulary opens" → "the apply vocabulary is now shipped above this contract layer"
- line 248: "no reviewed-memory apply" 제거 → "reviewed-memory apply path is now shipped above this contract layer"
- line 249: "before any apply vocabulary opens" → "the apply vocabulary is now shipped above this contract layer"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES conflict/operator-audit 블록의 pre-apply 프레이밍 진실 동기화 완료
