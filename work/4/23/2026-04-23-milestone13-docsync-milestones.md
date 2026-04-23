# 2026-04-23 Milestone 13 doc-sync milestones

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-milestone13-docsync-milestones.md` (이 파일)

## 사용 skill
- `doc-sync`: M13 Axis 1 구현 사실과 가드레일을 현재 milestone 문서에 맞췄다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- CONTROL_SEQ 959 handoff에 따라 M12 close 이후 다음 milestone인 M13을 `docs/MILESTONES.md`에 정의했다.
- M13 Axis 1 commit `8cea2f1`의 applied preference tracking 변경이 코드에는 반영됐지만 milestone 문서에는 아직 없어서 bounded docs sync로 보완했다.

## 핵심 변경
- `docs/MILESTONES.md`의 Milestone 12 close record 바로 다음에 `Milestone 13: Applied Preference Effectiveness Tracking` 항목을 추가했다.
- M13 목적을 active preference 적용 추적, 이후 correction 개선 측정, safety loop 검증 전 자동화 확장 금지로 정리했다.
- 가드레일을 명시했다: repeated-signal promotion은 safety loop 검증 전 blocked, cross-session counting은 later, CANDIDATE → ACTIVE auto-activation은 deferred.
- Axis 1 shipped infrastructure를 추가했다: `8cea2f1`, seq 958, `app/handlers/chat.py`의 `applied_preference_ids` 저장, `storage/session_store.py`의 `stream_trace_pairs()` yield, 57 unit tests.
- 코드 파일, `.pipeline` control slot, `preference_store.py`, `correction_store.py`는 수정하지 않았다.

## 검증
- `python3 -m py_compile docs/MILESTONES.md 2>/dev/null || true`
  - 명령 완료, 출력 없음
- `grep -n "Milestone 13" docs/MILESTONES.md`
  - `494:### Milestone 13: Applied Preference Effectiveness Tracking`
- `git diff --check -- docs/MILESTONES.md`
  - 통과, 출력 없음

## 남은 리스크
- 이번 round는 docs-only handoff라 코드와 테스트는 실행하지 않았다.
- M13의 다음 축 선택, safety loop 검증 방식, PR/merge 결정은 이번 implement lane 범위 밖이다.
- 기존 untracked `work/4/23/2026-04-23-milestone13-axis1-commit-push.md`는 선행 commit/push closeout으로 남아 있으며 이번 round에서 수정하지 않았다.
- 커밋, 푸시, PR 생성, next-slice 선택, `.pipeline` control slot 작성은 수행하지 않았다.
