# 2026-04-29 M85 Axis 2 promote result reliability feedback

## 변경 파일
- `app/handlers/corrections.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_summary.py`
- `work/4/29/2026-04-29-m85-axis2-promote-result-reliability-feedback.md`

## 사용 skill
- `security-gate`: promotion 응답과 preference record 갱신이 기존 local-first 저장/승인 경계를 벗어나지 않는지 확인했다.
- `finalize-lite`: 실행한 검증, 미실행 범위, dist/E2E 금지 범위, closeout 준비 상태를 점검했다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 closeout note를 작성했다.

## 변경 이유
- M85 Axis 1에서 correction `recurrence_count`가 신규 preference의 reliability seed로 저장되면서, 승격 직후 `is_highly_reliable` 판정이 가능해졌다.
- 사용자가 `PreferencePanel`에서 correction pattern을 승격한 직후 활성화 수뿐 아니라 "신뢰도 높음" 상태도 즉시 확인할 수 있어야 했다.

## 핵심 변경
- `promote_correction_pattern` 응답에 `is_highly_reliable` boolean 필드를 추가했다.
- promoted correction의 `similarity_score`를 `avg_similarity_score`로 preference 생성 호출에 전달하고, activate 결과를 `enrich_preference_reliability`로 평가해 응답 플래그를 계산한다.
- `promoteCorrectionPattern` TypeScript 반환 타입에 `is_highly_reliable?: boolean`을 추가했다.
- `PreferencePanel`의 `lastPromoteResult` 상태와 표시 블록에 `isHighlyReliable`을 추가해 승격 결과 옆에 `신뢰도 높음`을 표시한다.
- `tests/test_correction_summary.py`에 recurrence 3 이상이면 `is_highly_reliable: True`, 3 미만이면 `False`인 응답 테스트를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: 요청된 `6580837a9d968a5c2a0a5e70c6316061e34ad891acfaa90c342b3127723ec125`와 일치.
- `git switch -c feat/m85-axis2-promote-result-reliability-feedback` 실행: `.git/refs/heads/...lock` 생성이 read-only filesystem으로 막혀 실패. 브랜치 생성은 환경 제약으로 완료하지 못했다.
- `python3 -m py_compile app/handlers/corrections.py tests/test_correction_summary.py` 통과.
- `python3 -m unittest -v tests.test_correction_summary` 통과 (`Ran 7 tests ... OK`).
- `python3 -m unittest -v tests.test_preference_handler` 통과 (`Ran 20 tests ... OK`).
- `git diff --check -- app/handlers/corrections.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_correction_summary.py` 통과.
- `cd app/frontend && npx tsc --noEmit` 통과.

## 남은 리스크
- 브랜치 생성은 `.git/refs` 쓰기 제한 때문에 실패했으므로 변경은 현재 `feat/m85-axis1-correction-reliability-seed` 작업트리에 남아 있다.
- dist 재빌드와 E2E 파일 수정은 handoff 경계에 따라 수행하지 않았다.
- UI 변경에 따른 broader browser/E2E, docs milestone 갱신, commit/push/PR publish, `/verify` 작성은 수행하지 않았다.
