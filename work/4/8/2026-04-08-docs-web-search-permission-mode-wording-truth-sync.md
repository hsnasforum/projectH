# Docs web-search permission-mode wording truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- 없음

## 변경 이유

다수 product-layer 문서가 web-search permission 모드를 `enabled/disabled/ask per session`으로 기술하고 있었으나, 실제 shipped enum(`core/contracts.py:149-152`)은 `disabled` / `approval` / `enabled`임. `ask`는 코드에 존재하지 않는 값이었음.

## 핵심 변경

6개 문서, 총 11곳에서 `enabled/disabled/ask per session` → `disabled/approval/enabled per session` 교체.

## 검증

- `rg -n "enabled/disabled/ask"`: 대상 6개 문서에서 0건 확인
- `rg -c "disabled/approval/enabled per session"`: 6개 파일, 11건 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`에서 동일 문구가 있는지 확인 필요 (이번 슬라이스 범위 밖).
