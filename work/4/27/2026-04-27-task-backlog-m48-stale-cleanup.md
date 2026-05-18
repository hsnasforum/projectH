# 2026-04-27 TASK_BACKLOG M48 stale cleanup

## 변경 파일
- `docs/TASK_BACKLOG.md`
- `work/4/27/2026-04-27-task-backlog-m48-stale-cleanup.md`

## 사용 skill
- `doc-sync`: M48 A1/A2 shipped 이후 남은 backlog 문구를 현재 구현 truth에 맞춰 제거하는 범위인지 확인했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남기는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 502 handoff는 `docs/TASK_BACKLOG.md`의 `M48 Direction Candidates` 섹션에서 M48 A1/A2 shipped 이후 스테일이 된 두 항목만 제거하라고 지정했다.
- Candidate B의 cross-session preference schema design은 장기 north-star 방향으로 아직 유효하므로 유지했다.

## 핵심 변경
- `M48 Direction Candidates`에서 `conflict detection improvement` 후보를 제거했다.
- `M48 Axis 1 should be confirmed through advisory...` 확인 항목을 제거했다.
- 같은 섹션 제목은 유지하고 Candidate B만 남겼다.
- 코드, 다른 docs, `.pipeline/`, `verify/`는 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `851f542b3f4c8eec33e5e2fa194f930475d68c86e09e9a3fd7bd54c6575bc9ef`.
- `sed -n '1,220p' work/4/27/2026-04-27-m48-axis2-doc-sync.md` 확인.
- `sed -n '1,220p' verify/4/27/2026-04-27-m48-axis2-doc-sync.md` 확인.
- `git diff --check -- docs/TASK_BACKLOG.md` 통과.
- `grep -n "M48\|conflict detection improvement\|Axis 1 should be confirmed" docs/TASK_BACKLOG.md` 결과에서 스테일 문구 없음 확인.
- `grep -n "Candidate B\|cross-session preference schema" docs/TASK_BACKLOG.md`로 Candidate B 유지 확인.
- `if grep -n "conflict detection improvement\|Axis 1 should be confirmed" docs/TASK_BACKLOG.md; then exit 1; else echo stale-items-absent; fi` 통과.

## 남은 리스크
- docs-only cleanup이라 코드 테스트, unittest, Playwright는 실행하지 않았다.
- 이번 implement lane에서는 commit, push, branch/PR publish, merge를 수행하지 않았다.
- PR #45 merge 및 후속 control 작성은 이번 handoff 범위 밖이다.
