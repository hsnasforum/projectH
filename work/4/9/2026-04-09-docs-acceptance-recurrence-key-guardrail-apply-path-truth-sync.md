# docs: ACCEPTANCE_CRITERIA recurrence-key guardrail apply-path truth sync

## 변경 파일
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 806): recurrence-key 가드레일에서 apply-path 부정 제거, shipped 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 806이 "must not emit ... a reviewed-memory apply path"로 전역 부정
- 동일 문서에서 이미 출하된 apply 라이프사이클을 기술 (line 763-776, 920-967)
- PRODUCT_SPEC(line 1178-1203)과 ARCHITECTURE(line 907-913)는 planning-target/unblock 의미가 apply보다 좁다고 기술 (전역 부정 아님)
- `app/web.py:302-306`에서 5개 aggregate transition API 존재

## 핵심 변경
- "a repeated-signal promotion object, a reviewed-memory candidate store, or a reviewed-memory apply path" → "a repeated-signal promotion object or a reviewed-memory candidate store; the reviewed-memory apply path ... is now shipped and lives above the planning-target / recurrence-key guardrail layer"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — recurrence-key 가드레일의 apply-path 부정 진실 동기화 완료
