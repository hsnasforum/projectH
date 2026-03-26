---
name: security-gate
description: Use before or after a change that touches file writes, shell execution, permissions, logs, or external network access.
---

# Security Gate Skill

Checklist:
1. Is the action read-only or write-capable?
2. Does it require explicit user approval?
3. Can it overwrite, delete, move, or execute?
4. Is the affected path limited and auditable?
5. Is the action logged?
6. Is there a reversible path?
7. Does it introduce hidden network dependency?

Output:
- Risk summary
- Required safeguards
- Approval requirements
- Logging requirements
- Remaining concerns
