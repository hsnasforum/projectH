---
paths:
  - "e2e/**/*"
  - "README.md"
  - "docs/ACCEPTANCE_CRITERIA.md"
  - "docs/MILESTONES.md"
  - "docs/TASK_BACKLOG.md"
---

# Browser And E2E Rules

- Start with the narrowest relevant browser rerun first.
- For selector drift, fixture drift, or one scenario family, use an isolated Playwright rerun before `make e2e-test`.
- Use the broad browser suite only when the browser-visible contract widened, shared browser helpers changed, release / ready claims are being made, or an isolated rerun shows broader drift.
- Keep browser claims exact. Do not silently broaden a parity gate from one scenario family to a larger contract without matching reruns and doc updates.
- When sqlite/browser parity work is in scope, preserve the JSON-default path unless the handoff explicitly changes the default contract.
- If README or docs describe scenario counts, titles, or gate meaning, sync them in the same task as the browser change.

