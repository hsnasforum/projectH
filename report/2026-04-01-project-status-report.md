# projectH 상세 현황 보고서

**작성일**: 2026-04-01  
**프로젝트**: projectH — 로컬 퍼스트 문서 어시스턴트 웹 MVP  
**저장소**: github.com/hsnasforum/projectH  
**브랜치**: master (23 커밋)

---

## 1. 프로젝트 개요

projectH는 로컬 파일을 읽고, 근거 기반 요약을 생성하며, 명시적 승인을 통해서만 저장하는 **로컬 퍼스트 문서 어시스턴트**입니다.

장기적으로는 사용자 교정을 흡수하고, 승인 하에 제한된 프로그램 운영이 가능한 **교습 가능한 로컬 퍼스널 에이전트**로 확장되는 것을 목표로 합니다.

**핵심 원칙**:
- 로컬 퍼스트 (127.0.0.1에서만 동작)
- 승인 기반 안전성 (쓰기 작업은 반드시 사용자 승인 필요)
- 근거/출처 투명성 (모든 응답에 증거 경로 포함)
- 교체 가능한 모델/런타임 (provider 추상화)

---

## 2. 아키텍처 구조

```
┌─────────────────────────────────────────────────┐
│                  React SPA (Vite 5)              │
│        Tailwind CSS 3 · TypeScript · 1,719 줄     │
├─────────────────────────────────────────────────┤
│              app/web.py (6,995 줄)               │
│         Flask 웹 서버 · REST API · SSE 스트리밍     │
├──────────┬──────────┬──────────┬────────────────┤
│  Core    │ Storage  │  Tools   │ Model Adapter  │
│ 10,366줄 │ 2,449줄  │  904줄   │   1,744줄      │
└──────────┴──────────┴──────────┴────────────────┘
```

### 계층별 책임

| 계층 | 파일 수 | 줄 수 | 역할 |
|------|---------|-------|------|
| **Frontend** (React) | 13 | 1,719 | UI 렌더링, 스트리밍, 세션 관리 |
| **App** (web.py) | 4 | 7,443 | HTTP 라우팅, SSE, API 엔드포인트 |
| **Core** | 9 | 10,366 | 오케스트레이션, 의도 분석, 승인, 증거 |
| **Storage** | 8 | 2,449 | 세션·아티팩트·교정·선호 영속화 |
| **Tools** | 7 | 904 | 파일 읽기, 검색, 노트 쓰기, 웹 검색 |
| **Model Adapter** | 5 | 1,744 | Ollama/Mock 프로바이더 어댑터 |
| **Config** | 2 | 47 | 환경 설정 |
| **Eval** | 6 | 417 | 선호 준수 평가 프레임워크 |
| **총 소스** | **54+** | **23,163** | — |
| **테스트** | 22 | 26,485 | 525개 테스트 함수 |

---

## 3. 완료된 구조 리팩터링

### 3.1 계약 고정 (contracts.py — 344줄)

모든 문자열 상수를 24개 StrEnum으로 단일화. 프론트/백 간 상수 동기화 보장.

주요 Enum:
- `ResponseStatus`, `ArtifactKind`, `RecordStage`, `AnswerMode`
- `SourceType`, `SourceRole`, `CoverageStatus`
- `WebSearchPermission`, `CorrectionStatus`, `PreferenceStatus`
- `StreamEventType`, `ResponseOriginProvider`, `ApprovalKind`

상태 전이 규칙: `RECORD_STAGE_TRANSITIONS`, `CORRECTION_STATUS_TRANSITIONS`, `PREFERENCE_STATUS_TRANSITIONS`

### 3.2 상태 모델화 (models.py — 115줄)

`RequestContext` (frozen dataclass, 16 필드): handle()에 흩어져 있던 지역 변수를 불변 객체로 통합.

`SearchIntentResolution`: 검색 의도 해석 결과를 구조화, 엔티티 재조사 지원.

### 3.3 handle() 분해 (agent_loop.py)

| 항목 | 이전 | 이후 |
|------|------|------|
| handle() 본문 | 1,157줄 | 89줄 오케스트레이터 |
| 핸들러 | 1개 (handle) | 18개 전문 핸들러 |
| 공통 패턴 | 중복 | `_finalize_response()` · `_dispatch_request()` |

