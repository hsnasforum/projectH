# 2026-03-31 transcript meta source filename smoke assertion

## 목표
단일 문서 요약 응답의 transcript meta에서 basename(`long-summary-fixture.md`)이 노출되는 현재 shipped 계약을 browser smoke로 고정.

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`: scenario 1에 transcript meta basename assertion 1줄 추가
- `README.md`: smoke scenario 1 설명에 transcript meta filename coverage 반영
- `docs/ACCEPTANCE_CRITERIA.md`: smoke scenario 1 설명에 transcript meta filename coverage 반영
- `docs/MILESTONES.md`: smoke suite 설명에 transcript meta filename coverage 반영
- `docs/TASK_BACKLOG.md`: smoke coverage 설명에 transcript meta filename coverage 반영

## 변경 내용
- 기존 scenario 1(`파일 요약 후 근거와 요약 구간이 보입니다`)에서 `data-testid="transcript-meta"`의 마지막 요소가 `long-summary-fixture.md`를 포함하는지 assert하는 1줄 추가.
- 기존 selector(`data-testid="transcript-meta"`)와 fixture(`long-summary-fixture.md`)를 그대로 재사용, selector 추가 없음.
- 문서 4개에서 "source filename in quick-meta"를 "source filename in both quick-meta and transcript meta"로 truth-sync.

## 검증
- `git diff --check`: whitespace 오류 없음
- `make e2e-test`: 13 passed (전체 통과)

## 리스크
- 없음. 기존 shipped 계약을 그대로 고정하는 assertion이므로 behavior 변경 없음.

## 사용 스킬
- 없음 (직접 편집)
