# 2026-04-02 Canonical Work Closeout

**범위**: 4/2 세션 — 응답 품질 최적화, 구조 리팩터링, 저장소 백엔드 추가, 백엔드 기능 프론트엔드 노출, UX 개선
**커밋 범위**: 4cce8c1..5667f8a (4/2 00:34 ~ 14:02 KST, 36커밋)

---

## 변경 파일

### 신규 생성 (Python)
- `app/errors.py` (12줄) — WebApiError 데이터클래스, circular import 해소 목적
- `app/serializers.py` (4,784줄) — web.py에서 추출한 25개 `_serialize_*` 헬퍼 mixin
- `app/handlers/__init__.py` — 핸들러 패키지 초기화
- `app/handlers/chat.py` (736줄) — 채팅 스트리밍 코어 mixin
- `app/handlers/aggregate.py` (678줄) — 후보/집계 트랜지션 mixin
- `app/handlers/feedback.py` (280줄) — 피드백/교정/판정 mixin
- `app/handlers/preferences.py` (48줄) — 선호 CRUD mixin
- `storage/sqlite_store.py` (534줄) — SQLite 통합 저장소 (sessions, artifacts, corrections, preferences, task_log)
- `storage/migrate.py` (39줄) — JSON→SQLite 마이그레이션 CLI
- `model_adapter/router.py` (99줄) — 3-tier 모델 라우팅 (RoutingHint → ModelTier → 모델명)

### 신규 생성 (Frontend)
- `app/frontend/src/components/Toast.tsx` (77줄)
- `app/frontend/src/components/LinkChip.tsx` (126줄)
- `app/frontend/src/index.css` (35줄) — 다크모드 + 마크다운 스타일

### 신규 생성 (Docs)
- `docs/superpowers/specs/2026-04-02-web-layer-split-design.md`
- `docs/superpowers/specs/2026-04-02-web-search-ui-design.md`
- `docs/superpowers/plans/2026-04-02-web-layer-split.md`

### 주요 수정
- `app/web.py` — 약 7,000줄 → 563줄 (mixin 추출로 92% 감소)
- `core/agent_loop.py` — 라우팅 통합, 2단계 검토, 3단 웹 요약 (+253/-변경)
- `model_adapter/ollama.py` — 프롬프트 분기, `review_draft()`, `use_model()` context manager (+365/-변경)
- `model_adapter/base.py` — `review_draft` 인터페이스 추가
- `eval/scenarios.py` — 25개 시나리오로 재작성 (+396줄)
- `eval/harness.py` — 릴리스 게이트 모드 추가 (+109줄)
- `eval/metrics.py` — 라우팅/불확실성/품질 메트릭 추가 (+65줄)
- `eval/report.py` — eval 리포트 출력 (+38줄)
- `tools/web_search.py` — UA 변경, DDG fallback, 재시도 로직 (+74/-변경)
- `core/request_intents.py` — 웹검색 콜론 파싱 버그 수정
- `config/settings.py` — `storage_backend`, `sqlite_db_path` 설정 추가
- `pyproject.toml` — `duckduckgo-search` optional dependency 선언
- 프론트엔드 13개 파일 — 총 +956/-116줄 변경

### Dirty worktree (미커밋)
- `watcher_core.py` — claude_prompt에 `CLAUDE.md`, `verify/README.md` 추가 (1줄 변경)
- `.pipeline/` — experimental watcher 로그/상태 파일 변경 (런타임 산출물)

---

## 사용 skill

- 없음

---

## 변경 이유

4/1까지 프로젝트는 기능적으로 MVP 수준이었으나, 단일 파일 `web.py`(~7,000줄)에 직렬화·핸들러·라우팅이 모두 결합되어 있고, JSON 파일 기반 저장소만 있었으며, 모델 라우팅 없이 단일 모델을 사용하고 있었다. 4/2 세션은 이미 만들어진 백엔드 기능(교정, 피드백, 선호, 웹 검색)을 프론트엔드에 노출하면서, 동시에 web.py 구조를 분리하고 저장소/라우팅 인프라를 추가하는 작업을 진행했다.

---

## 핵심 변경

### 1. web.py 구조 분리 (6커밋: e484567~82e1a0c, +5667f8a)

`web.py` 약 7,000줄을 mixin 패턴으로 분해:
- `SerializerMixin` (25개 `_serialize_*` 메서드) → `app/serializers.py`
- `PreferenceHandlerMixin` → `app/handlers/preferences.py`
- `FeedbackHandlerMixin` → `app/handlers/feedback.py`
- `AggregateHandlerMixin` → `app/handlers/aggregate.py`
- `ChatHandlerMixin` → `app/handlers/chat.py`
- `WebApiError` → `app/errors.py` (circular import 해소)

분리 후 `app/web.py`는 563줄(라우트 등록, HTTP 핸들링, 초기화)만 남음.

### 2. 응답 품질 최적화 (4커밋: 4cce8c1, 4440323, dc691ef, 3abdb36 등)

- **모델 크기별 프롬프트 분기**: ≤14B 모델에 한국어 시스템 프롬프트 자동 적용, 깨진 유니코드 감지 시 한국어 재작성
- **3-tier 모델 라우팅** (`model_adapter/router.py`): RoutingHint → ModelTier(light/medium/heavy) → 모델명, 프론트엔드 프리셋(자동/속도/균형/정확)
- **2단계 생성**: 웹 조사 합성 시 7B 초안 → 14B 검토 (`review_draft()`)
- **3단 구조 웹 요약**: 확인된 사실 / 단일 출처 정보 / 커뮤니티 참고용, 불확실성 게이팅 규칙

