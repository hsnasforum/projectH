# 2026-04-28 M49 Axis 1 preference application contract

## 변경 파일

- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/4/28/2026-04-28-m49-axis1-preference-application-contract.md`

## 사용 skill

- `work-log-closeout`: 구현 소유자 라운드 종료 기록의 필수 항목과 실제 검증 결과를 맞추기 위해 사용.

## 변경 이유

`CONTROL_SEQ 1152` handoff가 M49 Axis 1을 구현 없는 docs-first 계약 정의로 지정했다. ACTIVE 선호도를 모델 프롬프트에 주입하기 전, 주입 대상과 포맷, 적용 범위, approval 경계를 문서상 계약으로 먼저 고정해야 했다.

## 핵심 변경

- `docs/MILESTONES.md`의 M48 항목 뒤에 `M49 Cross-session Preference Application` 항목을 추가했다.
- M49 Axis 1을 `선호도 프롬프트 주입 계약 및 스키마 확정 — ACTIVE`로 표시했다.
- `docs/TASK_BACKLOG.md`에 `M49 Direction Candidates`와 `M49 Axis 1: 선호도 프롬프트 주입 계약 정의`를 추가했다.
- 계약 표면을 ACTIVE + `is_highly_reliable=True` 기본 주입 대상, 시스템 프롬프트 텍스트 스키마, document summary / chat 한정 적용, 웹 조사 미적용, 기존 approval-based save 경계 유지로 정리했다.
- 실제 프롬프트 주입, `record_reviewed_candidate_preference` 경로 수정, cross-session counting 확장, 승인 경계 수정은 금지 항목으로 남겼다.
- 선택적 코드 스텁은 추가하지 않았다. 이번 handoff의 docs-first 계약은 두 문서 변경으로 충분하다고 판단했다.

## 검증

- PASS: `sha256sum .pipeline/implement_handoff.md` 결과가 요청된 `dfdcac040f28f0a2850daf6ed090f92163942507920a96072b9bf0e6171b7ce3`와 일치.
- PASS: `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- PASS(no whitespace diagnostics): `git diff --no-index --check /dev/null work/4/28/2026-04-28-m49-axis1-preference-application-contract.md` (exit 1은 `/dev/null`과 새 파일 비교 때문)
- PASS: `grep -n "M49\|preference.*inject\|주입.*계약" docs/MILESTONES.md docs/TASK_BACKLOG.md`
- 미실행: `python3 -m py_compile storage/preference_application.py`는 선택적 스텁을 추가하지 않아 실행하지 않음.

## 남은 리스크

- 이번 라운드는 계약 문서화만 수행했다. ACTIVE 선호도 프롬프트 주입 구현과 런타임 검증은 Axis 2 이후 작업으로 남아 있다.
- 기존 approval, storage, preference lifecycle 경계는 변경하지 않았다.
- commit, push, branch/PR publish는 수행하지 않았다.
