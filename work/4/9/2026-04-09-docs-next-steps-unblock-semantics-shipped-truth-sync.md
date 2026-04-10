# docs: NEXT_STEPS exact same-session unblock semantics shipped wording truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 1곳(line 206): "before any emitted transition record or apply vocabulary opens" → "the emitted transition record and apply vocabulary are shipped above this unblock layer"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 206이 emitted record와 apply vocabulary를 "before ... opens"로 미개방 프레이밍
- MILESTONES(line 271, 278), PRODUCT_SPEC(line 1524, 1530), ARCHITECTURE(line 1160, 1164), ACCEPTANCE_CRITERIA(line 920, 930)에서 이미 shipped로 기술

## 핵심 변경
- "exact same-session unblock semantics should now stay fixed before any emitted transition record or apply vocabulary opens" → "exact same-session unblock semantics are now fixed; the emitted transition record and apply vocabulary are shipped above this unblock layer"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — NEXT_STEPS unblock-semantics 문구 shipped 진실 동기화 완료
