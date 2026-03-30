# 2026-03-26 Product direction doc realignment

## 변경 파일

- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill

- `mvp-scope`: 현재 계약, 다음 단계, 장기 북극성을 섞지 않고 제품 문서 구조를 다시 세우는 기준으로 사용
- `doc-sync`: 실제 구현 기준과 문서 서술이 어긋나지 않게 맞추는 기준으로 사용
- `work-log-closeout`: `/work` closeout 형식과 기록 항목을 저장소 규칙에 맞춰 남기기 위해 사용

## 변경 이유

- 기존 제품 문서들은 현재 문서 비서 MVP와 장기 방향을 다루고 있었지만, `다음 단계`인 교정/승인/선호 메모리 층이 상대적으로 약하게 드러났습니다.
- 일부 문서는 장기 방향을 `proprietary model` 축으로 읽기 쉬워, 사용자가 요청한 `현재 계약 / 다음 단계 / 장기 북극성` 메시지를 일관되게 전달하기 어려웠습니다.
- 이번 라운드의 목적은 구현 범위를 넓히지 않고, 문서 세트를 실행 우선순위 중심으로 재배열하는 것이었습니다.

## 핵심 변경

- `docs/project-brief.md`를 현재 제품 한 줄 정의, 장기 북극성 한 줄 정의, 단계별 이유, 지금 쌓아야 할 데이터 자산, `OPEN QUESTION` 중심으로 재구성했습니다.
- `docs/PRODUCT_PROPOSAL.md`를 문서 비서 중심 제품 논리, 다음 단계 메모리 설계 이유, 프로그램 조작을 뒤로 미루는 이유가 보이도록 다시 정리했습니다.
- `docs/PRODUCT_SPEC.md`에서 현재 구현 계약과 다음 단계 설계 대상, 장기 북극성을 명시적으로 분리하고, 구현된 승인/세션/패널/웹 조사 사실만 남겼습니다.
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`를 현재 단계, 다음 단계, 그 이후 순서로 재배열하고 `다음 구현 우선순위 3개`와 `지금 쌓아야 할 데이터 자산`을 명시했습니다.
- 문서 전반에서 웹 조사를 secondary mode로 유지하고, 모델 학습이나 프로그램 조작을 현재 구현처럼 쓰지 않도록 표현을 조정했습니다.

## 검증

- 실행: `sed -n '1,260p' AGENTS.md`
- 실행: `sed -n '1,260p' CLAUDE.md`
- 실행: `sed -n '1,260p' PROJECT_CUSTOM_INSTRUCTIONS.md`
- 실행: `sed -n '1,260p' plandoc/2026-03-26-teachable-local-agent-roadmap.md`
- 실행: `sed -n '1,260p' README.md`
- 실행: `sed -n '1,320p' docs/PRODUCT_SPEC.md`
- 실행: `sed -n '1,320p' docs/ARCHITECTURE.md`
- 실행: `sed -n '1,260p' app/web.py`
- 실행: `sed -n '1,320p' core/agent_loop.py`
- 실행: `git diff --check -- docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- 실행: `rg -n "One-Line Current Product Definition|One-Line Long-Term North Star|Next 3 Implementation Priorities|Data Assets To Accumulate|OPEN QUESTION|Why The Current|Why The Next Phase|Why Program Operation" docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- 미실행: `python3 -m unittest -v`
- 미실행: `make e2e-test`

## 남은 리스크

- `README.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 현재 계약 문서로서 유지했지만, 이후 제품 방향 설명을 더 넓게 맞출 필요가 생기면 추가 정렬이 필요할 수 있습니다.
- `교정/승인/선호 메모리`의 실제 저장 단위와 승격 규칙은 아직 문서상 `OPEN QUESTION`이며, 구현 전 스키마 합의가 필요합니다.
- 프로그램 조작의 첫 대상 표면은 아직 정해지지 않았으므로, 다음 단계 이후 로드맵은 의도적으로 설계 목표 수준에 머물러 있습니다.
