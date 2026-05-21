# verify: 2026-05-21 pane fallback telemetry 기준 문서화

## 대상 work
`work/5/21/2026-05-21-pane-fallback-telemetry-criteria-doc.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `git diff --check` README + RUNBOOK | PASS |

## 문서 확인

| 위치 | 내용 | 확인 |
|---|---|---|
| `.pipeline/README.md:195` | `pane_text_fallback_used`는 failure 아닌 telemetry. 허용/주의 기준 요약 | ✓ |
| `05_운영_RUNBOOK.md:253` | 관찰값 / 해석 / 다음 행동 기준표 | ✓ |
| RUNBOOK raw pane text 경고 | payload에 raw pane text 포함 시 즉시 수정 명시 | ✓ |

## 이번 작업 전체 완료 현황

| 단계 | 내용 | 상태 |
|---|---|---|
| P1-P18 버그픽스 | pipeline launcher 18개 이슈 | 커밋 완료 |
| runs 자동 정리 | `.pipeline/runs/` 오래된 런 삭제 | 커밋 완료 |
| wrapper-events schema | 공식 계약 정식화 | 미커밋 |
| supervisor wrapper-first | pane text fallback 계층 분리 | 미커밋 |
| Claude stream-json | JSONL → wrapper event 변환 | 미커밋 |
| pane fallback telemetry | `pane_text_fallback_used` 이벤트 | 미커밋 |
| 기준표 문서화 | README + RUNBOOK | 미커밋 |

## 남은 사항

- 미커밋 변경 커밋 (operator 결정)
- live Claude stream-json 검증 (Claude가 active lane이 되는 시점)
- Codex/Gemini fallback 빈도 누적 관찰 → 구조화 출력 필요성 데이터 기반 판단
