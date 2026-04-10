# docs: MILESTONES reviewed-memory apply/emitted vocabulary reopen wording truth sync

## 변경 파일
- `docs/MILESTONES.md` — 2곳(line 270-271, 278-279): "before any apply or emitted-transition vocabulary reopens" / "how future satisfied capability outcome should reopen" → shipped 프레이밍

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 271: "before any apply or emitted-transition vocabulary reopens"로 apply/emitted를 미래 대상으로 프레이밍
- line 279: "how future satisfied capability outcome should reopen"으로 동일 프레이밍
- 동일 파일 line 320-340에서 이미 shipped로 기술
- PRODUCT_SPEC, NEXT_STEPS, TASK_BACKLOG 모두 이미 shipped 프레이밍 완료

## 핵심 변경
- line 270-271: "no reviewed-memory apply" 제거 + "apply/emitted-transition vocabulary is now shipped above this layer", "before ... reopens" → "are now fixed and shipped"
- line 278-279: "still not apply, not emitted transition record" → "apply path and emitted transition record are now shipped above the readiness layer", "how future ... should reopen" → "shipped capability outcome is now fixed"

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 4줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — MILESTONES의 apply/emitted "reopen" 프레이밍 진실 동기화 완료
