# Docs ARCHITECTURE session_store permissions persistence truth sync

## 변경 파일

- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ARCHITECTURE.md:74`의 `session_store` persistence summary에서 `permissions`가 누락되어 있었음. 실제 코드(`storage/session_store.py`)는 `permissions`를 정규화하고 `set_permissions`/`get_permissions`를 노출하므로 persistence summary와 불일치.

## 핵심 변경

### docs/ARCHITECTURE.md
- line 74: `pending_approvals`와 `active_context` 사이에 `permissions` 추가

## 검증

- persistence summary에 `permissions` 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 없음.
