# TASK_BACKLOG Web Investigation wording clarification

날짜: 2026-04-08

## 변경 파일

- `docs/TASK_BACKLOG.md` (lines 7, 23, 24)

## 사용 skill

- 없음 (docs-only 최소 범위 수정)

## 변경 이유

`docs/TASK_BACKLOG.md`의 Current Product Identity (line 7)과 Implemented 목록 (lines 23-24)이 web investigation을 generic하게만 기술하고 있어, 이미 shipped된 permission states, document-first guardrail, history reload/badges, answer-mode distinction, strong-badge downgrade, claim-coverage panel 세부 사항을 직접 드러내지 못했습니다. `docs/PRODUCT_SPEC.md:151-155`, `docs/NEXT_STEPS.md:15`, `docs/ACCEPTANCE_CRITERIA.md:37` 등의 source-of-truth과 일치하도록 최소 범위로 갱신했습니다.

## 핵심 변경

line 7 기존:
```
- secondary mode: permission-gated web investigation
```
변경:
```
- secondary mode: permission-gated web investigation (enabled/disabled/ask per session) under document-first guardrail
```

line 23 기존:
```
10. Permission-gated web investigation with local history
```
변경:
```
10. Permission-gated web investigation with local JSON history (in-session reload, history-card answer-mode / verification-strength / source-role trust badges), entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
```

line 24 기존:
```
11. Claim coverage and slot reinvestigation scaffolding
```
변경:
```
11. Claim coverage panel with status tags and actionable hints, and slot reinvestigation scaffolding
```

## 검증

- `git diff -- docs/TASK_BACKLOG.md`: 3줄만 변경 확인
- `git diff --check -- docs/TASK_BACKLOG.md`: whitespace 에러 없음
- `nl -ba docs/TASK_BACKLOG.md | sed -n '3,25p'`: 주변 문맥 정상

## 남은 리스크

- `docs/PRODUCT_PROPOSAL.md:26,59,135`도 web investigation을 더 generic하게 기술하고 있으나, 이번 슬라이스 범위 밖입니다.
