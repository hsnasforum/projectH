# ACCEPTANCE_CRITERIA + PRODUCT_SPEC Web Investigation agreement/reinvestigation wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill

- 없음 (문서 전용 슬라이스)

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:53-54`의 In Progress 항목 2개(agreement-over-noise, weak-slot reinvestigation)와 `docs/PRODUCT_SPEC.md:315-317`의 In Progress 항목 3개(source consensus, weak-slot reinvestigation, noisy source suppression)가 이미 출하된 구현임에도 In Progress로 남아 있었음. 코드 확인 결과:
- `core/agent_loop.py:3967-3995`: consensus items 우선, single-source capped
- `core/agent_loop.py:2448-2483`: weak/missing slots 우선 reinvestigation
- `core/agent_loop.py:4124-4160`: weak slots `rendered_as = "uncertain"`
- `tests/test_smoke.py`, `tests/test_web_app.py`에서 다수 테스트로 잠금

## 핵심 변경

### ACCEPTANCE_CRITERIA
1. **Implemented (lines 40-41, 신규)**: agreement-over-noise 및 weak-slot reinvestigation 불릿 2개 추가
2. **In Progress (line 55)**: 기존 2개 항목 제거, `TASK_BACKLOG` 참조 문구로 대체

### PRODUCT_SPEC
1. **Implemented (lines 313-314, 신규)**: agreement-over-noise baseline 및 weak-slot reinvestigation baseline 불릿 2개 추가
2. **In Progress (line 317)**: 기존 3개 항목 제거, `TASK_BACKLOG` 참조 문구로 대체

## 검증

- `git diff -- docs/ACCEPTANCE_CRITERIA.md`: Implemented에 2줄 추가, In Progress에서 2줄 제거 + 1줄 참조 추가
- `git diff -- docs/PRODUCT_SPEC.md`: Implemented에 2줄 추가, In Progress에서 3줄 제거 + 1줄 참조 추가
- `git diff --check`: 양쪽 모두 whitespace 에러 없음
- 핵심 라인 범위 확인: ACCEPTANCE_CRITERIA:37-56, PRODUCT_SPEC:307-320

## 남은 리스크

- `docs/TASK_BACKLOG.md:102-105`의 Current Phase In Progress 항목은 미래 품질 개선 방향으로 그대로 유지됨 (이 슬라이스 범위 밖).
- 웹 조사 관련 docs truth-sync 계열이 이제 전체 문서에 걸쳐 완료됨.
