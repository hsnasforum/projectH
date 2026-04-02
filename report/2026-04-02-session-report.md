# projectH 작업 보고서 — 2026-04-02

**세션 범위**: 응답 품질 최적화 → 아키텍처 리팩터링 → 기능 노출 → UX 개선 → 신규 기능
**커밋 수**: 40개 (78e2c27 ~ a50281d)
**테스트**: 536개 함수

---

## 1. 응답 품질 최적화

### 1.1 모델 크기별 프롬프트 최적화 (4cce8c1, 4440323)
- ≤14B 모델에 한국어 시스템 프롬프트 자동 적용
- 컨텍스트 프롬프트 간소화: **문서 발췌 → 핵심 근거 → 질문** 순서 재배치
- 영어 메타 지시(Output contract, Guardrails 등) 제거
- 깨진 유니코드(combining marks) 감지 시 자동 한국어 재작성

### 1.2 3-Tier 모델 라우팅 (dc691ef)
```
작업 유형                    → 모델    → 선호 예산
───────────────────────────────────────────────
리라이트/형식 맞추기          → 3B      → 2건
일반 채팅/문서 Q&A/메모       → 7B      → 5건
웹 조사/충돌 출처/최신성/저장  → 14B     → 10건
```
- `model_adapter/router.py` — RoutingHint → ModelTier → 모델명 결정
- `OllamaModelAdapter.use_model()` — 호출별 모델 전환 (context manager)
- 프론트엔드 프리셋: 자동 / 속도 / 균형 / 정확

### 1.3 웹 조사 품질 강화 (6075e9b)
- **3단 구조 웹 요약**: 확인된 사실 / 단일 출처 정보 / 커뮤니티 참고용
- claim coverage 절반 이상 weak → **확정 표현 금지** + "(교차 확인 부족)"
- 커뮤니티/블로그 전용 → "비공식 출처"로 강등
- 시스템 프롬프트에 불확실성 게이팅 규칙 추가

### 1.4 2단계 생성 (3abdb36)
- 웹 조사 합성 시 7B 초안 → 14B 검토
- 14B가 unsupported claim, 누락 유보 표현, 환각 감지
- 수정 불필요 시 원본 유지

### 1.5 모델 설치 및 관리
- qwen2.5:14b (9.0GB), qwen2.5:7b (4.7GB) 설치
- 사이드바/헤더에 모델 선택 UI
- 기본 모델 qwen2.5:14b → auto(라우팅)로 변경
- 웹 검색 기본 권한 "approval" → "enabled"

---

## 2. Eval 릴리스 게이트 (6d6c9ca)

### 시나리오 확대 (6 → 25개)
| 카테고리 | 개수 | 내용 |
|----------|------|------|
| preference | 8 | mock plumbing + 용어/스타일/결론배치 반영 |
| routing | 8 | 3B/7B/14B 라우팅 정확성 |
| doc_followup | 4 | key_points, action_items, memo, 근거 기반 |
| uncertainty | 3 | 근거 없음, 직접 경험, 검증 불가 사실 |
| doc_summary | 1 | 단일 문서 요약 |
| format | 1 | 한국어 리라이트 |

### 새 메트릭
- `measure_routing()` — 모델 티어 정확성
- `measure_uncertainty_honesty()` — 불확실성 표기 정직성
- `measure_response_quality()` — 한국어 비율, 빈 응답, 길이

### 릴리스 게이트 모드
```bash
python -m eval --gate       # exit code 1이면 머지 차단
python -m eval --category uncertainty
```

---

## 3. Preference User-Visible 루프 (8151074)

- 어시스턴트 메시지에 보라색 **"선호 N건 반영"** 배지
- 호버 시 각 선호의 description 표시
- PreferencePanel에 승격 사유 (교정: A→B, 추가, 제거)
- `AgentResponse.applied_preferences` → API → 프론트 전달

---

## 4. SQLite 저장소 백엔드 (4c2ed68)

| 테이블 | 용도 |
|--------|------|
| sessions | 세션 데이터 (메시지, 승인, 컨텍스트) |
| artifacts | 그라운디드 브리프 아티팩트 |
| corrections | 교정 패턴 (JSON 유지) |
| preferences | 선호 기억 |
| task_log | 작업 로그 |

- Thread-local 커넥션 + WAL 모드 + health check
- `LOCAL_AI_STORAGE_BACKEND=sqlite`로 전환
- `python -m storage.migrate`로 JSON → SQLite 마이그레이션
- `duckduckgo-search` optional dependency 선언

---

## 5. 코드 리뷰 수정 (a9c19e6)

| 등급 | 이슈 | 조치 |
|------|------|------|
| CRITICAL | SQLite 단일 커넥션 병목 | thread-local 커넥션 + health check |
| CRITICAL | _ModelOverrideContext 스레드 안전 | 단일 스레드 가정 문서화 |
| IMPORTANT | 마이그레이션 corrections 미구현 무경고 | WARNING 출력 + 문서화 |
| IMPORTANT | 데드 메서드 2개 | 삭제 |
| IMPORTANT | duckduckgo-search 미선언 | pyproject.toml optional dep |
| IMPORTANT | 마이그레이션 에러 무시 | 파일별 에러 수집 |
| IMPORTANT | web_search_records 데드 스키마 | 제거 |

---

## 6. 웹 검색 안정화

| 커밋 | 수정 내용 |
|------|-----------|
| a586ee6 | User-Agent를 브라우저 UA로 변경 (DDG 봇 차단 해결) |
| 74b252e | "웹검색:" 콜론이 쿼리에 포함되던 파싱 버그 수정 |
| 0ead33c | DDG rate limit 재시도 로직 (최대 2회, 백오프) |
| 36adff1 | DDG 블럭 시 duckduckgo-search 패키지 API fallback |

