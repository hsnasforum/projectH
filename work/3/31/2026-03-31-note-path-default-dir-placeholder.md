# 2026-03-31 note-path default directory placeholder

## 변경 파일
- `app/web.py`
- `app/templates/index.html`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- note-path 입력 필드 placeholder가 "비워두면 notes 디렉터리 기본 경로를 사용합니다"로만 표시되어, 사용자가 실제 기본 저장 위치를 모른 채 승인하는 사용성 gap
- badge/history/detail 축과 완전히 다른 approval UX honesty fix

## 핵심 변경

### backend 변경
- `app/web.py`: `get_config()` 응답에 `notes_dir` 필드 추가

### UI 변경
- `app/templates/index.html`: config 로드 후 `notes_dir` 값이 있으면 note-path placeholder를 `비워두면 {notes_dir} 기본 경로를 사용합니다.`로 업데이트
- 예: `비워두면 data/notes 기본 경로를 사용합니다.`

### docs 반영
- `docs/ACCEPTANCE_CRITERIA.md`: note-path placeholder가 서버 config의 기본 디렉터리를 표시한다는 contract 추가

## 검증
- `python3 -m py_compile app/web.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — `97 tests OK`
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- `README.md`, `docs/PRODUCT_SPEC.md`에는 이번 변경을 별도로 적지 않았음 (이 surface는 기존 "approval-based save" 항목 아래에 자연스럽게 포함되며, verify에서 필요시 추가 sync 가능)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
