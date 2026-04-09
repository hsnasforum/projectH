# docs: NEXT_STEPS TASK_BACKLOG reviewed-memory apply-result absence truth sync

## 변경 파일
- `docs/NEXT_STEPS.md` — 1곳(line 399): boundary draft의 apply result 부재 문구 수정
- `docs/TASK_BACKLOG.md` — 1곳(line 347): boundary draft의 apply result 부재 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `docs/PRODUCT_SPEC.md:1540`과 `docs/ACCEPTANCE_CRITERIA.md:923`/`930`에서 이미 reviewed-memory apply result (apply / stop-apply / reversal / conflict-visibility)가 출하 상태로 기술됨
- 이전 라운드에서 PRODUCT_SPEC과 ACCEPTANCE_CRITERIA의 동일 패턴 잔여 문구 10곳을 수정 완료
- NEXT_STEPS와 TASK_BACKLOG에 남은 마지막 2곳도 동일하게 "no apply result"로 적어 shipped truth와 충돌

## 핵심 변경
- NEXT_STEPS:399 — "no apply result" → "reviewed-memory apply result is shipped separately above the capability path; boundary draft does not carry it"
- TASK_BACKLOG:347 — "no apply result" → "reviewed-memory apply result is shipped separately above the capability path; boundary draft does not carry it"
- boundary draft가 read-only이고 apply result를 직접 포함하지 않는다는 보수적 의미 보존
- literal id, shipped enum value, 기존 계약 구조 변경 없음

## 검증
- `git diff -- docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` — 2줄 변경 확인
- `rg -n 'no apply result' docs/NEXT_STEPS.md docs/TASK_BACKLOG.md` — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 root docs의 reviewed-memory apply-result absence 진실 동기화 완료 (PRODUCT_SPEC, ACCEPTANCE_CRITERIA, NEXT_STEPS, TASK_BACKLOG 모두 수정됨)
