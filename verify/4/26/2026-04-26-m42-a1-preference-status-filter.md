STATUS: verified
CONTROL_SEQ: 255
BASED_ON_WORK: work/4/26/2026-04-26-m42-a1-preference-status-filter.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 254
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 255

---

# 2026-04-26 M42 Axis 1 — Preference Status Filter 검증

## 이번 라운드 범위

M42 Axis 1 (preference status filter UI + `paused_count` payload) 단독 검증.
이전 라운드 3개 (watcher re-export, auth boundary, resolver) 는 이미 커밋됨 (`85c5210`, `af5141d`).

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile app/handlers/preferences.py` | **PASS** (출력 없음) |
| `cd app/frontend && npx tsc --noEmit` | **PASS** (출력 없음) |
| `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_list_preferences_payload_includes_status_counts` | **PASS** (1 test, 0.007s) |
| `git diff --check -- [변경 파일 전체]` | **PASS** (trailing whitespace 없음) |

## 코드 리뷰 확인

**`app/handlers/preferences.py`** (단 1줄 추가):
```python
"paused_count": sum(1 for p in enriched if p.get("status") == "paused"),
```
- `active_count` / `candidate_count`와 동일한 패턴, 정확.

**`app/frontend/src/api/client.ts`** (단 1줄 추가):
```typescript
paused_count: number;
```
- `PreferencesPayload` 인터페이스에 서버 payload와 정확히 대응하는 타입 추가.

**`app/frontend/src/components/PreferencePanel.tsx`** (실질 변경):
- `PreferenceStatusFilter` 타입 추가 (`all | candidate | active | paused`)
- `statusFilter` 상태 추가, 기본값 `all`
- `filteredPreferences` 파생값: `all`이면 전체, 그 외에는 해당 status만 필터
- `statusTabs` 배열: 전체/후보/활성/일시중지 탭 + 각 count
- 탭 버튼 렌더링: `data-testid="preference-status-filter-{key}"`, `aria-pressed` 적용
- 빈 탭에 "해당 상태 선호가 없습니다" 메시지 추가
- rejected 항목 숨김: 기존 `preferences.filter(p => p.status !== "rejected")`는 유지됨
- activate/pause/reject 버튼, status 배지, 기타 아이템 렌더링 변경 없음

## 범위 미검증 (정직한 보고)

- 전체 `tests.test_web_app` 스위트: `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled` 장시간 블로킹으로 미완료 (work note와 동일한 제약)
- Playwright/browser E2E: sandbox 제약으로 미실행 (handoff guardrails에 명시된 항목)

## 현재 Dirty Tree 상태

| 파일 | 라운드 | 커밋 여부 |
|------|--------|-----------|
| `app/handlers/preferences.py` | M42 A1 | 미커밋 |
| `app/frontend/src/api/client.ts` | M42 A1 | 미커밋 |
| `app/frontend/src/components/PreferencePanel.tsx` | M42 A1 | 미커밋 |
| `docs/MILESTONES.md` | M42 A1 docs | 미커밋 |
| `docs/PRODUCT_SPEC.md` | M42 A1 docs | 미커밋 |
| `docs/ACCEPTANCE_CRITERIA.md` | M42 A1 docs | 미커밋 |
| `tests/test_web_app.py` | M42 A1 tests | 미커밋 |

이전 라운드(watcher re-export, auth boundary, resolver)는 모두 커밋됨.

## 발견된 문서 불일치

- `docs/MILESTONES.md` "Next 3 Implementation Priorities" 항목 1: 아직 "M42 Axis 1 미구현" 형태로 기술됨. M42 A1이 shipped 됐으므로 stale. M42 milestone 섹션은 "Axis 1 shipped" 로 정상 갱신됨.
- "Next 3" 항목 2 (watcher re-export note)는 커밋 85c5210으로 완료됐으므로 stale.
- 항목 3 (E2E 환경 개선 note)는 여전히 검증 대기 중.

## 남은 리스크

- M42 A1 commit bundle (7개 파일) 미커밋: 다음 advisory에서 커밋 범위 및 방법 결정 필요
- "Next 3" 항목 1, 2가 stale: advisory에서 M42 A2 또는 M43 방향과 함께 갱신 결정 필요
- E2E 환경 개선 note (항목 3): next slice로 남아 있음, 검증 방법 확인 필요
