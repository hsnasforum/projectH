# 2026-04-19 CONFLICT docs truth-sync bundle

## 변경 파일
- docs/ACCEPTANCE_CRITERIA.md
- docs/TASK_BACKLOG.md
- docs/MILESTONES.md

## 사용 skill
- release-check: docs-only bundle에 맞춰 `git diff --check`와 scoped `grep`만 실행하고, 코드 테스트를 돌리지 않은 이유를 정직하게 분리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서와 실제 실행 결과를 저장소 규약에 맞춰 정리했습니다.

## 변경 이유
- seq 366 → seq 369 → seq 376 → seq 377 → seq 378로 `CoverageStatus.CONFLICT` family의 server/storage/browser surface는 닫혔지만, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`에는 아직 `정보 상충`이 독립 상태로 드러난 현재 shipped contract가 충분히 반영되지 않은 문장이 남아 있었습니다.
- 이번 라운드는 handoff 범위대로 user-facing docs 3개만 최소 수정해, claim-coverage / fact-strength / history-card / live-session summary에서 이미 shipped된 CONFLICT visibility를 과장 없이 맞추는 데 목적이 있었습니다.

## 핵심 변경
- `docs/ACCEPTANCE_CRITERIA.md`
  - line 35 성격의 current contract 문장을 업데이트해 claim-coverage slot status tag를 `[교차 확인] / [정보 상충] / [단일 출처] / [미확인]`으로 맞췄고, focus-slot explanation은 기존 `reinforced / regressed / still single-source / still unresolved` 4-way naming을 유지한 채 sources가 어긋날 때 `정보 상충` wording이 별도로 드러난다고 명시했습니다.
  - line 48 성격의 focus-slot explanation 문장은 `정보 상충`이 `still single-source`나 `still unresolved`에 암묵적으로 접히지 않도록, explicit `정보 상충` state가 남을 수 있다고 분리해 적었습니다.
  - line 49 성격의 response-body header 문장은 실제 구현 기준으로만 적었습니다. `[정보 상충]` response-body header tag는 **추가하지 않았고**, `core/agent_loop.py` / `core/web_claims.py`가 현재 `확인된 사실 [교차 확인]:`, `단일 출처 정보 [단일 출처] (추가 확인 필요):`, `확인되지 않은 항목 [미확인]:`만 emit하므로, `정보 상충`은 count summary / history-card·live-session `.meta` / fact-strength bar / focus-slot explanation에서만 드러난다고 명시했습니다.
- `docs/TASK_BACKLOG.md`
  - line 25 인접의 implemented bullet 하나만 수정해, shipped fact-strength summary bar가 generic phrasing이 아니라 4-segment bar(`교차 확인 / 정보 상충 / 단일 출처 / 미확인`)임을 분명히 적었습니다.
- `docs/MILESTONES.md`
  - line 50 인접 claim-coverage smoke 묶음 옆에 2개 bullet을 추가했습니다:
    - `fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다`
    - `live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다`
  - line 150 인접 history-card `.meta` count-summary composition bullet 옆에 1개 bullet을 추가했습니다:
    - `history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다`
  - 기존 3-state MILESTONES bullet은 renumber/rewrite하지 않았고, 새 bullet만 인접 위치에 추가했습니다.
- `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`는 seq 376에서 이미 동기화된 상태라 이번 라운드에서 의도적으로 수정하지 않았습니다.
- 이번 라운드에서는 source code, test file, 그리고 위 3개 외 다른 markdown 파일을 수정하지 않았습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, 통과
- `grep -nE "정보 상충|CoverageStatus\.CONFLICT|CONFLICT|\"conflict\"" docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과:
    - `docs/MILESTONES.md:51:- \`fact-strength bar는 conflict badge를 교차 확인과 단일 출처 사이에 렌더링합니다\` ... no regression to the pre-CONFLICT 3-badge composition`
    - `docs/MILESTONES.md:52:- \`live-session answer meta는 conflict claim coverage를 정보 상충 segment로 렌더링합니다\` ... \`사실 검증 교차 확인 1 · 정보 상충 1 · 단일 출처 1 · 미확인 1\` ...`
    - `docs/MILESTONES.md:151:- \`history-card summary가 non-zero conflict count를 정보 상충 segment로 렌더링합니다\` ... \`사실 검증 교차 확인 1 · 정보 상충 2 · 단일 출처 1\` ...`
    - `docs/TASK_BACKLOG.md:25:11. Claim coverage panel ... a 4-segment color-coded fact-strength summary bar (\`교차 확인 / 정보 상충 / 단일 출처 / 미확인\`) ...`
    - `docs/ACCEPTANCE_CRITERIA.md:35:- claim coverage or verification state ... (\`[교차 확인]\`, \`[정보 상충]\`, \`[단일 출처]\`, \`[미확인]\`) ... with explicit \`정보 상충\` wording ...`
    - `docs/ACCEPTANCE_CRITERIA.md:48:- ... remains in an explicit \`정보 상충\` state.`
    - `docs/ACCEPTANCE_CRITERIA.md:49:- ... Current implementation does not emit a dedicated \`[정보 상충]\` response-body header tag; \`정보 상충\` is currently surfaced ...`
- 코드 테스트/Playwright 미실행
  - 이번 라운드는 handoff scope가 docs-only truth-sync bundle이고 source code/test file을 전혀 건드리지 않았기 때문에, `tests.test_web_app`나 Playwright는 요구되지 않았고 실행하지 않았습니다.

## 남은 리스크
- `core/agent_loop.py`의 CONFLICT-specific focus_slot wording strengthening은 이번 라운드에서도 문서만 맞춘 상태이며, 별도 future round 후보로 남아 있습니다.
- Milestone 4의 새 sub-axis(`source role labeling/weighting`, `strong vs weak vs unresolved separation beyond CONFLICT`)는 이번 라운드 범위 밖이며 여전히 separate candidate입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family(`LocalOnlyHTTPServer` bind `PermissionError`, `SQLiteSessionStore._compact_summary_hint_for_persist` 누락)는 이번 docs-only 슬라이스와 무관하며 여전히 범위 밖입니다.
- `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`에는 이번 라운드와 무관한 선행 dirty hunk가 이미 있었고, 이번 작업은 handoff가 지정한 CONFLICT-family sentence/bullet 범위만 확장했습니다.