---

## 7. 아키텍처: web.py 분리

**7,025줄 → 573줄** (92% 감소)

| 파일 | 줄 수 | 역할 |
|------|-------|------|
| app/web.py | 573 | 라우트 등록, 초기화, HTTP 핸들링 |
| app/serializers.py | 4,784 | 직렬화 + 유틸리티 헬퍼 |
| app/handlers/chat.py | 736 | 채팅 스트리밍 코어 |
| app/handlers/aggregate.py | 678 | 후보/집계 트랜지션 |
| app/handlers/feedback.py | 280 | 피드백/교정/판정 |
| app/handlers/preferences.py | 48 | 선호 CRUD |

6개 커밋으로 단계별 추출 (e484567 ~ 82e1a0c), 334 테스트 전체 통과.

---

## 8. 백엔드 기능 노출 (B단계)

| 기능 | 커밋 | UI |
|------|------|-----|
| 웹 검색 | cff70f0 | `/검색` 슬래시 명령어 + 자동완성 드롭다운 |
| 교정 추적 | a98057f | 호버 연필 아이콘 → 인라인 편집 → API 제출 |
| 콘텐츠 판정 | a5b087a | 좋아요/싫어요 버튼 → API 피드백 |
| 리뷰 큐 | c97431c | 헤더 "리뷰 N건" 배지 + API 연결 |

---

## 9. UX 개선 (A단계)

| 개선 | 커밋 | 내용 |
|------|------|------|
| 에러 토스트 | 8cfd71e | Toast 컴포넌트 (하단 우측, 5초 자동 사라짐) |
| 세션 검색 | 8cfd71e | 사이드바 검색 입력 (4개 이상 세션 시) |
| 반응형 | 71b0742 | 울트라와이드 720px 제한, 모바일 95% |
| Diff 뷰어 | 71b0742 | "교정 완료" 클릭 → 원본/수정 비교 (빨강/초록) |

---

## 10. 신규 기능 (C단계)

| 기능 | 커밋 | 내용 |
|------|------|------|
| 메시지 복사 | a50281d | 호버 시 복사 아이콘, 클릭 → 클립보드, 녹색 체크 피드백 |
| 다크모드 | a50281d | 사이드바 토글, localStorage 저장, CSS 오버라이드 |
| 마크다운 렌더링 | a50281d | `marked` 라이브러리, 제목/목록/코드블록/인용 스타일 |

---

## 11. 백그라운드 세션 (20c55a3, 75d9b56)

- 세션별 독립 상태 관리 (Map 기반)
- 요청 처리 중 다른 세션 전환 가능
- 사이드바에 처리 중(주황 점) / 완료(녹색 체크) 아이콘
- 상단 토스트 알림으로 백그라운드 완료 통지
- 세션 목록 최근 업데이트순 정렬

---

## 12. UI 개선 (이전 세션 이어받기)

| 커밋 | 내용 |
|------|------|
| d01f4b1 | URL을 파비콘 링크 칩 + 호버 프리뷰로 렌더링 |
| 09d4894 | "링크:/근거" 라벨 제거, 모델 선택 헤더 이동 |
| fdb8e29 | 사이드바 모델 선택 드롭다운 (14b/7b/3b) |

---

## 파일 변경 요약

### 신규 파일 (14개)
```
model_adapter/router.py          — 모델 라우팅 로직
storage/sqlite_store.py          — SQLite 백엔드
storage/migrate.py               — JSON→SQLite 마이그레이션 CLI
eval/scenarios.py                — 25개 eval 시나리오 (재작성)
app/serializers.py               — 직렬화 mixin
app/handlers/__init__.py         — 핸들러 패키지
app/handlers/chat.py             — 채팅 핸들러 mixin
app/handlers/feedback.py         — 피드백 핸들러 mixin
app/handlers/preferences.py      — 선호 핸들러 mixin
app/handlers/aggregate.py        — 집계 핸들러 mixin
app/frontend/src/components/Toast.tsx    — 에러/성공 토스트
app/frontend/src/components/LinkChip.tsx — URL 링크 칩
docs/superpowers/specs/          — 설계 문서 2개
docs/superpowers/plans/          — 구현 계획 1개
```

### 주요 수정 파일
```
model_adapter/ollama.py          — 프롬프트 분기, review_draft, use_model
model_adapter/base.py            — review_draft 인터페이스
core/agent_loop.py               — 라우팅 통합, 2단계 검토, 3단 웹 요약
core/request_intents.py          — 쿼리 파싱 수정
app/web.py                       — 7,025줄 → 573줄 리팩터링
tools/web_search.py              — UA 변경, DDG fallback
config/settings.py               — storage_backend, sqlite_db_path
pyproject.toml                   — optional dependency
app/frontend/src/                — 전체 프론트엔드 개선
tests/                           — 테스트 업데이트
```

---

## 수치 요약

| 지표 | 수치 |
|------|------|
| 총 커밋 | 40 |
| 신규 파일 | 14 |
| 테스트 함수 | 536 |
| web.py 감소 | 7,025 → 573줄 (92%) |
| Eval 시나리오 | 6 → 25 |
| 모델 라우팅 티어 | 3 (light/medium/heavy) |
| 프론트엔드 컴포넌트 | 10개 |
| API 엔드포인트 | 20+ |

---

*이 보고서는 2026-04-02 세션의 전체 작업을 기반으로 작성되었습니다.*
