# docs: MILESTONES boundary_draft priority shipped machinery wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 1곳(line 400): boundary_draft 우선순위 행에서 "before actual ... machinery exists" 제거, shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 400이 "before actual rollback / disable / conflict / operator-audit machinery exists"로 계약 machinery를 미존재로 프레이밍
- 실제로 rollback/disable/conflict/operator-audit 계약 + apply 경로 모두 이미 출하됨
  - PRODUCT_SPEC(line 1473-1493), ARCHITECTURE(line 864-888), ACCEPTANCE_CRITERIA(line 647-665)
- 동일 파일 line 402에서 이미 apply/stop/reverse/conflict-visibility를 shipped로 기술

## 핵심 변경
- "before actual rollback / disable / conflict / operator-audit machinery exists" 제거
- "The rollback / disable / conflict / operator-audit contracts and the reviewed-memory apply path are now shipped; boundary draft stays separate from apply result" 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES boundary_draft 우선순위 행 shipped machinery 진실 동기화 완료
