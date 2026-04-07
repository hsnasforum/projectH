# history-card entity-card click-reload follow-up docs exact-field wording clarification

## 변경 파일

- `README.md` (line 131)
- `docs/MILESTONES.md` (line 49)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1340)
- `docs/TASK_BACKLOG.md` (line 38)

## 사용 skill

- 없음 (docs-only wording clarification)

## 변경 이유

history-card entity-card click-reload follow-up docs 4곳이 generic wording(`response origin badge와 answer-mode badge drift prevention`)만 남아 있어, test/body에서 이미 검증하는 exact-field(`WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`)를 docs에서 직접 드러내지 못했습니다. test title은 이전 라운드에서 이미 clarify되었으므로, 동일 truth를 docs에도 적용합니다.

## 핵심 변경

| 파일 | before | after |
|---|---|---|
| README.md:131 | `response origin badge와 answer-mode badge가 drift하지 않는지 확인` | `WEB badge, 설명 카드 answer-mode badge, 설명형 단일 출처 verification label, 백과 기반 source-role detail이 drift하지 않는지 확인` |
| MILESTONES.md:49 | `response origin badge and answer-mode badge drift prevention` | `WEB badge, 설명 카드 answer-mode badge, 설명형 단일 출처 verification label, 백과 기반 source-role detail drift prevention` |
| ACCEPTANCE_CRITERIA.md:1340 | `response origin badge, answer-mode badge drift 없음` | `WEB badge, 설명 카드 answer-mode badge, 설명형 단일 출처 verification label, 백과 기반 source-role detail drift 없음` |
| TASK_BACKLOG.md:38 | `response origin badge, answer-mode badge drift prevention` | `WEB badge, 설명 카드 answer-mode badge, 설명형 단일 출처 verification label, 백과 기반 source-role detail drift prevention` |

모든 4곳에서 `history-card` → `history-card entity-card` prefix도 정렬했습니다.

## 검증

- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- `response origin badge와 answer-mode badge` generic wording은 docs 기준으로도 이번 라운드로 모두 닫혔습니다.
- 다른 answer-mode family(crimson, entity-card actual-search natural-reload 등)의 별도 패턴은 별도 라운드 대상입니다.
