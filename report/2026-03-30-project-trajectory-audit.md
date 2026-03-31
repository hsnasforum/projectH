# projectH 궤도 분석 리포트

> 분석일: 2026-03-30
> 분석 범위: work/3/26 ~ work/3/30, verify/3/30, 전체 코드베이스
> 성격: **중간 시점 trajectory warning memo** (현재 factual truth 문서가 아님)
> Codex 리뷰: 2026-03-30 반영 완료

---

## 0. 이 문서의 성격

이 리포트는 **방향성 경고 문서**입니다.
현재 repo 상태의 factual truth가 아니라, 작업 궤도가 원래 목표에서 벗어났는지를 점검하는 것이 목적입니다.

초판 작성 후 Codex 리뷰를 거쳐, 사실과 맞지 않던 항목을 아래 3분류로 정리하고 교정했습니다:
- **지금도 유효한 주장** — 그대로 유지
- **지금은 stale한 주장** — 취소선 + 교정 사유
- **현재 상태 기준으로 다시 쓴 문장** — [교정] 표시

---

## 1. 프로젝트 정체성

| 항목 | 내용 |
|------|------|
| 현재 정체성 | 로컬 우선 문서 비서 웹 MVP |
| 장기 목표 | teachable local personal agent |
| 핵심 기능 | 파일 요약, 문서 검색, 일반 채팅, 승인 기반 저장, 증거/출처 패널, 스트리밍, PDF 지원, 웹 조사 |

---

## 2. 일별 작업 방향 분포 [유효]

| 날짜 | 총 노트 | Core MVP | Reviewed Memory 기계 | 인프라/프로세스 |
|------|---------|----------|---------------------|---------------|
| 03-26 | 8 | 0% | 0% | **100%** |
| 03-27 | 34 | **53%** | 12% | 35% |
| 03-28 | 30 | 7% | **77%** | 17% |
| 03-29 | 44 | **0%** | **98%** | 2% |
| 03-30 | 32 | 22% | **72%** | 6% |
| **합계** | **148** | **~16%** | **~62%** | **~22%** |

### 추이 요약

- 03-26: 방향 재설정 (doc-sync, roadmap alignment)
- 03-27: MVP 핵심 기능 구현 (grounded-brief, correction editor, approval reason)
- **03-28: 급격한 전환** — reviewed-memory 계약 폭증 시작
- **03-29: 극단** — 44개 노트 중 43개가 reviewed-memory 내부 machinery
- 03-30: 부분 복귀 (summary prompt 개선) + reviewed-memory materialization 마무리

> **이 분포 자체는 지금도 유효합니다.** 5일간 작업의 62%가 reviewed-memory에 집중되었다는 사실은 변하지 않습니다.

---

## 3. 코드베이스 실제 구현 현황

### 3.1 Core MVP (완성도 높음) [유효]

| 기능 | 상태 | 비고 |
|------|------|------|
| 로컬 파일 읽기 및 요약 | **완료** | 짧은/긴 문서 구분, chunk reduce |
| 문서 검색 | **완료** | 폴더 기반 검색 |
| 일반 채팅 | **완료** | |
| 승인 기반 저장 | **완료** | 재발급, 출처 구분 포함 |
| 증거/출처 패널 | **완료** | summary chunks 선택 표시 |
| 스트리밍 | **완료** | 진행 표시 + 취소 |
| PDF 텍스트 레이어 | **완료** | OCR 미지원 안내 |
| 웹 조사 | **완료** | 권한 게이트, claim coverage |
| 수정 에디터 | **완료** | corrected_text 저장 |
| 콘텐츠 거절 | **완료** | 승인 거절과 분리 |

### 3.2 Reviewed Memory 기계 [교정됨 — 초판은 stale했음]

**초판 주장**: 모두 contract_only / internal_only / absent → 사용자 기능 0개

**[교정] 현재 실제 상태**:

| 항목 | 초판 판정 | 현재 실제 상태 |
|------|----------|--------------|
| `capability_basis` | ~~absent~~ | **구현됨** — `same_session_reviewed_memory_capability_basis_v1`, payload 노출 |
| `capability_outcome` | ~~blocked_all_required (hardcoded)~~ | **동적화됨** — basis present 시 `unblocked_all_required` |
| `transition_record` | ~~absent (payload)~~ | **전 lifecycle 구현** — 발행→적용→결과확정→중단→되돌리기 |
| 집계 액션 | ~~0개~~ | **6개 API 완성** (emit/apply/result/stop/reverse/conflict-check) |
| 효과 활성화 | ~~미구현~~ | **구현됨** — 응답 prefix에 `[검토 메모 활성]` 주입 |
| local_effect_presence | internal_only | 내부 helper로 유지 (이 부분은 초판과 동일) |

