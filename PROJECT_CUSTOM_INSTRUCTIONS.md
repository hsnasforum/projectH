이 저장소는 **로컬 퍼스트 문서 비서 웹 MVP**입니다.

다만 장기 북극성은 단순 문서 비서가 아니라, 사용자가 하나씩 가르치고 나중에는 프로그램 조작까지 확장할 수 있는 **학습 준비형 로컬 개인 에이전트**입니다.
현재 단계는 그 장기 목표를 위한 첫 단계이며, 아직 프로그램 조작이나 모델 자체 학습을 구현한 상태는 아닙니다.

현재 구현 기준의 중심은 아래입니다.
- 로컬 웹 셸
- 최근 세션 / 타임라인
- 파일 요약 / 문서 검색 / 일반 채팅
- 승인 기반 저장
- approval 재발급(reissue) 흐름
- 근거/출처 패널
- 요약 반영 구간 패널
- response origin 배지
- 스트리밍 진행 표시와 취소
- PDF text-layer 읽기와 OCR 미지원 안내
- 권한 게이트 기반 웹 조사와 로컬 JSON 기록
- claim coverage / verification 상태와 검색 기록 재활용
- Playwright 스모크 검증

항상 아래 원칙을 따르세요.

## 1. 범위를 함부로 넓히지 않습니다
- 현재 제품의 중심은 `로컬 문서 비서`입니다.
- 웹 검색은 보조 조사 기능입니다.
- 범용 지식 챗봇 경쟁처럼 범위를 넓히지 않습니다.
- 장기 목표가 개인 에이전트라고 해도, 현재 단계 문서에서는 `현재 구현`과 `장기 목표`를 반드시 분리해서 씁니다.

## 2. 로컬 우선 원칙을 유지합니다
- 기본 동작은 로컬 파일과 로컬 저장을 우선합니다.
- 모델, 런타임, 저장 구조는 교체 가능하게 유지합니다.
- 특정 공급자나 특정 모델명을 제품 기본값처럼 강제하지 않습니다.
- 사용자의 교정, 승인, 선호 정보가 나중에 개인화 자산이 될 수 있도록 구조화 가능성을 열어 둡니다.

## 3. 안전성을 우선합니다
- 파일 저장은 승인 없이 실행하지 않습니다.
- overwrite / delete / move / shell 실행 / 외부 네트워크는 위험 작업입니다.
- 웹 검색은 읽기 전용 + 권한 게이트 + 로컬 기록 유지 원칙을 지킵니다.
- OCR은 아직 미지원이며, 조용히 실패시키지 않습니다.
- 장기적으로 프로그램 조작을 하더라도 승인, 감사 가능성, 가시성 없는 자동 행동은 허용하지 않습니다.

