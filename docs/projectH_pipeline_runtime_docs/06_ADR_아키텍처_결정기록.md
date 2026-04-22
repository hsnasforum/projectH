# projectH Pipeline Runtime ADR (Architecture Decision Record)
버전: v1.1  
작성일: 2026-04-10  
문서 성격: 핵심 설계 결정 기록

## ADR-001. Launcher는 thin client로 축소한다
### 상태
승인 제안

### 배경
현재 launcher는 start/stop UI이면서 동시에 tmux pane, watcher.log, 최신 `work`/`verify` 파일을 읽어 상태를 추정한다.

### 결정
launcher는 command client + status viewer 역할만 수행한다.

### 이유
- 상태 추론 경로 수를 줄인다.
- launcher 교체/확장이 쉬워진다.
- GUI/CLI/controller 간 상태 불일치가 줄어든다.

### 결과
- launcher 코드가 단순해진다.
- supervisor 의존이 생긴다.

## ADR-002. Supervisor를 단일 state writer로 둔다
### 상태
승인 제안

### 배경
여러 프로세스가 상태를 각자 계산하면 split-brain이 생긴다.

### 결정
status/event/receipt는 supervisor가 단일 writer가 된다.

### 이유
- 상태 일관성 확보
- recovery 정책 중앙화
- QA와 운영 관측 단순화

### 결과
- supervisor 안정성이 중요해진다.
- supervisor restart recovery 설계가 필수다.

## ADR-003. tmux는 즉시 제거하지 않고 backend adapter로 남긴다
### 상태
승인 제안

### 배경
tmux는 현재 불안정성의 유일 원인이 아니다. 동시에 attach/debug 효용이 크다.

### 결정
1단계에서는 `TmuxAdapter`를 유지한다.  
단, 상위 계층에서 tmux를 직접 호출하지 않는다.

### 이유
- big bang migration 리스크 축소
- 현재 운영 절차 유지
- PTY 전환을 나중에 lane 단위 pilot으로 검증 가능

### 결과
- tmux 의존은 완전히 사라지지 않는다.
- 그러나 영향 반경을 backend 내부로 제한할 수 있다.

## ADR-004. Round close는 receipt로만 확정한다
### 상태
승인 제안

### 배경
최신 artifact 존재만으로 종료를 판정하면 false close가 발생한다.

### 결정
round 종료는 receipt 기록으로만 확정한다.

### 이유
- artifact와 state 분리
- verify refutation 처리 일관성
- QA 게이트 명확화

### 결과
- receipt writer/validator가 필요하다.
- 상태 표시는 다소 엄격해지지만 정확도가 올라간다.

## ADR-005. 전역 state cleanup 대신 run-scoped storage를 사용한다
### 상태
승인 제안

### 배경
시작할 때 `.pipeline/state`, `.pipeline/locks`, `.pipeline/manifests`를 전역 삭제하면 장시간 운용과 복구에서 이전 상태와 현재 상태의 경계가 약해진다.

### 결정
`.pipeline/runs/<run_id>/...` 구조로 이전 run과 현재 run을 분리한다.

### 이유
- stale state 혼입 감소
- restart/recovery 일관성 향상
- postmortem 분석 용이

### 결과
- 디렉터리 구조가 조금 복잡해진다.
- 보존 정책과 cleanup 정책이 별도로 필요해진다.

## ADR-006. PTY는 pilot으로만 도입 여부를 판단한다
### 상태
승인 제안

### 배경
PTY가 이론상 더 나을 수 있지만, 현재 불안정성의 핵심은 상태 경계와 책임 분리 문제다.

### 결정
PTY는 1단계 핵심 범위가 아니다.  
supervisor/adapter/state 정비 후 lane 1개 pilot으로만 검증한다.

### 이유
- 구조 문제를 substrate 교체로 가리지 않기 위함
- 안정성 향상을 수치로 입증하기 위함

### 결과
- PTY 전환 시점이 늦어질 수 있다.
- 하지만 잘못된 대규모 치환을 피할 수 있다.

## ADR-007. Compatibility surface는 legacy status surface에 한해 export-only로 유지한다
### 상태
승인 제안

### 배경
기존 도구나 운영 화면은 당장 전부 바꾸기 어렵다.