**교정 사유**: 초판 작성 시점에 최신 work/verify 노트를 충분히 반영하지 못했음. Codex 리뷰에서 아래 워크노트들이 이미 구현 완료를 기록하고 있음을 확인:
- `2026-03-30-reviewed-memory-capability-basis-materialization-only.md`
- `2026-03-30-reviewed-memory-unblocked-all-required-path-only.md`
- `2026-03-30-aggregate-level-transition-record-emission-only.md`
- `2026-03-30-reviewed-memory-correction-pattern-effect-activation-only.md`
- `2026-03-30-future-reviewed-memory-stop-apply-only.md`
- `2026-03-30-future-reviewed-memory-reversal-only.md`

### 3.3 코드 비중 [부분 교정]

| 영역 | 비중 | 상태 |
|------|------|------|
| 문서 비서 MVP | ~65% | 완전히 작동 |
| 웹 조사 2차 모드 | ~15% | 대부분 작동 |
| Reviewed Memory 기계 | ~10-15% | [교정] app/web.py에 집중되어 있으나, **6개 API + 효과 활성화까지 작동** |
| 저장소/모델 인프라 | ~10% | 작동 |

---

## 4. 테스트 현황 [교정됨]

| 테스트 | 초판 기록 | [교정] 현재 상태 |
|--------|----------|----------------|
| Python 단위 테스트 | 176/176 통과 | **유효** — 여전히 통과 |
| E2E Playwright | ~~11/12 (1 실패)~~ | **과거에 12/12 green 기록 있음** (verify note 확인). 다만 이후 focused verify만 진행, full e2e 미재실행 |
| git diff --check | clean | **유효** |

**교정 사유**: `verify/3/30/2026-03-30-e2e-568-recurrence-aggregate-verification.md`에서 `make e2e-test` 12 passed로 닫은 기록이 있음. 초판이 이를 반영하지 못하고 과거 실패 snapshot을 현재 사실처럼 기술했음.

**현재 불확실성**: 이후 regression 라운드들이 focused verify만 했고 full e2e를 다시 안 돌렸으므로, 현재 repo-level ready 여부는 full e2e 재실행으로 확인해야 함.

---

## 5. 문서-코드 격차 [교정됨]

| 항목 | 초판 판정 | [교정] 현재 판정 |
|------|----------|----------------|
| 로컬 문서 비서 MVP | 일치 | **유효** |
| 핵심 루프 (읽기-요약-Q&A-승인) | 일치 | **유효** |
| 웹 조사 | 일치 | **유효** |
| transition_audit_source_ref | ~~docs stale~~ | **현재 루트 docs 기준 이미 해소** |
| capability source family | ~~docs stale~~ | **현재 루트 docs 기준 이미 해소** |
| reviewed-memory 계약들 | ~~과대 표기~~ | **대부분 실제 구현됨** (초판이 outdated) |
| E2E 전체 green | ~~불일치~~ | **과거 green 기록 있으나 최신 full 재실행 미확인** |

---

## 6. 핵심 발견: 딴길로 샌 지점

### 6.1 방향성 경고 [유효]

작업 비중의 급격한 전환은 사실입니다:
- 03-27: MVP 53% → 03-29: MVP 0%, reviewed-memory 98%
- 5일간 합계: reviewed-memory 62%, Core MVP 16%

**다만 이것이 "딴길"인지 "계획된 다음 단계 진입"인지는 해석이 다를 수 있습니다.**

### 6.2 "materialization-only" 패턴 [유효]

03-29~30에 집중 발생한 극단적 세분화:
- `reviewed-memory-local-effect-proof-boundary-materialization-only`
- `reviewed-memory-local-effect-proof-record-materialization-only`
- `reviewed-memory-local-effect-reversible-effect-handle-materialization-only`
- ... (20개 이상)

**이 구간이 길었다는 지적은 Codex도 인정한 유효한 관찰입니다.**

### 6.3 ~~역행 설계~~ [교정 — 과장이었음]

초판에서 "계약만 있고 사용자 기능 0개"라고 했으나, 실제로는:
- 6개 API가 모두 작동
- 효과 활성화 (응답에 교정 패턴 반영) 구현됨
- E2E smoke에서 전체 lifecycle 검증됨

