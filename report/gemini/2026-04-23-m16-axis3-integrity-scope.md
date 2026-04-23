# Advisory Log: M16 Axis 3 - Integrity Consolidation (Ollama Fallback + Dist Policy)

## 개요
- **일시**: 2026-04-23
- **요청**: Ollama heavy tier fallback 안전성 문제와 M16 Axis 3(Dist Policy) 우선순위 결정
- **상태**: M16 Axis 2까지 완료되었으며, out-of-band로 구현된 Ollama 라우팅 활성화로 인해 특정 모델 미설치 시 시스템이 실패할 수 있는 리스크가 발견됨.

## 분석 및 판단
1.  **우선순위**: Ollama fallback 리스크는 "Integrity"와 직접적으로 연결됨. 사용자가 14B 모델을 설치하지 않았을 경우 엔티티 카드나 최신 정보 요약 등 중량급(Heavy) 경로에서 500 에러가 발생할 수 있으므로, M16 Axis 3의 "Integrity Consolidation" 범위에 이를 포함하여 최우선 해결하는 것이 타당함.
2.  **Ollama Fallback (Item 1)**: 
    - **Option B (Runtime Fallback) + Option A (Startup Check)** 하이브리드 방식 추천. 
    - `OllamaModelAdapter`가 사용 가능한 모델 목록을 캐싱하고, `use_model` 시점에 목표 모델이 없으면 하위 티어(Heavy -> Medium -> Light)로 자동 강등(Fallback)되도록 구현.
3.  **Dist Packaging Policy (Item 2)**:
    - **Option B (Fixed output names)** 추천.
    - 현재 `app/static/dist` 파일들이 git에 추적되고 있으나 Vite의 해시 파일명과 충돌하여 관리가 번거로움. 
    - `vite.config.ts`를 수정하여 고정된 파일명을 출력하게 함으로써, git 추적의 일관성을 유지하고 불필요한 고아(Orphan) 해시 파일 생성을 방지함.
4.  **결론**: 이 두 과제를 하나의 "Integrity Consolidation" 슬라이스로 묶어 M16을 완결짓는 것을 권고함.

## 권고 사항 (RECOMMEND)
**RECOMMEND: implement M16 Axis 3 (Integrity Consolidation: Ollama Fallback + Dist Policy)**

### 1. Ollama Reliability (Safety)
- **Adapter**: `OllamaModelAdapter`가 건강 확인(Health Check) 시 모델 목록을 캐싱하도록 보강.
- **Fallback Logic**: `use_model(target)` 호출 시 `target`이 없으면 `ModelConfig`에 정의된 차선책 모델을 자동으로 선택.
- **Observability**: Fallback 발생 시 로그 또는 `runtime_status` 이벤트를 통해 사용자에게 알림 (선택 사항).

### 2. Dist Packaging (Housekeeping)
- **Vite Config**: `app/frontend/vite.config.ts`에서 `build.rollupOptions.output`을 설정하여 `entryFileNames`, `chunkFileNames`, `assetFileNames`에서 해시를 제거하고 고정된 이름(예: `index.js`, `index.css`)을 사용하도록 수정.
- **Git Cleanup**: 추적 중인 기존 해시 파일들을 정리하고 고정된 이름의 파일들만 관리하도록 `git rm` 및 `git add` 수행.

## 기대 효과
- 모델 미설치 환경에서도 시스템 중단 없이 안정적인 서비스 제공.
- 빌드 결과물 관리 오버헤드 제거 및 git 상태 정합성 확보.
- Milestone 16의 "Integrity Consolidation" 목표 완벽 달성.
