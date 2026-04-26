# 2026-04-26 operator attention release-gate labels

## 변경 파일
- `controller/js/cozy.js`
- `e2e/tests/controller-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`
- `work/4/26/2026-04-26-operator-attention-release-gate-labels.md`

## 사용 skill
- `frontend-skill`: controller Office View의 operator attention board가 운영 도구 화면 안에서 과장 없이 읽히도록 UI 표현 범위를 정했습니다.
- `work-log-closeout`: 실제 변경 파일, 검증, 남은 리스크를 이 `/work` closeout으로 정리했습니다.

## 변경 이유
- operator attention board가 lane 없는 `m37_commit_push_milestones_doc_sync` 같은 release-gate stop을 generic `운영자 개입 필요`와 raw `runtime status reason_code=...`로 보여 주면, 운영자가 왜 멈췄는지 즉시 알기 어렵습니다.
- 인증/login stop뿐 아니라 커밋, push, 문서 동기화 같은 operator-only 경계도 메인 보드에서 사람이 읽을 수 있는 사유와 대상으로 표시해야 합니다.

## 핵심 변경
- `commit + push`, `doc_sync`, `commit + push + doc_sync` reason 패턴을 공통 helper로 해석해 각각 `커밋/푸시 승인 필요`, `문서 동기화 승인 필요`, `커밋/푸시 문서 동기화 승인 필요`로 표시하게 했습니다.
- lane이 없는 publish/doc-sync stop은 대상이 `—`로 비지 않고 `Repository / release gate`로 표시되게 했습니다.
- explicit evidence가 없는 release-gate stop은 raw `runtime status reason_code=...` 대신 승인 경계를 설명하는 fallback 문장을 보여 주게 했습니다.
- `Refresh` 버튼은 live monitor 연결 상태에서도 강제로 `/api/runtime/status`와 monitor snapshot을 다시 조회하고, 버튼 상태와 Quest Log에 refresh 결과를 남기게 했습니다.
- Playwright controller smoke에 lane 없는 `m37_commit_push_milestones_doc_sync` fixture를 추가해 title, target, decision, evidence, disabled terminal action, live monitor 상태에서의 refresh click을 검증했습니다.
- README와 현재 제품/수용/백로그 문서를 operator attention board의 repository release-gate fallback 및 smoke coverage에 맞췄습니다.

## 검증
- `node --check controller/js/cozy.js`
  - 통과, 출력 없음.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "commit push doc-sync" --reporter=line`
  - 통과.
  - `1 passed (6.8s)`
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "operator attention" --reporter=line`
  - 통과.
  - `2 passed (8.4s)`
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.028s`
- `git diff --check -- controller/js/cozy.js e2e/tests/controller-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 통과, 출력 없음.

## 남은 리스크
- 전체 `make controller-test`는 실행하지 않았습니다. 변경이 operator attention board helper와 해당 board smoke에 한정되어 `operator attention` 관련 2개 시나리오와 문법/doc-sync 체크로 좁혔습니다.
- Playwright 실행 중 기존 환경 경고인 `NO_COLOR` / `FORCE_COLOR` warning이 출력됐지만 테스트 실패에는 영향을 주지 않았습니다.
- 작업 전부터 있던 `e2e/tests/web-smoke.spec.mjs`, `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 기존 미추적 `work/`/`verify/` 파일들은 이번 변경 범위가 아니라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
