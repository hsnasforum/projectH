# docs: NEXT_STEPS TASK_BACKLOG aggregate later-stage qualifier truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — line 418: "from later reviewed-memory apply" → "reviewed-memory apply ... are now also shipped"
- `docs/TASK_BACKLOG.md` — line 658: "Keep the first materialization slice narrower than later transition vocabulary" → "The full transition vocabulary is now shipped"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 두 수식어가 apply/stop-apply/reversal/conflict-visibility를 "later" 또는 "narrower than"으로 기술하지만, 동일 섹션 바로 아래에서 이미 shipped로 기술
- 수식어와 내용이 모순하여 혼동 유발
- `docs/PRODUCT_SPEC.md:1531-1537`과 `e2e/tests/web-smoke.spec.mjs:900-966`에서 전체 흐름 출하 확인

## 핵심 변경
- NEXT_STEPS: "from later reviewed-memory apply" 제거, shipped 명시
- TASK_BACKLOG: "narrower than later transition vocabulary" → "full transition vocabulary is now shipped"

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 각 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서의 aggregate 후반 단계 수식어 진실 동기화 완료