### 결정
export-only compatibility 대상은 legacy status surface와 read-model 보조 파일/화면으로 제한한다.  
`latest-work`, `latest-verify`, legacy status snapshot 같은 surface는 export-only로 유지할 수 있다.  
단, `.pipeline/implement_handoff.md`, `.pipeline/advisory_request.md`, `.pipeline/advisory_advice.md`, `.pipeline/operator_request.md` 같은 rolling control slot은 export-only 대상에 포함하지 않는다.
rolling control slot은 전환 기간에도 canonical control plane으로 유지하며, current truth가 아닌 compatibility surface로 격하하지 않는다.
historical aliases `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`는 같은 role-based logical slot의 read-only compatibility input으로만 허용하며, 별도 control plane으로 분리하지 않는다.

### 이유
- 점진적 전환 가능
- 기존 operator workflow 충격 완화

### 결과
- compatibility surface 관리 비용이 남는다.
- 그러나 control plane과 분리하면 legacy status surface만 안전하게 유지할 수 있다.
- rolling control slot까지 compatibility 범위가 넓어지는 오해를 줄일 수 있다.

## ADR-008. Status truth는 run-scoped status.json/events.jsonl로 고정한다
### 상태
승인 제안

### 배경
turn_state mirror, pane 출력, watcher.log, rolling control slot이 섞이면 다시 split-brain이 생긴다.

### 결정
authority path는 run-scoped `status.json` 1개와 append-only `events.jsonl` 1개로 고정한다.  
`.pipeline/state/turn_state.json`는 migration 동안만 export-only mirror로 유지한다.

### 이유
- status truth 경계를 단순화
- controller/UI 소비 경로 표준화
- watcher-exporter -> supervisor takeover를 같은 schema로 연결 가능

### 결과
- current run pointer와 run-scoped layout이 필요하다.
- turn_state는 더 이상 authority가 아니다.

## ADR-009. 브라우저 UI는 controller HTTP API만 읽고, 로컬 thin client는 runtime helper/CLI를 쓴다
### 상태
승인 제안

### 배경
브라우저 UI가 repo 파일을 직접 읽으면 migration이 끝날수록 임시 결합이 남는다.  
반면 `pipeline_gui`와 `pipeline-launcher`는 로컬 실행 도구이므로 controller HTTP를 강제하기보다 shared runtime helper/CLI thin-client 경계로 고정하는 편이 현재 repo 구조와 맞다.

### 결정
브라우저 controller UI는 controller HTTP API만 읽고, repo 파일 직접 읽기를 current truth 경로로 사용하지 않는다.  
`pipeline_gui`와 `pipeline-launcher`는 로컬 thin client로서 shared runtime helper/CLI를 사용할 수 있지만, pane/log/file scan을 current truth 경로로 사용하지 않는다.

### 이유
- local HTTP facade 재사용
- UI와 filesystem schema 결합 축소
- WSL/Windows 접근 경계 유지

### 결과
- controller API 안정성이 브라우저 UI 경계에서 중요해진다.
- 로컬 thin client는 shared runtime helper/CLI contract 안정성이 중요해진다.

## ADR-010. Round-close receipt는 supervisor만 생성한다
### 상태
승인 제안

### 배경
receipt authority가 lane이나 watcher 쪽으로 분산되면 `/verify`와 runtime close 판단이 다시 흔들린다.

### 결정
round-close receipt는 supervisor만 생성한다.  
watcher, wrapper, verify/advisory owner lane은 completion fact만 보고한다.

### 이유
- single writer 원칙 유지
- `/verify` persistent truth와 receipt close authority 분리
- manifest/control/workflow 검증을 한 곳에서 수행 가능

### 결과
- supervisor에 receipt validator가 필요하다.
- lane은 receipt 직접 쓰기 권한을 갖지 않는다.

## ADR-011. Wrapper contract는 5개 이벤트와 lane별 recovery 경계를 사용한다
### 상태
승인 제안

### 배경
vendor UI 문자열을 여러 레이어가 재해석하면 readiness와 recovery가 계속 흔들린다.

### 결정
wrapper 최소 이벤트는 `READY`, `HEARTBEAT`, `DISPATCH_SEEN`, `TASK_ACCEPTED`, `TASK_DONE`, `BROKEN`으로 고정한다.
implement owner는 post-accept blind replay를 금지하고, verify/advisory owner는 bounded auto-retry를 허용한다.

### 이유
- readiness/recovery/receipt/UI 상태를 같은 경계 위에 올리기 위함
- lane별 업무 특성 차이를 recovery 정책에 반영하기 위함

### 결과
- wrapper payload 계약이 필요하다.
- retry 숫자와 타임아웃은 운영 중 조정 여지가 남는다.

## 종합 결론

이번 전환의 핵심 결정은 다음 한 줄로 요약됩니다.

**“tmux를 바로 버리는 것이 아니라, 상태 추론을 launcher에서 제거하고 supervisor 중심으로 구조를 재편한다.”**
