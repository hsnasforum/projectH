# Docs claim-coverage focus-slot explanation state-granularity truth sync

## 변경 파일

- `README.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`
- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

shipped 브라우저 동작은 focus-slot에 대해 4가지 상태(reinforced, regressed, still single-source, still unresolved)를 구분하여 설명하지만, 다수 문서가 `improved/regressed/unchanged`로 3-state 요약하고 있어 `docs/PRODUCT_SPEC.md:291`과 `docs/ACCEPTANCE_CRITERIA.md:41`의 authoritative 4-state 기술과 불일치했음.

## 핵심 변경

8개 문서에서 `improved/regressed/unchanged` → `reinforced / regressed / still single-source / still unresolved` 일괄 교체. 총 12개 occurrence.

## 검증

- `rg -n "improved/regressed/unchanged"`: 대상 8개 문서에서 0건 확인
- `rg -c "reinforced / regressed / still single-source / still unresolved"`: 8개 파일, 12건 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- work/verify 노트는 과거 기록이므로 구 문구가 남아 있으나, historical record로서 의도적 미수정.
- claim-coverage focus-slot 문서 동기화는 이번 슬라이스로 전체 계층에서 완료됨.