---

## 4. 구현 완료 기능

### 4.1 문서 처리
- **파일 요약**: 로컬 파일 경로 또는 파일 탐색기/드래그앤드롭으로 업로드
- **문서 검색**: 지정 디렉터리 내 키워드 검색
- **PDF 지원**: 텍스트 레이어 추출, OCR 미지원 안내
- **일반 채팅**: 자유 질문/응답

### 4.2 세션 관리
- 세션 생성/전환/삭제/전체삭제
- 원자적 JSON 저장 (임시 파일 + rename)
- 손상 파일 자동 격리 (.quarantine/)
- 세션당 최대 500 메시지
- 버전 카운터 (`_version`)

### 4.3 승인 플로우
- 노트 저장 승인 (경로 확인 후 저장)
- 재발행 승인 (경로 변경 후 재승인)
- 덮어쓰기 승인
- 교정 텍스트 승인
- 콘텐츠 판정 (content verdict)

### 4.4 웹 조사
- 권한 기반 웹 검색 (disabled / approval / auto)
- 듀얼 프로브 검색 (엔티티 + 키워드)
- JSON 이력 저장 (data/web-search/)
- 클레임 커버리지 시각화
- 출처 유형/역할 분류 (source_policy.py)

### 4.5 스트리밍 & UX
- SSE 기반 실시간 응답 스트리밍
- 단계별 상태 표시 (요청 준비 → 연결 확인 → 응답 작성)
- 응답 취소 (AbortController)
- 응답 출처 뱃지 (response_origin)

### 4.6 근거/출처 투명성
- 증거 패널 (evidence)
- 요약 청크 패널 (summary_chunks)
- 클레임 커버리지 상태
- 출처 유형 라벨 (위키, 뉴스, DB 등)

---

## 5. 학습 기반 (Teachable Foundation)

### 5.1 Artifact Store (artifact_store.py — 177줄)

그라운디드 브리프 아티팩트를 개별 JSON 파일로 영속화.
- `create()` → `get()` → `append_correction()` → `append_save()` → `record_outcome()`
- 세션별/최근 조회

### 5.2 Correction Store (correction_store.py — 205줄)

교정 패턴 추적 및 재발 감지.
- 델타 분석: `compute_correction_delta()` (difflib + SHA-256 핑거프린트)
- 상태 흐름: recorded → confirmed → promoted → active → stopped
- 동일 핑거프린트 중복 제거, 재발 카운트 증가

### 5.3 Preference Store (preference_store.py — 235줄)

교차 세션 선호 기억.
- 2개 이상 서로 다른 세션에서 동일 패턴 → 자동 후보(candidate) 승격
- 사용자 관리: 활성화(activate) / 일시중지(pause) / 거부(reject)
- 한국어 설명 자동 생성

### 5.4 프롬프트 주입

활성 선호(최대 10건)가 Ollama 시스템 프롬프트에 자동 반영.
```
[사용자 선호]
1. {description}
2. {description}
위 선호사항을 자연스럽게 반영해 주세요.
```

### 5.5 Eval 하니스 (eval/ — 417줄)

| 측정 항목 | 설명 |
|-----------|------|
| `measure_adherence` | 필수 포함/제외 키워드 확인 |
| `measure_ab_delta` | 선호 반영 전/후 A/B 비교 |
| `measure_consistency` | 동일 시나리오 다중 실행 일관성 |

6개 내장 시나리오 (Mock 4 + Ollama 2).

---

## 6. 프론트엔드

### 6.1 기술 스택

| 항목 | 버전 |
|------|------|
| React | 19.2 |
| TypeScript | 6.0 |
| Vite | 5.4 (Node 18 호환) |
| Tailwind CSS | 3.4 |
| PostCSS + Autoprefixer | 최신 |

### 6.2 컴포넌트 구조

