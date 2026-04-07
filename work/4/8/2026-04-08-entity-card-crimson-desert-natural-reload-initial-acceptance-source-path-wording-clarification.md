# entity-card crimson-desert natural-reload initial acceptance source-path wording clarification

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` (line 1367)

## 사용 skill

- 없음 (docs-only source-path wording clarification)

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:1367`이 `source path plurality(...provenance 포함)` wording으로 남아 있어, sibling `README.md:158`과 current test title의 compact `source path(...provenance)` pattern과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| ACCEPTANCE_CRITERIA.md:1367 | `source path plurality(...provenance 포함)` → `source path(...provenance)` |

## 검증

- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- crimson-desert natural-reload docs 전체(initial + noisy + actual-search)가 이번 라운드로 compact source-path/exact-field로 정렬됐습니다.
- 현재 tree 기준으로 `plurality` 또는 `포함` 중심 long-form docs 잔여가 있는지 다음 라운드에서 Codex가 확인할 예정입니다.
