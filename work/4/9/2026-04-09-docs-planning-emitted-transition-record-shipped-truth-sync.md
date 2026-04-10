# docs: NEXT_STEPS TASK_BACKLOG emitted-transition-record current-shipped wording truth sync

## 변경 파일
- `docs/TASK_BACKLOG.md` — 1곳(line 653): "may materialize only for" → "current shipped ... materializes only for"
- `docs/NEXT_STEPS.md` — 2곳(line 402-403): reviewed-memory apply를 미출하 대상에서 제거, emitted transition record를 "later" → "now shipped alongside"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- TASK_BACKLOG line 653: "may materialize only for"로 약하게 기술
- NEXT_STEPS line 402: reviewed-memory apply를 "do not reopen" 목록에 포함하지만 이미 출하됨
- NEXT_STEPS line 403: emitted transition record를 "later" / "reviewed-memory apply vocabulary"로 프레이밍
- 권위 문서(PRODUCT_SPEC:1529, ARCHITECTURE:1160, ACCEPTANCE_CRITERIA:928, 937)에서 이미 current shipped로 기술

## 핵심 변경
- TASK_BACKLOG: "may materialize only for" → "current shipped ... materializes only for"
- NEXT_STEPS: "reviewed-memory apply" 미출하 목록에서 제거 + "now shipped above the precondition family", "later emitted transition record" → "now shipped alongside"

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서 emitted-transition-record/apply shipped 문구 진실 동기화 완료