```
src/
├── App.tsx (52줄)          — 루트, 사이드바 토글 + 설정 상태
├── main.tsx (10줄)         — ReactDOM 엔트리
├── types.ts (155줄)        — 인터페이스 + DEFAULT_SETTINGS
├── api/
│   └── client.ts (169줄)   — fetch/stream/preference/session API
├── hooks/
│   └── useChat.ts (222줄)  — 상태 관리 + 스트리밍 + 사고 상태
└── components/
    ├── Sidebar.tsx (290줄)         — 다크 사이드바, 세션, 선호, 설정
    ├── ChatArea.tsx (115줄)        — 메시지 + 입력 + 승인
    ├── MessageBubble.tsx (152줄)   — 사용자(베이지)/어시스턴트(화이트) 말풍선
    ├── InputBar.tsx (245줄)        — 파일 선택 + 드래그앤드롭 + 자동 크기 조절
    ├── ApprovalCard.tsx (70줄)     — 인라인 앰버 승인 카드
    ├── PreferencePanel.tsx (181줄) — 접기/펼치기, 스크롤, 페이드아웃
    └── TypingIndicator.tsx (27줄)  — 바운스 점 + 상태 텍스트
```

### 6.3 디자인

- Claude.ai/ChatGPT 스타일 미니멀 디자인
- 따뜻한 베이지/화이트 톤 (warm-50, beige-100, stone 계열)
- 한국어 UI 텍스트
- 반응형 (모바일 오버레이 사이드바)

### 6.4 기본 설정

| 항목 | 기본값 |
|------|--------|
| Provider | ollama |
| Model | qwen2.5:3b |
| 웹 검색 권한 | approval (승인 후 허용) |

---

## 7. 테스트 현황

### 7.1 유닛 테스트 (525개 함수)

| 테스트 파일 | 함수 수 | 대상 |
|-------------|---------|------|
| test_web_app.py | ~186 | 웹 앱 전체 통합 |
| test_smoke.py | ~96 | E2E 시나리오 |
| test_contracts.py | 45 | 계약 안정성, 전이 규칙 |
| test_http_integration.py | 22 | HTTP 요청/응답 계약 |
| test_ollama_adapter.py | 22 | Ollama 어댑터 |
| test_correction_store.py | 18 | 교정 기억 영속화 |
| test_preference_store.py | 15 | 선호 기억 승격/관리 |
| test_eval_harness.py | 19 | 평가 프레임워크 |
| test_web_search_tool.py | 14 | 웹 검색 도구 |
| test_artifact_store.py | 12 | 아티팩트 CRUD |
| test_delta_analysis.py | 11 | 핑거프린트 호환성, 유사도 |
| test_session_store.py | 11 | 세션 직렬화 |
| test_models.py | 10 | 데이터 모델 |
| test_preference_injection.py | 9 | 프롬프트 주입 |
| test_request_intents.py | 9 | 의도 분류 |
| test_file_reader.py | 8 | 파일 읽기 |
| test_localization.py | 5 | 한국어 로컬라이제이션 |
| test_write_note.py | 4 | 노트 쓰기 |
| test_path_utils.py | 4 | 경로 유틸리티 |
| test_source_policy.py | 3 | 출처 정책 |
| test_approval.py | 2 | 승인 워크플로우 |

### 7.2 E2E 브라우저 테스트 (Playwright)

`e2e/tests/web-smoke.spec.mjs` — 주요 커버리지:
- 응답 복사 버튼 + 클립보드
- 메시지 타임스탬프
- 출처 파일명 메타데이터
- 파일 선택기/드래그앤드롭
- 승인 카드 인터랙션
- 교정 저장 워크플로우
- 후보 확인 및 검토 큐
- 웹 검색 이력 리로드
- PDF 텍스트 레이어
- OCR 미지원 안내

---

## 8. 데이터 영속화

```
data/
├── sessions/       — 세션별 JSON (원자적 저장, 격리)
├── artifacts/      — 그라운디드 브리프 JSON
├── corrections/    — 교정 패턴 JSON
├── preferences/    — 선호 기억 JSON
├── notes/          — 승인된 노트
└── web-search/     — 웹 검색 이력 (13,000+ 파일)
```

모든 저장소가 공통으로 사용하는 패턴:
- 파일당 하나의 레코드 (JSON)
- 원자적 쓰기 (임시 파일 → rename)
- 스레드 안전 (RLock)
- UUID 기반 임시 파일명

---

## 9. 커밋 이력 (최근 10건)

