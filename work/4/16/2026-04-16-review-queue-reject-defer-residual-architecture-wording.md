# review-queue reject/defer residual architecture wording bundle

## 변경 파일

- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

이전 architecture-doc 라운드(`work/4/16/2026-04-16-review-queue-reject-defer-architecture-docs-parity.md`)에서 lines 1223–1229의 stale wording을 정확히 닫았으나, 같은 파일의 다른 위치에 남아 있던 동일 계열 drift를 닫지 못했습니다. 이번 라운드는 verify에서 지적된 나머지 두 곳(line 34, line 1143)을 닫고, 전체 파일 reread으로 같은 계열 stale wording이 더 없음을 확인합니다.

## 핵심 변경

1. **top-level responsibilities summary** (line 34): `plus one \`accept\`-only reviewed-but-not-applied action` → `with \`accept\` / \`reject\` / \`defer\` reviewed-but-not-applied actions`
2. **recurrence/architecture guidance** (line 1143): `broader \`edit\` / \`reject\` / \`defer\` expansion` → `broader \`edit\` expansion`, reject/defer shipped 상태 괄호 주석 추가

## 검증

- `nl -ba docs/ARCHITECTURE.md | sed -n '28,40p'` → line 34 shipped 상태 반영 확인
- `nl -ba docs/ARCHITECTURE.md | sed -n '1138,1146p'` → line 1143 shipped 상태 반영 확인
- `rg -n 'plus one \x60accept\x60-only reviewed-but-not-applied action|broader \x60edit\x60 / \x60reject\x60 / \x60defer\x60 expansion' docs/ARCHITECTURE.md` → no matches (stale pattern 소멸)
- `git diff --check -- docs/ARCHITECTURE.md work/4/16` → clean
- broader reread: `rg -n 'accept.-only|\x60accept\x60 only|no.*reject.*defer.*API|reject.*defer.*still.*later|reject.*defer.*deferred|reject.*defer.*expansion' docs/ARCHITECTURE.md` → line 1229만 매치 (이전 라운드에서 이미 shipped 상태로 수정된 truthful 문장). 같은 계열 stale wording 추가 잔존 없음

## 남은 리스크

- `docs/ARCHITECTURE.md`의 review-action 계열 root-doc drift는 이 라운드로 전부 닫힘.
- 모든 root docs (MILESTONES, TASK_BACKLOG, ARCHITECTURE, PRODUCT_SPEC, ACCEPTANCE_CRITERIA, NEXT_STEPS) 공히 shipped `accept`/`reject`/`defer` 상태를 정확히 반영.