**즉 "역행 설계"가 아니라 "bottom-up으로 내부 layer를 쌓은 뒤 top-level까지 올라온 상태"입니다.** 방식의 차이이지 방향이 틀린 것은 아닙니다.

### 6.4 Scope 복잡도 [유효 — 단 판정 완화]

| 시점 | 의도 | 실제 |
|------|------|------|
| 03-26 | "minimal memory contract 초안" | doc-sync만 |
| 03-27 | correction editor + 최소 candidate | MVP 53% + memory 12% |
| 03-28 | "minimum promotion guardrail" | 계약 객체 정의 시작 |
| 03-29 | - | 내부 layer 집중 구축 |
| 03-30 | - | materialization 마무리 + lifecycle 완성 |

"최소(minimum)"라는 이름 대비 실제 복잡도가 높았다는 지적은 여전히 유효합니다.
**다만 최종적으로 6개 API + 효과 활성화까지 작동하게 되었으므로, 완전한 허공 작업은 아니었습니다.**

---

## 7. 판정 [교정됨]

### 지금도 유효한 주장

- Core MVP는 손상 없이 유지됨
- 단위 테스트 176개 전부 통과
- work/verify 기록 체계 자체는 건강
- **5일간 작업 비중이 reviewed-memory에 편중되었다는 사실** (62%)
- **materialization-only 구간이 길었다는 점**
- **work 노트가 하루 30개 이상으로 과도하게 세분화되었다는 점**

### 지금은 stale한 주장

- ~~capability_basis absent, capability_outcome blocked_all_required~~ → 구현 완료
- ~~transition_record absent~~ → 전 lifecycle 구현
- ~~사용자 기능 0개~~ → 6개 API + 효과 활성화 작동
- ~~E2E 11/12 실패~~ → 과거 green 기록 있음 (최신 full 재실행 미확인)
- ~~docs mismatch (transition_audit_source_ref 등)~~ → 현재 루트 docs 기준 해소
- ~~"역행 설계"~~ → bottom-up 구현이 top까지 올라온 상태

### 최종 판정 [교정]

> **궤도 이탈 정도: 중 (주의 수준, 교정 필요까지는 아님)**
>
> MVP는 온전하고, reviewed-memory 기계도 최종적으로 작동하는 상태까지 도달했음.
> 다만 03-28~29 구간에서 **내부 machinery 비중이 과도하게 높았고**,
> **materialization-only 세분화가 추적 가능 범위를 넘었다**는 점은 유효한 경고.
>
> "딴길"보다는 **"계획된 다음 단계에 너무 깊이 들어간 기간이 있었다"**가 정확한 표현.

---

## 8. 권장사항 [교정됨]

### 즉시

1. **full E2E 재실행으로 현재 repo 상태 확인** — green이면 ready, 아니면 triage
2. **work 노트 세분화 제한** — 하루 30개 이상은 추적 불가, 의미 단위로 묶기

### 단기

3. **다음 작업 비중을 core MVP 쪽으로 재조정**
   - reviewed-memory lifecycle이 완성되었으므로, 이제 그 위의 사용자 경험 품질에 집중
   - summary 품질, 검색 정확도, UI 다듬기 등

4. **reviewed-memory 코드 구조 점검**
   - app/web.py에 집중된 352건의 참조 — core/로의 분리 필요 여부 판단

### 원칙

5. **매 라운드 closeout 시 "payload에 노출된 기능"과 "internal helper"를 구분 표기**
6. **focused verify 후에도 주기적으로 full e2e 재실행**

---

## 부록: 파일 참조

- E2E green 기록: [verify/3/30/2026-03-30-e2e-568-recurrence-aggregate-verification.md](../verify/3/30/2026-03-30-e2e-568-recurrence-aggregate-verification.md)
- 다음 슬라이스 지시: [.pipeline/codex_feedback.md](../.pipeline/codex_feedback.md)
- 프로젝트 지침: [CLAUDE.md](../CLAUDE.md)
- 마일스톤: [docs/MILESTONES.md](../docs/MILESTONES.md)

---

## 부록: 교정 이력

| 일시 | 내용 |
|------|------|
| 2026-03-30 초판 | 코드베이스 + work/verify 분석 기반 작성 |
| 2026-03-30 교정 | Codex 리뷰 반영 — stale 사실 6건 교정, 판정 "중~상"→"중"으로 완화, 문서 성격을 "trajectory warning memo"로 명시 |
