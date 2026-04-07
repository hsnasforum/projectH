# entity-card crimson-desert natural-reload initial README source-path wording clarification

## 변경 파일

- `README.md` (line 158)

## 사용 skill

- 없음 (docs-only source-path wording clarification)

## 변경 이유

`README.md:158`이 `source path(...provenance 포함)` wording으로 남아 있어, sibling `docs/ACCEPTANCE_CRITERIA.md:1367`과 current test title의 compact `source path(...provenance)` pattern과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| README.md:158 | `provenance 포함)` → `provenance)` |

## 검증

- `git diff --check -- README.md` → clean

## 남은 리스크

- crimson-desert natural-reload initial docs가 README와 ACCEPTANCE_CRITERIA 모두 compact source-path pattern으로 정렬됐습니다.
- 현재 tree 기준으로 `포함` 중심 long-form docs 잔여가 있는지 다음 라운드에서 Codex가 확인할 예정입니다.
