# 2026-05-12 M123 아크 종료 doc-sync

## 변경 파일

- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/5/12/2026-05-12-m123-arc-closure-doc-sync.md`

## 사용 skill

- `doc-sync`: M123 Axis 1–3 publish 완료와 M124 전환 방향을 현재 문서 truth에 맞게 반영했습니다.
- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1597의 M123 아크 종료 doc-sync 지시를 실행했습니다.
- advisory CONTROL_SEQ 1596의 `close_arc_m123` 추천에 따라 M123 아크 종료와 M124 Investigation Observability & Metrics 전환 대기를 문서화했습니다.

## 핵심 변경

- `docs/MILESTONES.md`의 M123 섹션 말미에 Axis 1–3 published 및 M124 전환 요약 단락을 추가했습니다.
- `docs/MILESTONES.md`의 Next 3 첫 항목을 M123 아크 완전 종료와 M124 시작 대기 상태로 갱신했습니다.
- `docs/TASK_BACKLOG.md`에 `#147` M123 아크 종료 완료 항목을 추가했습니다.
- handoff 금지 범위에 따라 코드·테스트 파일, `.pipeline/`, frontend, E2E, commit/push/PR은 건드리지 않았습니다.

## 검증

- PASS: `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- PASS: `rg "M123 아크 완료|M123 아크 완전 종료|M124" docs/MILESTONES.md`
- PASS: `rg "^147\. M123 아크|M123 아크 종료" docs/TASK_BACKLOG.md`

## 남은 리스크

- PR #122–#124를 포함한 PR 스택 merge gate는 operator 결정 영역으로 남아 있습니다.
- docs-only 변경이므로 `python3 -m unittest`, Playwright, E2E는 재실행하지 않았습니다.