## 4. 문서와 구현을 같이 유지합니다
- UI 동작이 바뀌면 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`를 같이 봅니다.
- approval payload나 session schema가 바뀌면 `docs/ARCHITECTURE.md`도 같이 갱신합니다.
- 테스트 시나리오가 바뀌면 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`도 같이 맞춥니다.
- 에이전트/스킬 설정이 바뀌면 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.codex/config.toml`, 대응되는 agent/skill 파일을 같이 맞춥니다.
- `/work` closeout 규칙이나 `/verify` verification 규칙이 바뀌면 `work/README.md`, `verify/README.md`도 같이 갱신합니다.
- `.pipeline/gpt_prompt.md`, `.pipeline/codex_feedback.md` 같은 rolling handoff 슬롯 규칙이 바뀌면 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `work/README.md`, `verify/README.md`, 필요 시 `.pipeline/README.md`도 같이 갱신합니다.
- 장기 로드맵이나 단계 정의가 바뀌면 `plandoc/` 문서도 같이 맞춥니다.

## 5. 운영 보조 에이전트와 스킬도 제품 범위를 따라갑니다
- 새 agent는 반복적으로 발생하는 저장소 리스크나 워크플로우에만 추가합니다.
- 현재 저장소에서 특히 가치가 큰 역할은 `planner`, `reviewer`, `spec-editor`, `qa-e2e-reviewer`, `approval-auditor`, `investigation-reviewer`, `documenter`, `trace-implementer`입니다.
- 새 skill은 `.agents/skills/`와 `.claude/skills/`에 거울처럼 유지하고, Codex 기본 사용 대상이면 `.codex/config.toml`에도 등록합니다.
- 웹 조사 품질, 승인 플로우, 문서 동기화, `/work` closeout처럼 현재 저장소의 실제 문제 축에 맞는 skill을 우선합니다.
- 최신 `/work` closeout 재검증과 다음 라운드 지시사항 작성처럼 반복되는 handoff 정리는 `round-handoff` 같은 좁은 skill로 표준화하고, 기존 `documenter` 역할과 중복되는 새 agent는 쉽게 늘리지 않습니다.
- 장기 방향을 다루는 planning 계열 문서는 “지금 구현된 것”과 “장기 북극성”을 섞지 않게 설계합니다.
- `trace-implementer`는 grounded-brief trace anchor, snapshot normalization, corrected-outcome linkage 같은 작은 구현 슬라이스를 맡기되, review queue나 user-level memory 같은 다음 단계 범위를 끌어오지 않도록 제한합니다.

## 6. `/work` / `/verify` 작업기록 규칙
- 의미 있는 구현/운영 작업이 끝나면 `work/<월>/<일>/YYYY-MM-DD-<slug>.md` 형식으로 closeout 메모를 남깁니다.
- 의미 있는 검증 재실행 / truth 재대조 / 다음 라운드 handoff 작업이 끝나면 `verify/<월>/<일>/YYYY-MM-DD-<slug>.md` 형식으로 verification 메모를 남깁니다.
- `.pipeline/codex_feedback.md`는 자동화용 rolling 최신 슬롯이며, 최신 handoff를 편하게 넘기기 위한 보조 수단일 뿐 `/work`와 `/verify`를 대체하지 않습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만 canonical single-Codex 흐름의 필수 단계는 아닙니다.
- 새 라운드를 시작할 때는 오늘 폴더의 최신 메모를 먼저 보고, 없으면 전날 최신 메모를 이어받습니다.
- 검증 라운드를 시작할 때는 최신 `/work` 메모를 먼저 보고, 같은 날짜의 `/verify` 메모가 있으면 그 다음에 이어받습니다.
- 메모에는 최소한 `변경 파일`, `사용 skill`, `변경 이유`, `핵심 변경`, `검증`, `남은 리스크`를 넣습니다.
- 검증 전용 메모에서 파일을 바꾸지 않았다면 `변경 파일`에는 `- 없음`이라고 적습니다.
- 실행하지 않은 검증은 적지 말고, 미실행이면 그대로 남깁니다.

## 6-1. single Codex tmux 운영 규칙
- Codex는 하나의 verification + handoff 레인입니다.
- 권장 흐름은 아래와 같습니다.
  - Claude가 구현 후 `/work`를 남깁니다.
  - Codex가 최신 `/work`, 최신 `/verify`를 읽고 실제 검증을 재실행합니다.
  - Codex가 `/verify`를 남깁니다.
  - Codex가 다음 Claude 지시사항을 `.pipeline/codex_feedback.md`에 씁니다.
- `.pipeline/gpt_prompt.md`는 필요하면 scratch나 legacy 호환용으로 남길 수 있지만, canonical 흐름의 필수 단계는 아닙니다.
- rolling 슬롯 파일은 매 라운드 덮어써도 되지만, 영속 truth는 항상 `/work`와 `/verify`에 남겨야 합니다.

## 7. 제품 방향 정리 원칙
- 현재 단계의 핵심은 `문서 작업`입니다.
- 다음 단계의 핵심은 `교정/승인/선호를 구조적으로 저장해 다음 답변에 반영하는 것`입니다.
- 장기 단계의 핵심은 `승인 기반 로컬 행동과 프로그램 조작`입니다.
- 그 이후에야 `개인화된 독자 모델` 또는 그에 준하는 적응형 로컬 모델이 의미가 생깁니다.
- 따라서 기획 문서에는 항상 `현재 단계`, `다음 단계`, `장기 단계`를 나눠 적습니다.

## 8. 응답 방식
- 사용자에게는 한국어 존댓말로 답합니다.
- 사실, 가정, 권고를 구분합니다.
- 구현 전/후에는 목표, 영향 파일, 리스크, 검증 결과를 짧게 요약합니다.
