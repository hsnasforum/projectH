# 2026-04-22 4축 오너 번들 완료 및 마일스톤 재개 자문

## 개요
오늘 세션(CONTROL_SEQ 742, 747, 750, 753)을 통해 파이프라인의 핵심 구조 4축(공유 상태 파싱, 검증 체인 닫기, 리스 반납 통합, 활성 라운드 정규화)이 모두 성공적으로 구현 및 검증되었습니다. 이제 `feat/watcher-turn-state` 브랜치는 파이프라인 자동화의 'Ordinary next-step'을 안전하게 처리할 수 있는 견고한 상태입니다.

## Q1. commit/push 타이밍 판정
**판정**: **RECOMMEND: commit_push_now**

- **사유**: 현재까지의 4개 슬라이스는 순수하게 인프라의 구조적 개선(structural)에 집중되어 있으며, 모든 유닛 테스트와 통합 테스트(321건)가 통과된 깨끗한 상태입니다.
- **리스크 관리**: 이후 제품 기능(Milestone 5/6) 작업을 시작하면 UI와 백엔드 서비스 로직이 섞이게 됩니다. 인프라 정리가 완료된 이 시점을 하나의 'PR stabilization' 경계로 삼아 커밋 및 푸시를 수행함으로써, 구조적 변경사항을 명확히 보관하고 다음 단계의 진척도를 깨끗한 베이스라인에서 측정하는 것이 유리합니다.

## Q2. Milestone 5/6 첫 제품 슬라이스 선정
**판정**: **Milestone 6: "define shared reason fields with distinct correction / reject / reissue label sets"**

- **선정 이유**: 
  - Milestone 5와 6의 대부분의 핵심 제어 로직(artifact_id, 내용 거절, 수정본 저장 브릿지, session_local_memory_signal 등)은 이미 구현되어 있습니다.
  - 현재 `core/contracts.py`에 정의된 사유 라벨(reason_label)은 `explicit_content_rejection`, `explicit_correction_submitted` 등 최소한의 고정 문자열로만 구성되어 있어, 세션 메모리나 검토 후보(durable candidate)가 가질 수 있는 정보의 해상도가 낮습니다.
  - 이 슬라이스는 `ActiveControlSnapshot` 기반의 안정화된 인프라 위에서 실제 데이터의 질(quality)을 높이는 작업으로, 리스크는 낮으면서도 후속 `reviewed-memory` 활용 단계의 가치를 즉시 높여줍니다.

- **구현 범위 (Bounded Scope)**:
  - **소유 모듈**: `core/contracts.py`, `app/static/contracts.js`, `app/static/app.js`.
  - **백엔드**: `ALLOWED_CONTENT_REASON_LABELS`, `ALLOWED_CORRECTED_OUTCOME_REASON_LABELS`, `ALLOWED_APPROVAL_REASON_LABELS`에 구체적인 라벨 추가 (예: `fact_error`, `typo_fix`, `style_update`, `hallucination` 등).
  - **프런트엔드**: 내용 거절(`내용 거절`) 또는 수정본 제출 시 단순 버튼 클릭 외에 사유 라벨을 선택할 수 있는 UI 요소(작은 드롭다운 또는 칩셋) 추가.
  - **진입점**: `core/contracts.py` L202 (CorrectedOutcomeReasonLabel), L242 (ALLOWED_CONTENT_REASON_LABELS).

## 요약 및 권고
**RECOMMEND: commit_push_now** 후 **Milestone 6 "Richer reason labels"** 슬라이스로 제품 기능 구현 재개를 권고합니다. 이는 인프라 부채가 정리된 최적의 시점에 데이터 해상도를 높이는 가장 효율적인 경로입니다.
