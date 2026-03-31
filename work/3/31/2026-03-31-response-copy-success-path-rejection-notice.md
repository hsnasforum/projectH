# 2026-03-31 response copy success-path rejection notice

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `navigator.clipboard.writeText()` promise rejection이 click handler의 generic `.catch(renderError)`로 처리되어 clipboard-specific 안내 없이 기술적 에러 메시지가 표시되는 risk

## 핵심 변경

### code 변경
- `copyTextValue()` success path: `navigator.clipboard.writeText()`를 try-catch로 감싸기
  - 성공: 기존대로 success notice
  - rejection: "클립보드 복사에 실패했습니다. 브라우저 권한을 확인하거나 텍스트를 직접 선택해 복사해 주세요." clipboard-specific failure notice

### docs 반영 (3개 파일)
- `README.md`: "shows clipboard-specific failure notice on both success-path rejection and fallback failure"
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: rejection + fallback failure 모두 clipboard-specific notice, coverage 범위 정확 구분

### copy-to-clipboard notice honesty 완결 상태
이제 3개 경로 모두 정직한 notice를 표시:
1. **success**: success notice + clipboard에 텍스트 기록 (Playwright smoke 검증)
2. **success-path rejection**: clipboard-specific failure notice (code review only)
3. **fallback failure**: clipboard-specific failure notice (code review only)

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- rejection/fallback failure branch는 current Chromium Playwright baseline에서 직접 도달 불가 (code review only)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
