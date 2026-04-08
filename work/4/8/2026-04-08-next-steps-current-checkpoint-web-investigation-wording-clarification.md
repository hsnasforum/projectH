# NEXT_STEPS Current Checkpoint Web Investigation wording clarification

날짜: 2026-04-08

## 변경 파일

- `docs/NEXT_STEPS.md` (line 15)

## 사용 skill

- 없음 (docs-only 단일 줄 수정)

## 변경 이유

`docs/NEXT_STEPS.md:15`의 Current Checkpoint web-investigation bullet이 `guarded secondary mode with local JSON history and claim-coverage state` 수준으로만 기술되어 있어, 이미 shipped된 permission states, history reload/badges, answer-mode distinction, document-first guardrail 등의 세부 사항을 직접 드러내지 못했습니다. `docs/PRODUCT_SPEC.md:151-155`, `docs/PRODUCT_SPEC.md:307-312`, `README.md:68-69`, `docs/ACCEPTANCE_CRITERIA.md:37` 등의 source-of-truth과 일치하도록 최소 범위로 갱신했습니다.

## 핵심 변경

기존:
```
- Web investigation exists as a guarded secondary mode with local JSON history and claim-coverage state.
```

변경:
```
- Web investigation is a permission-gated secondary mode (enabled/disabled/ask per session) under a document-first guardrail, with local JSON history supporting in-session reload and history-card badges (answer-mode, verification-strength, source-role trust), entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade, and a claim-coverage panel with status tags and actionable hints.
```

## 검증

- `git diff -- docs/NEXT_STEPS.md`: line 15 한 줄만 변경 확인
- `git diff --check -- docs/NEXT_STEPS.md`: whitespace 에러 없음
- `nl -ba docs/NEXT_STEPS.md | sed -n '3,16p'`: 주변 문맥 정상

## 남은 리스크

- `docs/TASK_BACKLOG.md:23-24`, `docs/PRODUCT_PROPOSAL.md:26,59,135`도 web investigation을 더 generic하게 기술하고 있으나, 이번 슬라이스 범위 밖입니다.
- line 16 Playwright smoke inventory bullet은 그대로 유지했습니다.