| 해시 | 내용 |
|------|------|
| 78e2c27 | fix: 선호 패널 오버플로우 + 에이전트 사고 상태 표시 |
| ab5a8f3 | fix: 세션 삭제 + 파일 선택기/드래그앤드롭 |
| 2c1ec0f | fix: 3가지 UI 이슈 — 설정 적용, 세션 삭제, 어시스턴트 말풍선 |
| d64b58a | feat: 선호 준수 워크플로우 eval 하니스 |
| 7b61609 | feat: 선호 관리 API + React UI 패널 |
| e239851 | feat: 활성 선호를 모델 프롬프트에 주입 |
| 62efeeb | feat: 교차 세션 선호 기억 저장소 |
| 3cbc519 | feat: 교정 기억 저장소 + 델타 분석 |
| 41609aa | feat: 독립 그라운디드 브리프 아티팩트 저장소 |
| fb9994a | config: React 기본 설정 변경 |

총 23 커밋.

---

## 10. 규모 요약

| 지표 | 수치 |
|------|------|
| Python 소스 코드 | 23,163줄 |
| 프론트엔드 소스 코드 | 1,719줄 |
| 테스트 코드 | 26,485줄 |
| 테스트 함수 | 525개 |
| 테스트 파일 | 22개 |
| 핵심 모듈 | 6개 패키지 |
| StrEnum 상수 | 24개 |
| API 엔드포인트 | 15+ |
| 저장소 클래스 | 5개 |
| Git 커밋 | 23 |
| 데이터 파일 | 13,000+ |

---

## 11. 현재 단계 판단

```
[완료] MVP 기능 구현          ████████████████████ 100%
[완료] 구조 리팩터링           ████████████████████ 100%
[완료] 학습 기반 구축           ████████████████████ 100%
[완료] React 프론트엔드        ████████████████████ 100%
[완료] UI 버그 수정            ████████████████████ 100%
[진행] 응답 품질 튜닝          ████░░░░░░░░░░░░░░░░  20%
[미착수] 외부 API 연동          ░░░░░░░░░░░░░░░░░░░░   0%
[미착수] 프로그램 제어/실행      ░░░░░░░░░░░░░░░░░░░░   0%
[미착수] 배포/패키징            ░░░░░░░░░░░░░░░░░░░░   0%
```

**현재 위치**: MVP 기능과 구조는 완성. 실사용 품질 다듬기 + 응답 품질 개선 단계.

---

## 12. 미완료 / 향후 과제

### 단기 (품질 개선)
- [ ] 모델 응답 품질 튜닝 (프롬프트 최적화, 모델 업그레이드)
- [ ] 작은 모델용 프롬프트 분기 (모델 크기별 시스템 프롬프트 길이 조절)
- [ ] 선호 기억 user-visible 루프 완성 (효과 활성화 + 명시적 정지)

### 중기 (기능 확장)
- [ ] 외부 API provider 연동 (Claude API, OpenAI API)
- [ ] 교정 edit/reject/defer 확장
- [ ] 충돌 가시성 및 운영자 감사
- [ ] 검토된 기억 적용 범위 확장

### 장기 (로드맵)
- [ ] 승인 기반 로컬 운영자 기반 (프로그램 제어)
- [ ] 개인화 로컬 모델 레이어
- [ ] 배포/패키징 (Docker, 데스크톱 앱)

---

## 13. 리스크 및 제약

| 리스크 | 현재 상태 | 완화 방안 |
|--------|-----------|-----------|
| qwen2.5:3b 모델 품질 한계 | 체감 품질 낮음 | 모델 업그레이드 또는 프롬프트 최적화 |
| agent_loop.py 8,545줄 | 여전히 대형 | 핸들러 분리 완료, 추가 분할 가능 |
| web.py 6,995줄 | 여전히 대형 | 라우트별 모듈 분리 가능 |
| JSON 파일 기반 영속화 | 대규모 시 성능 이슈 가능 | SQLite 전환 로드맵에 포함 |
| 테스트 환경 의존성 | pytest 설치 필요 | CI/CD 파이프라인 구성 필요 |
| main ↔ master 브랜치 동기화 | 3 커밋 behind | 주기적 merge 필요 |

---

*이 보고서는 2026-04-01 시점의 코드베이스 실제 상태를 기반으로 작성되었습니다.*
