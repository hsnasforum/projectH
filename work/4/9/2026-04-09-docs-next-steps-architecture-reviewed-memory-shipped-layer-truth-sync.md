# docs: NEXT_STEPS and ARCHITECTURE reviewed-memory shipped-layer residual truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 2곳(line 532, 536): rollback/disable/conflict/operator-audit contract surface shipped 반영
- `docs/ARCHITECTURE.md` — 1곳(line 1138): rollback/disable/conflict/operator-audit contract surface 및 apply lifecycle shipped 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 3개 행이 rollback/disable/conflict/operator-audit 계층을 "없음" 또는 "precondition-future"로 프레이밍
- 실제로는 contract surface가 read-only로 이미 출하, apply/stop-apply/reversal/conflict-visibility lifecycle도 이미 출하
- 미출하인 것: payload-visible reviewed-memory store, proof-record/proof-boundary surface, cross-session counting, repeated-signal promotion

## 핵심 변경
- NEXT_STEPS:532 — "no rollback / disable / conflict / operator-audit layer" → "contract surfaces shipped read-only; apply lifecycle shipped above; no cross-session counting"
- NEXT_STEPS:536 — "no precondition-satisfying rollback / disable layer" → "rollback/disable contract surfaces shipped read-only while state machines remain later"
- ARCHITECTURE:1138 — "no separate reviewed-memory boundary, no rollback / disable surface, no operator-audit repair surface" → "ships contract surfaces read-only and apply lifecycle above; no payload-visible store, no cross-session counting"

## 검증
- `git diff -- docs/NEXT_STEPS.md docs/ARCHITECTURE.md` — 3줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — NEXT_STEPS/ARCHITECTURE reviewed-memory shipped-layer 진실 동기화 완료
