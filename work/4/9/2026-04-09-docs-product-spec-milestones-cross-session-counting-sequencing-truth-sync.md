# docs: PRODUCT_SPEC MILESTONES reviewed-memory cross-session-counting sequencing truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 1곳(line 1022): cross-session counting 순서 문구 수정
- `docs/MILESTONES.md` — 1곳(line 189): cross-session counting 순서 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 두 라인 모두 "cross-session counting remains later than local-store, rollback, conflict, and reviewed-memory boundary rules"로 적어, 해당 same-session 레이어들이 아직 전제 조건으로만 존재하는 것처럼 프레이밍
- 실제로 이 same-session 레이어들과 apply lifecycle (apply / stop-apply / reversal / conflict-visibility)은 이미 출하됨
- 근거 앵커: `docs/PRODUCT_SPEC.md:1062`, `docs/MILESTONES.md:199`, `docs/ACCEPTANCE_CRITERIA.md:580`/`589`

## 핵심 변경
- PRODUCT_SPEC:1022 — "cross-session counting remains later than explicit local-store, rollback, conflict, and reviewed-memory boundary rules" → "cross-session counting remains later; the same-session layers (local-store, rollback, conflict, and reviewed-memory boundary) and the apply lifecycle are already shipped above the capability path"
- MILESTONES:189 — "cross-session counting remains later than local store, rollback, conflict, and reviewed-memory rules" → 동일 패턴 적용
- cross-session counting이 여전히 later라는 사실 보존
- same-session 레이어와 apply lifecycle이 이미 출하라는 shipped truth 반영

## 검증
- `git diff -- docs/PRODUCT_SPEC.md docs/MILESTONES.md` — 2줄 변경 확인
- `rg` stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/MILESTONES의 cross-session-counting sequencing 진실 동기화 완료