### 3. SQLite 저장소 백엔드 (2커밋: 4c2ed68, a9c19e6)

- `storage/sqlite_store.py`: sessions, artifacts, corrections, preferences, task_log 5개 테이블
- Thread-local 커넥션 + WAL 모드 + health check
- `storage/migrate.py`: JSON→SQLite 마이그레이션 CLI
- `LOCAL_AI_STORAGE_BACKEND=sqlite`로 전환 가능
- 코드 리뷰 후속: thread-local 커넥션, 마이그레이션 WARNING, 데드 메서드/스키마 제거

### 4. Eval 확장 (1커밋: 6d6c9ca)

- 시나리오 6개 → 25개 (preference 8, routing 8, doc_followup 4, uncertainty 3, doc_summary 1, format 1)
- `measure_routing()`, `measure_uncertainty_honesty()`, `measure_response_quality()` 메트릭 추가
- `python -m eval --gate` 릴리스 게이트 모드

### 5. 백엔드 기능 프론트엔드 노출 (5커밋: cff70f0~c97431c)

- `/검색` 슬래시 명령어 + 자동완성 드롭다운 (InputBar.tsx)
- 인라인 교정 편집기: 호버 연필 아이콘 → 인라인 편집 → API 제출 (MessageBubble.tsx)
- 좋아요/싫어요 피드백 버튼 (MessageBubble.tsx)
- 리뷰 큐 배지: 헤더 "리뷰 N건" + API 연결 (Sidebar.tsx)
- 선호 반영 배지: 보라색 "선호 N건 반영" + 호버 설명 (MessageBubble.tsx, commit 8151074)

### 6. UX 개선 (7커밋)

- 에러 토스트 컴포넌트: 하단 우측, 5초 자동 사라짐 (Toast.tsx)
- 사이드바 세션 검색 (4개 이상 세션 시 표시)
- 반응형 레이아웃: 울트라와이드 720px 제한, 모바일 95%
- 교정 diff 뷰어: 원본/수정 빨강/초록 비교
- 복사 버튼: 호버 시 아이콘, 클릭 → 클립보드, 녹색 체크 피드백
- 다크모드: 사이드바 토글, localStorage 저장
- 마크다운 렌더링: `marked` 라이브러리, 제목/목록/코드블록/인용 스타일
- URL 링크 칩: 파비콘 + 호버 프리뷰 (LinkChip.tsx)
- 모델 선택 드롭다운: 헤더에 14b/7b/3b 선택
- 백그라운드 세션: 요청 처리 중 세션 전환, 처리중/완료 아이콘, 세션 목록 최근순

### 7. 웹 검색 안정화 (4커밋: a586ee6, 74b252e, 0ead33c, 36adff1)

- User-Agent를 브라우저 UA로 변경 (DDG 봇 차단 해결)
- "웹검색:" 콜론이 쿼리에 포함되던 파싱 버그 수정
- DDG rate limit 재시도 로직 (최대 2회, 백오프)
- DDG 블럭 시 `duckduckgo-search` 패키지 API fallback

---

## 검증

이번 closeout 작성 시 실제 실행한 검증:
- `python3 -m py_compile` — 변경/신규 10개 Python 모듈 전부 컴파일 성공
- `wc -l` — 신규 파일 줄 수 직접 확인 (web.py 563, serializers.py 4784, chat.py 736 등)
- `git diff --stat` — 커밋 범위별 변경량 직접 확인
- `ls` — 핸들러 패키지, 프론트엔드 컴포넌트, docs/superpowers 존재 확인

이번 closeout에서 실행하지 않은 것:
- `python3 -m unittest` (전체 테스트 스위트)
- `make e2e-test` (Playwright 브라우저 테스트)
- eval 릴리스 게이트 (`python -m eval --gate`)

---

## 남은 리스크

1. **전체 테스트 스위트 미실행**: 이번 closeout에서 unit test와 e2e test를 다시 돌리지 않았다. web.py 분리 커밋(82e1a0c)에서 334개 테스트 통과가 커밋 메시지에 기록되어 있으나, 이후 추가 커밋의 전체 테스트 상태는 이번 closeout에서 검증하지 않았다.
2. **SQLite 백엔드 corrections 마이그레이션 미구현**: `a9c19e6`에서 WARNING 출력으로 문서화했으나, JSON→SQLite corrections 마이그레이션은 아직 빈 상태.
3. **`_ModelOverrideContext` 스레드 안전성**: 단일 스레드 가정 문서화로 처리. 멀티스레드 환경 전환 시 주의 필요.
4. **web.py mixin 패턴**: `WebAppService`가 5개 mixin을 상속. 파일 분리는 완료했으나, 상호 참조가 `self.` 기반이라 mixin 간 암묵적 의존이 있음.
5. **dirty worktree**: `watcher_core.py` 1줄 변경(claude_prompt 확장)이 미커밋 상태.
6. **프론트엔드 빌드 산출물**: `app/static/dist/` 아래 빌드 파일이 커밋에 포함됨. 재빌드 시 해시가 바뀌면 diff가 발생할 수 있음.
