# 2026-03-26 Primary workflow doc sync

## 변경 파일

- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `work/3/26/2026-03-26-primary-workflow-doc-sync.md`

## 사용 skill

- `mvp-scope`: 현재 구현을 기준으로 1차 제품 워크플로우를 좁히고, 지금 MVP와 장기 독자 모델 방향을 분리하기 위해 사용했습니다.
- `doc-sync`: 구현 사실을 넘지 않도록 문서 표현을 정리하고, 지정된 기획 문서 5개를 현재 저장소 상태에 맞추기 위해 사용했습니다.
- `release-check`: 마무리 시 실제 실행한 검증과 미실행 항목을 구분해 기록하기 위해 사용했습니다.
- `work-log-closeout`: 이번 문서 정리 라운드를 `/work` 규칙에 맞는 closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- 현재 저장소는 로컬 퍼스트 문서 비서 웹 MVP이지만, 장기 방향은 독자적 모델 기반 사업입니다.
- 그래서 지금 단계에서 가장 먼저 고정해야 할 것은 범용 챗봇 방향이 아니라, 나중에 독자 모델이 학습하고 평가받을 수 있는 단일 핵심 문서 워크플로우입니다.
- 기존 문서에는 웹 조사 품질 작업이 상대적으로 크게 보였고, 핵심 제품 루프와 장기 사업 방향의 연결이 충분히 명시되어 있지 않았습니다.

## 핵심 변경

- 한 줄 제품 정의를 `로컬 퍼스트 문서 비서 웹 MVP`와 `승인 기반 근거 있는 문서 노트 생성` 중심으로 다시 정리했습니다.
- 1차 핵심 워크플로우를 `grounded document brief loop`로 고정하고, 왜 이것이 사업성, 반복 사용성, 평가 가능성, 독자 모델 차별화 측면에서 1순위인지 문서에 반영했습니다.
- `현재 구현됨 / 진행 중 / 미구현 / 장기 방향만 존재` 구분을 `project-brief`와 `PRODUCT_PROPOSAL`에 명시했습니다.
- `PRODUCT_SPEC`에 현재 구현 커버리지와 미구현 항목을 분리해, 추천 워크플로우가 아직 완성형 구현은 아니라는 점을 분명히 했습니다.
- `MILESTONES`와 `TASK_BACKLOG`를 웹 조사 확장 중심이 아니라 핵심 문서 워크플로우 고정과 eval 자산 축적 우선순위가 보이도록 재정렬했습니다.

## 검증

- `git diff --check -- docs/project-brief.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - tracked 문서 기준 whitespace 오류 메시지 없이 통과했습니다.
- `git diff --check --no-index /dev/null /home/xpdlqj/code/projectH/docs/PRODUCT_PROPOSAL.md`
  - 출력은 없었습니다. 신규 파일을 `/dev/null`과 비교해서 exit code 1이 났지만, 형식 오류 메시지는 없었습니다.
- `git diff --check --no-index /dev/null /home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md`
  - 출력은 없었습니다. 신규 파일을 `/dev/null`과 비교해서 exit code 1이 났지만, 형식 오류 메시지는 없었습니다.
- `git diff --check --no-index /dev/null /home/xpdlqj/code/projectH/work/3/26/2026-03-26-primary-workflow-doc-sync.md`
  - 출력은 없었습니다. 신규 파일을 `/dev/null`과 비교해서 exit code 1이 났지만, 형식 오류 메시지는 없었습니다.

## 남은 리스크

- 이번 라운드는 문서 정리 작업이며, `grounded document brief loop`를 first-class artifact로 만드는 구현은 아직 없습니다.
- 현재 저장 흐름은 요약 노트 저장에 강하고, 후속 메모/액션 아이템 재작성 결과를 별도 산출물로 저장하는 흐름은 아직 미구현입니다.
- dedicated eval harness도 아직 없어서, 문서에서 정의한 성공 기준과 eval 자산은 후속 구현이 필요합니다.
