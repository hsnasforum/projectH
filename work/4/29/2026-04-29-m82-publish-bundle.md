# 2026-04-29 M82 Publish Bundle — commit/push/stacked PR

## 스택 구조

```
PR #62(M76) ← … ← PR #67(M81) ← PR #68(M82)
```

## 커밋

| SHA | 내용 |
|-----|------|
| `befe079` | feat(M82): expose activated_count in promote-pattern API response |

베이스: `abe52b2` (M81, feat/m81-promote-auto-activate HEAD)

## PR 생성 결과

- **PR #68**: feat(M82): expose activated_count in promote-pattern API response
- URL: https://github.com/hsnasforum/projectH/pull/68
- base: `feat/m81-promote-auto-activate` (stacked on PR #67)

## 남은 사항

- PR #62–#68 머지: operator 결정
- M83 방향: advisory에서 결정
