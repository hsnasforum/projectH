# 2026-04-28 M53 Axis 1 TASK_BACKLOG stale 항목 현행화

## 변경 파일

- `docs/TASK_BACKLOG.md`
- `work/4/28/2026-04-28-m53-axis1-task-backlog-stale-sync.md`

## 사용 skill

- `doc-sync`: handoff가 지정한 `docs/TASK_BACKLOG.md` 두 stale 항목만 현재 구현 truth에 맞게 좁게 갱신했습니다.
- `work-log-closeout`: 문서 현행화 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M49-M52에서 cross-session preference application, prompt injection, visibility, reliability tracking, explicit correction feedback가 구현되었고, M37에서 corrections store가 SQLite로 이동했지만 `docs/TASK_BACKLOG.md`에는 일부 이전 상태가 남아 있었습니다. 이번 slice는 handoff가 지정한 두 stale 문구만 제거했습니다.

## 핵심 변경

- `Not Implemented`의 `durable preference memory` 항목을 partial 상태로 바꾸고, M49의 ACTIVE+`is_highly_reliable=True` 주입 및 M50-M52 visibility/reliability/feedback 완료 사실을 반영했습니다.
- `Partial / Opt-In`의 SQLite backend 항목에서 `Corrections store is still JSON-only.` 문구를 제거했습니다.
- 같은 SQLite backend 항목에 `Corrections store migrated to SQLite via SQLiteCorrectionStore (M37).` 문구를 추가했습니다.
- 긴 Browser-level parity gate 설명과 `Implemented` 목록은 변경하지 않았습니다.

## 검증

- `python3 -c "..."`
  - `PASS`
  - stale 문구 `prompt injection of newly recorded candidates remain future` 없음 확인
  - stale 문구 `Corrections store is still JSON-only` 없음 확인
  - `SQLiteCorrectionStore` 또는 `Corrections store migrated` 문구 존재 확인
- `git diff --check -- docs/TASK_BACKLOG.md`
  - 통과

## 남은 리스크

- 이번 handoff는 `docs/TASK_BACKLOG.md` 단일 파일 현행화만 요구했기 때문에 code, dist, E2E, `docs/MILESTONES.md`는 변경하지 않았습니다.
- 별도 unit/E2E 검증은 실행하지 않았습니다.
