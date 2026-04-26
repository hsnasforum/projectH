# 2026-04-26 M42 doc-sync architecture

## 변경 파일
- `docs/ARCHITECTURE.md`
- `docs/MILESTONES.md`

## 사용 skill
- `doc-sync`: M42 Axis 1의 preference payload 및 PreferencePanel status filter 계약을 현재 구현 기준으로 문서에 반영했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- M42 Axis 1 구현 커밋 후 `list_preferences_payload()`의 status count payload와 PreferencePanel status filter 계약이 `docs/ARCHITECTURE.md`에 아직 반영되지 않았다.
- `docs/MILESTONES.md`의 Next 3 Implementation Priorities에 이미 완료된 M42 Axis 1 및 watcher_core re-export 항목이 남아 있어 현재 우선순위와 맞지 않았다.

## 핵심 변경
- `docs/ARCHITECTURE.md`의 `list_preferences_payload()` 단락 원문을 보존하고 `active_count`, `candidate_count`, `paused_count` integer count 계약을 추가했다.
- 같은 단락에 PreferencePanel 전체/후보/활성/일시중지 status filter tab과 per-tab count 표시 계약을 추가했다.
- rejected preference는 선택된 tab과 무관하게 목록에서 항상 숨겨진다는 UI 계약을 명시했다.
- `docs/MILESTONES.md`의 Next 3 Implementation Priorities에서 완료된 M42 Axis 1 및 watcher_core re-export 항목을 제거했다.
- E2E 환경 개선 검증 항목을 1번으로 승격하고, M43 방향 확정 및 ARCHITECTURE.md M42 doc-sync 항목을 새 2, 3번으로 정리했다.
- 코드와 테스트 파일은 변경하지 않았다.

## 검증
- `git diff --check -- docs/ARCHITECTURE.md docs/MILESTONES.md` 통과, 출력 없음.
- `python3 -m py_compile app/handlers/preferences.py` 통과, 출력 없음.
- `git diff -- docs/ARCHITECTURE.md docs/MILESTONES.md`로 변경 범위가 handoff의 두 문서에만 해당함을 확인했다.
- `git diff --check -- docs/ARCHITECTURE.md docs/MILESTONES.md work/4/26/2026-04-26-m42-doc-sync-architecture.md` 통과, 출력 없음.

## 남은 리스크
- 이번 라운드는 문서 전용 handoff였으므로 unit 전체, browser/E2E, release gate는 실행하지 않았다.
- `docs/MILESTONES.md`의 새 3번 항목은 이번 라운드에서 완료된 내용을 가리키므로, 다음 verify/handoff lane에서 우선순위 정리 여부를 판단해야 한다.
- 기존 작업트리의 untracked `report/gemini/**` 파일들은 이번 handoff 범위 밖이므로 수정하지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
